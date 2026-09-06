"""Data contract and worker lifecycle checks; AI quality is not simulated here."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import server
from code_policy import prepare_code
from runtime.scene_contract import SCHEMA, parse_scene, validate_scene

EXAMPLES = Path(__file__).parent/'examples'


class SceneContractTests(unittest.TestCase):
    def setUp(self):
        self.oak=json.loads((EXAMPLES/'oak-lights.scene.json').read_text())

    def test_complete_oak_and_rocket_use_the_shared_contract(self):
        for name in ['oak-lights.scene.json','rocket.scene.json']:
            value=parse_scene((EXAMPLES/name).read_text())
            self.assertEqual(value['version'],1)
        self.assertEqual(self.oak['parts'][1]['bulbs'],20)

    def test_rejects_code_unknown_operations_extra_fields_and_nonfinite_values(self):
        for text in ['ellipsoid("x", [0,0,0], [1,1,1], None)', '{"version":1,"version":1}']:
            with self.subTest(text=text), self.assertRaises(ValueError):parse_scene(text)
        for change in [lambda s:s.update(python='open("secret")'),
                       lambda s:s['parts'][0].update(kind='eval'),
                       lambda s:s['parts'][0].update(height=float('nan')),
                       lambda s:s['parts'][0].update(height=True),
                       lambda s:s['materials'][0].update(rgb=[1,2,3])]:
            value=deepcopy(self.oak);change(value)
            with self.assertRaises(ValueError):validate_scene(value)

    def test_checks_material_references_duplicate_names_and_geometry_budget(self):
        for change in [lambda s:s['parts'][0].update(material='missing'),
                       lambda s:s['materials'][1].update(name='kora'),
                       lambda s:s['parts'][1].update(name='dab'),
                       lambda s:s['parts'].extend([{**s['parts'][0],'name':'extra%d'%i} for i in range(2)])]:
            value=deepcopy(self.oak);change(value)
            with self.assertRaises(ValueError):validate_scene(value)

    def test_invalid_mesh_tube_and_copy_are_rejected_before_blender(self):
        scene=deepcopy(self.oak)
        cases=[{'kind':'mesh','name':'bad','material':'kora','vertices':[[0,0,0],[1,0,0],[0,1,0]],'faces':[[0,1,3]]},
               {'kind':'mesh','name':'bad','material':'kora','vertices':[[0,0,0],[1,0,0],[2,0,0]],'faces':[[0,1,2]]},
               {'kind':'tube','name':'bad','material':'kora','points':[[0,0,0],[0,0,0]],'radii':[1,1],'sides':12},
               {'kind':'copies','name':'bad','source':'dab','offsets':[[0,0,0]]}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_scene({**scene,'parts':[value]})

    def test_legacy_geometry_is_never_silently_replaced_or_tuple_unpacked(self):
        for text in ['def ellipsoid(name, center, scale, material):\n    return [], []\na,b=ellipsoid("x",[0,0,0],[1,1,1],None)',
                     'trunk_vertices,trunk_faces=ellipsoid("trunk",(0,0,2),(1,1,2),bark_material)']:
            with self.assertRaisesRegex(ValueError,'geometrii'):prepare_code(text)

    def test_scene_generation_saves_data_only_and_retries_with_the_validation_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch.multiple(server, STATE=root/'state', JOBS=root/'state/jobs', CONFIG=root/'state/config.json'):
                server.initialize()
                with server.database() as db:
                    db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',('scene-job','Dab i 20 lampek','queued',''))
                with patch.object(server,'WAKE') as wake, patch.object(server,'verify_runtime'), patch.object(server,'generate_code',side_effect=['print("wrong")',json.dumps(self.oak)]) as ai, patch.object(server,'run_blender') as blender:
                    wake.wait.side_effect=[None,StopIteration]
                    with self.assertRaises(StopIteration):server.worker()
                    self.assertEqual(ai.call_count,2)
                    self.assertIn('complete corrected scene JSON',ai.call_args.args[0][-1]['content'])
                    blender.assert_called_once()
                    self.assertEqual(blender.call_args.kwargs['timeout'],180)
                folder=server.JOBS/'scene-job'
                self.assertTrue((folder/'scene.json').exists())
                self.assertFalse((folder/'generate.py').exists())
                with server.database() as db:self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0],'succeeded')

    def test_timeout_ends_job_without_another_ai_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch.multiple(server, STATE=root/'state', JOBS=root/'state/jobs', CONFIG=root/'state/config.json'):
                server.initialize()
                with server.database() as db:db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',('slow-job','Dab','queued',''))
                with patch.object(server,'WAKE') as wake, patch.object(server,'verify_runtime'), patch.object(server,'generate_code',side_effect=TimeoutError('slow')) as ai, patch.object(server,'run_blender') as blender:
                    wake.wait.side_effect=[None,StopIteration]
                    with self.assertRaises(StopIteration):server.worker()
                    ai.assert_called_once();blender.assert_not_called()
                with server.database() as db:self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0],'failed')


if __name__=='__main__':unittest.main()
