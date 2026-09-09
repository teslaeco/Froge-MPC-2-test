"""Data contract and worker lifecycle checks; AI quality is not simulated here."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import server
from code_policy import prepare_code
from runtime.scene_contract import SCHEMA, parse_scene, validate_scene, lathe_profile, polygon_outline

EXAMPLES = Path(__file__).parent/'examples'


class SceneContractTests(unittest.TestCase):
    def setUp(self):
        self.oak=json.loads((EXAMPLES/'oak-lights.scene.json').read_text())

    def test_complete_oak_and_rocket_use_the_shared_contract(self):
        for name in ['oak-lights.scene.json','rocket.scene.json','rapper.scene.json','dubai-tower.scene.json']:
            value=parse_scene((EXAMPLES/name).read_text())
            self.assertEqual(value['version'],1)
        self.assertEqual(self.oak['parts'][1]['bulbs'],20)

    def test_closed_descending_and_stepped_profiles_keep_their_outline(self):
        cases=[[[1,0],[1,2],[.4,2],[.4,3],[0,4]],
               [[0,4],[.4,3],[.4,2],[1,2],[1,0]],
               [[0,0],[1,0],[1,2],[0,3],[0,0]],
               [[.8,0],[1,0],[1,2],[.8,2],[.8,0]]]
        for profile in cases:
            with self.subTest(profile=profile):
                outline=lathe_profile(profile)
                self.assertTrue(all(point in [(r,z) for r,z in profile]+[(0,profile[-1][1]),(0,profile[0][1])] for point in outline))
                self.assertGreater(len(outline),2)

    def test_crossing_negative_radius_and_zero_volume_remain_invalid(self):
        for profile in [[[0,0],[2,2],[0,2],[2,0],[0,0]], [[-1,0],[1,1]], [[0,0],[0,2]], [[1,0],[2,0]]]:
            with self.subTest(profile=profile),self.assertRaises(ValueError):lathe_profile(profile)
        with self.assertRaises(ValueError):polygon_outline([[0,0],[2,2],[0,2],[2,0]])

    def test_new_wardrobe_choices_and_legacy_hair_default(self):
        legacy=parse_scene((EXAMPLES/'rapper.scene.json').read_text())
        self.assertEqual(legacy['parts'][0]['hair_style'],'short')
        sample=parse_scene((EXAMPLES/'rapper-eminem-style.scene.json').read_text())
        self.assertEqual(sample['parts'][0]['outfit'],'tshirt')
        self.assertFalse(sample['parts'][0]['necklace'])
        for outfit in ('tshirt','sweatshirt','hoodie'):
            scene=deepcopy(sample);scene['parts'][0]['outfit']=outfit;validate_scene(scene)
        for name in ('rapper-la.scene.json','rapper-female-la.scene.json'):
            current=parse_scene((EXAMPLES/name).read_text());self.assertEqual(current['parts'][0]['shirt_graphic'],'LA')
        self.assertEqual(legacy['parts'][0]['shirt_graphic'],'none')
        scene=deepcopy(sample);scene['parts'][0]['shirt_graphic']='arbitrary code'
        with self.assertRaises(ValueError):validate_scene(scene)
        scene=deepcopy(sample);scene['parts'][0]['hair_style']='unknown'
        with self.assertRaises(ValueError):validate_scene(scene)

    def test_person_materials_and_loft_and_extrusion_controls(self):
        person=parse_scene((EXAMPLES/'rapper.scene.json').read_text())
        for field,val in [('skin_material','missing'),('pose','unknown'),('necklace',1)]:
            scene=deepcopy(person);scene['parts'][0][field]=val
            with self.assertRaises(ValueError):validate_scene(scene)
        tower=parse_scene((EXAMPLES/'dubai-tower.scene.json').read_text())
        tower['parts'][0]['levels'][1]['z']=-1
        with self.assertRaises(ValueError):validate_scene(tower)

    def test_feminine_missing_hair_defaults_without_overriding_explicit_styles(self):
        sample=json.loads((EXAMPLES/'rapper-singer.scene.json').read_text())
        sample['parts'][0].pop('hair_style')
        self.assertEqual(validate_scene(sample)['parts'][0]['hair_style'],'shoulder_length')
        for style in ('short','buzz','bald'):
            sample['parts'][0]['hair_style']=style
            self.assertEqual(validate_scene(sample)['parts'][0]['hair_style'],style)
        with self.assertRaises(ValueError):validate_scene({**self.oak,'parts':[{'kind':'loft','name':'bad','material':'kora','sides':32,'sections':[{'center':[0,0,0],'radii':[1,1]}]*2}]})

    def test_subject_requirements_correct_a_contradictory_single_person_plan(self):
        sample=json.loads((EXAMPLES/'rapper.scene.json').read_text())
        original=json.dumps(sample)
        p=parse_scene(original,'Figurka dorosłej CardiB. Dopasowana koszulka, krągła sylwetka.')['parts'][0]
        self.assertEqual(p['presentation'],'feminine')
        self.assertEqual(p['body_shape'],'curvy')
        self.assertEqual(p['clothing_fit'],'fitted')
        self.assertEqual(p['hair_style'],'shoulder_length')
        p=parse_scene(original,'Dorosła wokalistka, krótkie włosy i luźna koszulka.')['parts'][0]
        self.assertEqual(p['presentation'],'feminine')
        self.assertEqual(p['hair_style'],'short')
        self.assertEqual(p['clothing_fit'],'oversized')
        p=parse_scene(original,'Męska wersja Cardi B.')['parts'][0]
        self.assertEqual(p['presentation'],'masculine')
        self.assertEqual(parse_scene(original)['parts'][0]['body_shape'],'natural')
        self.assertEqual(parse_scene(original)['parts'][0]['clothing_fit'],'regular')

    def test_body_choices_stay_bounded_and_nonhuman_scenes_stay_unchanged(self):
        sample=json.loads((EXAMPLES/'rapper.scene.json').read_text())
        for field in ('body_shape','clothing_fit'):
            invalid=deepcopy(sample);invalid['parts'][0][field]='arbitrary expression'
            with self.assertRaises(ValueError):parse_scene(json.dumps(invalid),'Cardi B')
        self.assertEqual(parse_scene(json.dumps(self.oak),'Dąb dla Cardi B'),{**self.oak,'subject_type':'object'})

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
                    self.assertEqual(blender.call_args.kwargs['timeout'],900)
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
