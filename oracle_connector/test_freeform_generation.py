"""Geometry/camera/budget correctness; these tests do not measure photo likeness."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from runtime.freeform_geometry import geometry,dimensions
from runtime.projection_math import project,inside,camera_basis
from runtime.scene_contract import validate_scene
from generation_budget import initial_ai_remaining,total_ai_limit,initial_blender_remaining
from quality_report import quality_report
from photo_input import validate_photo_plan


def surface(thickness=.02):
    return {'kind':'surface_grid','name':'panel','material':'blue',
        'control_grid':[[[x,0,z] for x in (0,.5,1)] for z in (0,.5,1)],'samples':3,'thickness':thickness}


def scene(p):
    return {'version':2,'name':'test','subject_type':'object','materials':[{'name':'blue','rgb':[0,.2,.8],
        'pattern':'plain','roughness':.5,'metallic':0,'emission':0}],'parts':[p],'reference_views':[]}


def view():
    return {'photo_index':0,'position':[0,-3,0],'target':[0,0,0],'up':[0,0,1],
        'projection':'orthographic','vertical_span':2,'fov':math.pi/2,
        'regions':[{'part':'panel','polygon':[[0,0],[1,0],[1,1],[0,1]]}]}


class FreeformTests(unittest.TestCase):
    def test_surface_budget_matches_mesh_and_shell_is_closed(self):
        p=surface();verts,faces,_=geometry(p)
        self.assertEqual(dimensions(p),(len(verts),sum(len(f)-2 for f in faces)))
        edges={}
        for face in faces:
            for a,b in zip(face,face[1:]+face[:1]):
                edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
        self.assertTrue(all(n==2 for n in edges.values()))
        self.assertAlmostEqual(max(v[1] for v in verts)-min(v[1] for v in verts),.02)

    def test_freeform_loft_preserves_asymmetric_controls(self):
        rings=[[[x,y,z] for x,y in ((-.3,-.2),(.5,-.2),(.4,.3),(-.2,.5))] for z in (0,.7,1.2)]
        p={'kind':'contour_loft','rings':rings,'samples':3,'caps':True}
        verts,faces,_=geometry(p)
        self.assertEqual(dimensions(p),(len(verts),sum(len(f)-2 for f in faces)))
        for ring in rings:
            for v in ring:self.assertIn(tuple(v),verts)

    def test_malformed_grid_and_missing_region_target_are_rejected(self):
        p=surface();p['control_grid'][1].pop()
        with self.assertRaises(ValueError):validate_scene(scene(p))
        s=scene(surface());v=view();v['regions'][0]['part']='missing';s['reference_views']=[v]
        with self.assertRaisesRegex(ValueError,'nieznana'):validate_scene(s)

    def test_camera_rejects_parallel_up_and_maps_axes(self):
        v=view()
        self.assertEqual(project((0,0,0),v,1),(.5,.5,3))
        self.assertEqual(project((1,0,1),v,1),(1.,0.,3))
        self.assertIsNone(project((0,-4,0),v,1))
        v['up']=[0,1,0]
        with self.assertRaises(ValueError):camera_basis(v)

    def test_perspective_changes_scale_with_depth(self):
        v=view();v['projection']='perspective'
        near=project((.5,-2,0),v,1);far=project((.5,-1,0),v,1)
        self.assertAlmostEqual(near[0]-.5,2*(far[0]-.5))

    def test_mask_rejects_concave_cutout_and_accepts_boundary(self):
        polygon=[[0,0],[1,0],[1,.4],[.4,.4],[.4,1],[0,1]]
        self.assertTrue(inside((.2,.8),polygon));self.assertFalse(inside((.8,.8),polygon))
        self.assertTrue(inside((.4,.8),polygon))

    def test_legacy_scene_gets_empty_projection_without_changing_version(self):
        s=scene(surface());s['version']=1;s.pop('reference_views')
        self.assertEqual(validate_scene(s)['reference_views'],[])
        self.assertEqual(s['version'],1)

    def test_new_photo_job_cannot_silently_use_an_untextured_preset(self):
        s=scene(surface())
        with self.assertRaisesRegex(ValueError,'reference_views'):validate_photo_plan(s,[{}])
        s['reference_views']=[view()];validate_photo_plan(s,[{}])
        s['reference_views'][0]['photo_index']=1
        with self.assertRaisesRegex(ValueError,'photo_index'):validate_photo_plan(s,[{}])

    def test_review_and_rebuild_reserves_survive_maximal_initial_work(self):
        self.assertEqual(total_ai_limit(True)-600,240)
        self.assertEqual(total_ai_limit(False),600)
        self.assertEqual(initial_ai_remaining(601),0)
        self.assertEqual(initial_blender_remaining(590,True),10)
        self.assertEqual(initial_blender_remaining(590,False),310)

    def test_generated_asset_is_not_automatically_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/'result.json').write_text(json.dumps({'triangles':100,'reference_likeness_verified':True}))
            report=quality_report(folder,'succeeded')
            self.assertFalse(report['automaticQualityAccepted']);self.assertFalse(report['likenessVerified'])
            self.assertEqual(report['visualReview']['status'],'not_completed')
            (folder/'visual-review.json').write_text('{broken')
            self.assertEqual(quality_report(folder,'succeeded')['visualReview']['status'],'not_completed')


if __name__=='__main__':unittest.main()
