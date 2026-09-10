from copy import deepcopy
import json
from pathlib import Path
import unittest
from runtime.scene_contract import parse_scene,validate_scene
from runtime.portrait_orbits import relaxed_lid_point
from runtime.portrait_shape import point,profile,brow_height,measured_gaze

EXAMPLES=Path(__file__).parent/'examples'


class PortraitQualityTests(unittest.TestCase):
    def test_measured_gaze_ignores_unreliable_iris_depth_and_keeps_eyes_conjugate(self):
        baseline={'width':1000,'height':1000,'points':[[.5,.5,0.] for _ in range(478)]}
        for iris,a,b,cx in ((468,33,133,.3),(473,362,263,.7)):
            baseline['points'][a]=[cx-.05,.5,0.]
            baseline['points'][b]=[cx+.05,.5,0.]
            baseline['points'][iris]=[cx,.5,0.]
        self.assertEqual(measured_gaze(baseline,baseline),(0.,0.))
        target=deepcopy(baseline)
        for iris in (468,473):
            target['points'][iris][0]+=.01
            target['points'][iris][1]+=.005
            target['points'][iris][2]=-.8 if iris==468 else .7
        horizontal,vertical=measured_gaze(target,baseline)
        self.assertAlmostEqual(horizontal,.19)
        self.assertAlmostEqual(vertical,-.095)
        target['points'][468][2]=0;target['points'][473][2]=0
        self.assertEqual(measured_gaze(target,baseline),(horizontal,vertical))
        # A missed iris outside its aperture must not turn either eye sideways.
        target['points'][468][0]=.9
        self.assertEqual(measured_gaze(target,baseline),(0.,0.))

    def test_glam_brow_arch_peaks_outside_the_pupil_not_above_inner_corner(self):
        heights=[brow_height(i/100,1.68,True) for i in range(101)]
        peak=max(range(101),key=lambda i:heights[i])
        self.assertGreater(peak,50);self.assertLess(peak,80)
        self.assertGreater(heights[peak]-heights[0],.005)

    def test_lip_fullness_projects_both_lips_without_a_philtrum_bulge(self):
        controls=profile({'lip_fullness':1})
        upper=(.008,-.15,1.618);lower=(.008,-.15,1.606);philtrum=(.008,-.15,1.633)
        upper_projection=upper[1]-point(upper,controls)[1]
        lower_projection=lower[1]-point(lower,controls)[1]
        self.assertGreater(upper_projection,.003)
        self.assertGreater(lower_projection,.003)
        self.assertLess(philtrum[1]-point(philtrum,controls)[1],upper_projection*.1)

    def test_soft_glam_lid_aperture_is_smaller_with_heavier_upper_lid(self):
        center=(0,-.085,1.69)
        upper=(0,-.10,1.704)
        lower=(0,-.10,1.676)
        neutral_upper=relaxed_lid_point(upper,center)
        neutral_lower=relaxed_lid_point(lower,center)
        glam_upper=relaxed_lid_point(upper,center,.36,.08)
        glam_lower=relaxed_lid_point(lower,center,.36,.08)
        self.assertLess(glam_upper[2]-glam_lower[2],neutral_upper[2]-neutral_lower[2])
        self.assertLess(glam_upper[2]-center[2],center[2]-glam_lower[2])
        self.assertEqual(relaxed_lid_point((.03,-.1,1.704),center,.36,.08),(.03,-.1,1.704))

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
