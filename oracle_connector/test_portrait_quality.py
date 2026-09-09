from copy import deepcopy
import json
from pathlib import Path
import unittest
from runtime.scene_contract import parse_scene,validate_scene

EXAMPLES=Path(__file__).parent/'examples'


class PortraitQualityTests(unittest.TestCase):
    def test_unsupported_seated_garment_does_not_silently_render_standing(self):
        scene=json.loads((EXAMPLES/'fashion-1.scene.json').read_text())
        scene['parts'][0]['outfit']='tshirt'
        with self.assertRaisesRegex(ValueError,'nie zastepuj jej staniem'):validate_scene(scene)

    def test_group_keeps_three_separate_detailed_people_and_rejects_extra_duplicates(self):
        original=json.loads((EXAMPLES/'fashion-group.scene.json').read_text())
        scene=validate_scene(deepcopy(original))
        self.assertEqual(sum(p['kind']=='person' for p in scene['parts']),3)
        fourth=deepcopy(original['parts'][0]);fourth['name']='extra-copy'
        original['parts'].append(fourth)
        with self.assertRaisesRegex(ValueError,'maksymalnie 3'):validate_scene(original)
    def test_custom_pose_accepts_connected_head_and_both_anatomical_hands(self):
        scene=parse_scene((EXAMPLES/'portrait-floor-components.scene.json').read_text(),'Dziewczyna siedząca ze zdjęcia')
        self.assertEqual([p['kind'] for p in scene['parts']],['portrait','anatomical_hand','anatomical_hand'])

    def test_human_primitive_fallback_is_rejected_even_if_labeled_object(self):
        source=json.loads((EXAMPLES/'rocket.scene.json').read_text())
        with self.assertRaisesRegex(ValueError,'Standard postaci'):parse_scene(json.dumps(source),'Dziewczyna z mojego zdjęcia')
        source['subject_type']='person'
        with self.assertRaisesRegex(ValueError,'Standard postaci'):validate_scene(source)

    def test_missing_wrong_sided_or_degenerate_hands_fail_before_rendering(self):
        original=json.loads((EXAMPLES/'portrait-floor-components.scene.json').read_text())
        for problem in ('missing','side','axis','normal'):
            scene=deepcopy(original)
            if problem=='missing':scene['parts'].pop()
            elif problem=='side':scene['parts'][2]['side']='left'
            elif problem=='axis':scene['parts'][1]['direction']=[0,0,0]
            else:scene['parts'][1]['palm_normal']=scene['parts'][1]['direction']
            with self.subTest(problem=problem),self.assertRaises(ValueError):validate_scene(scene)

    def test_face_controls_remain_bounded_and_person_cannot_add_a_ball_nose(self):
        original=json.loads((EXAMPLES/'portrait-floor-components.scene.json').read_text())
        for value in (1.01,False,float('nan')):
            scene=deepcopy(original);scene['parts'][0]['face']['nose_width']=value
            with self.assertRaises(ValueError):validate_scene(scene)
        scene=deepcopy(original)
        scene['parts'].append({'kind':'ellipsoid','name':'extra nose','material':scene['materials'][0]['name'],'center':[0,0,0],'radii':[.01,.01,.01]})
        with self.assertRaisesRegex(ValueError,'prostymi brylami'):validate_scene(scene)

    def test_bust_does_not_require_hidden_hands_and_gift_recipient_is_not_a_person_request(self):
        scene=json.loads((EXAMPLES/'portrait-floor-components.scene.json').read_text());scene['subject_type']='portrait';scene['parts']=scene['parts'][:1]
        validate_scene(scene)
        self.assertEqual(parse_scene((EXAMPLES/'oak-lights.scene.json').read_text(),'Dąb dla Cardi B')['subject_type'],'object')


if __name__=='__main__':unittest.main()
