"""Missing material regressions; mock AI responses, never paid generation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import server
from runtime.scene_contract import (
    MATERIAL_FIELDS, MaterialReferenceError, apply_material_repair,
    material_repair_schema, parse_scene,
)


class MaterialRepairTests(unittest.TestCase):
    def setUp(self):
        self.scene = parse_scene((Path(__file__).parent / 'examples/couture-fan-v20.scene.json').read_text())
        self.scene['parts'][0]['eye_material'] = 'eyes_grey_green'
        self.palette = {
            'slots': [{k: v for k, v in m.items() if k != 'name'} for m in self.scene['materials']],
            'bindings': {},
        }
        indices = {m['name']: i for i, m in enumerate(self.scene['materials'])}
        for part in self.scene['parts']:
            for field in MATERIAL_FIELDS:
                if field in part:
                    name = part[field]
                    self.palette['bindings'][name] = indices.get(name, indices['eyes'])
        self.palette['slots'][indices['eyes']]['rgb'] = [.32, .42, .35]

    def test_exact_report_and_repair_preserve_geometry_and_source(self):
        original = deepcopy(self.scene)
        with self.assertRaisesRegex(MaterialReferenceError, 'eyes_grey_green') as failure:
            parse_scene(json.dumps(self.scene))
        self.assertEqual(failure.exception.missing, {'eyes_grey_green': ['emerald-muse.eye_material']})
        repaired, report = apply_material_repair(failure.exception.scene, json.dumps(self.palette))
        self.assertEqual(self.scene, original)
        self.assertEqual(repaired['parts'], original['parts'])
        self.assertEqual({k: v for k, v in repaired.items() if k != 'materials'},
                         {k: v for k, v in original.items() if k != 'materials'})
        eye = next(m for m in repaired['materials'] if m['name'] == 'eyes_grey_green')
        self.assertEqual(eye['rgb'], [.32, .42, .35])
        for material in original['materials']:
            if material['name'] != 'eyes':
                self.assertIn(material, repaired['materials'])
        self.assertEqual(report['material_count'], 8)
        self.assertFalse(report['colors_independently_verified'])

    def test_ninth_reference_shares_a_declared_slot_without_ninth_material(self):
        self.scene['parts'].append({'kind': 'ellipsoid', 'name': 'material-sample',
            'material': 'eyes', 'center': [0, 0, 3], 'radii': [.01, .01, .01]})
        self.palette['bindings']['eyes'] = self.palette['bindings']['eyes_grey_green']
        repaired, report = apply_material_repair(self.scene, json.dumps(self.palette))
        self.assertEqual(len(repaired['materials']), 8)
        self.assertEqual(repaired['parts'][0]['eye_material'], 'eyes')
        self.assertEqual(report['bindings']['eyes_grey_green'], 'eyes')
        for before, after in zip(self.scene['parts'], repaired['parts']):
            self.assertEqual({k: v for k, v in before.items() if k not in MATERIAL_FIELDS},
                             {k: v for k, v in after.items() if k not in MATERIAL_FIELDS})

    def test_invalid_bindings_extra_geometry_colors_and_duplicate_keys_are_rejected(self):
        changes = [lambda p: p['bindings'].pop('eyes_grey_green'),
                   lambda p: p['bindings'].update(eyes_grey_green=8),
                   lambda p: p['bindings'].update(eyes_grey_green=True),
                   lambda p: p.update(parts=[]),
                   lambda p: p['slots'][0].update(rgb=[2, 0, 0]),
                   lambda p: p['slots'].pop()]
        for change in changes:
            bad = deepcopy(self.palette)
            change(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                apply_material_repair(self.scene, json.dumps(bad))
        with self.assertRaisesRegex(ValueError, 'Powtorzone pole'):
            apply_material_repair(self.scene, '{"slots":[],"slots":[]}')

    def test_material_repair_cannot_bypass_anatomy_validation(self):
        self.scene['parts'].append({'kind': 'ellipsoid', 'name': 'eye',
            'material': 'skin', 'center': [0, 0, 3], 'radii': [.01, .01, .01]})
        with self.assertRaisesRegex(ValueError, 'Standard postaci'):
            apply_material_repair(self.scene, json.dumps(self.palette))

    def test_both_providers_receive_the_repair_schema(self):
        schema = material_repair_schema(self.scene)
        for provider in ('openai', 'ollama'):
            with self.subTest(provider=provider), patch.object(server, 'stream_chat', return_value='{}') as local, \
                 patch.object(server.openai_provider, 'generate', return_value='{}') as remote:
                server.generate_code([], 'fixture', threading.Event(), attempt=2,
                    selected={'provider': provider, 'api_key': 'test-only'}, schema=schema)
                if provider == 'openai':
                    self.assertEqual(remote.call_args.kwargs['schema'], schema)
                    local.assert_not_called()
                else:
                    self.assertEqual(local.call_args.args[1]['format'], schema)
                    remote.assert_not_called()

    def test_worker_repairs_second_attempt_and_never_adds_a_third_attempt(self):
        for valid in (True, False):
            with self.subTest(valid=valid), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repair_text = json.dumps(self.palette) if valid else '{"slots":[],"bindings":{}}'
                with patch.multiple(server, STATE=root/'state', JOBS=root/'state/jobs', CONFIG=root/'state/config.json'):
                    server.initialize()
                    with server.database() as db:
                        db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)', ('material-job', 'Kobieta z wachlarzem', 'queued', ''))
                    with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'), \
                         patch.object(server, 'ai_settings', return_value={'provider': 'ollama'}), \
                         patch.object(server, 'generate_code', side_effect=[json.dumps(self.scene), repair_text]) as ai, \
                         patch.object(server, 'run_blender') as blender:
                        wake.wait.side_effect = [None, StopIteration]
                        with self.assertRaises(StopIteration):
                            server.worker()
                        self.assertEqual(ai.call_count, 2)
                        self.assertEqual(ai.call_args.kwargs['schema'], material_repair_schema(self.scene))
                        self.assertEqual(ai.call_args.args[3], ai.call_args_list[0].args[3])
                        self.assertEqual(ai.call_args.args[4], 2)
                        self.assertEqual(blender.call_count, 1 if valid else 0)
                    folder = server.JOBS/'material-job'
                    self.assertEqual(json.loads((folder/'attempt-1.json').read_text()), self.scene)
                    self.assertEqual((folder/'attempt-2.materials.json').read_text(), repair_text)
                    self.assertEqual((folder/'scene.json').exists(), valid)
                    if valid:
                        self.assertEqual(json.loads((folder/'scene.json').read_text())['parts'], self.scene['parts'])
                        report = json.loads((folder/'material-repair.json').read_text())
                        self.assertIn('eyes_grey_green', report['missing'])
                    with server.database() as db:
                        self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0], 'succeeded' if valid else 'failed')


if __name__ == '__main__':
    unittest.main()
