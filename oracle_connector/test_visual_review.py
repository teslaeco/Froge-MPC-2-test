"""Review orchestration regression tests; provider responses are test doubles.

These verify rollback, cancellation, scope and shared budgets, not visual taste.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock
from runtime.scene_contract import parse_scene
from visual_review import refine,review_content


class VisualReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);(self.folder/'review').mkdir()
        self.scene=parse_scene((Path(__file__).parent/'examples/couture-fan-v20.scene.json').read_text())
        self.cancel=threading.Event()
        for label in ('front','three-quarter','face','side','back'):
            (self.folder/'review'/(label+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*24)
        for name in ('scene.json','model.glb','model.blend','result.json'):(self.folder/name).write_bytes(b'original-'+name.encode())

    def response(self,scene=None):
        value=deepcopy(scene or self.scene);value['parts'][0]['fan']['radius']=.34
        return json.dumps({'action':'refine','issues':['Fan too large'],'scene':value})

    def test_reference_and_five_actual_views_are_sent_without_external_urls(self):
        content=review_content('Original request',[],self.folder,self.scene)
        images=[c['image_url'] for c in content if c.get('type')=='input_image']
        self.assertEqual(len(images),5)
        self.assertTrue(all(x.startswith('data:image/png;base64,') for x in images))

    def test_refinement_uses_remaining_cumulative_budgets_and_retains_original(self):
        generate=Mock(return_value=self.response());build=Mock()
        clock=iter((10.,14.,20.,26.)).__next__
        ai,blender,report=refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,generate,build,550,840,clock=clock)
        self.assertEqual(generate.call_args.args[2],50)
        build.assert_called_once_with(60)
        self.assertEqual((ai,blender),(554,846));self.assertEqual(report['refinements'],1)
        self.assertEqual((self.folder/'before-refinement/model.glb').read_bytes(),b'original-model.glb')
        self.assertFalse(report['likeness_verified'])

    def test_failed_rebuild_restores_the_previous_model_and_scene(self):
        (self.folder/'model.fbx').write_bytes(b'original fbx')
        (self.folder/'textures').mkdir()
        (self.folder/'textures/skin.png').write_bytes(b'original skin')
        def fail(_):
            (self.folder/'model.glb').write_bytes(b'broken candidate')
            (self.folder/'model.fbx').write_bytes(b'new fbx')
            (self.folder/'model.obj').write_bytes(b'new obj with no original')
            (self.folder/'textures/skin.png').write_bytes(b'new skin')
            (self.folder/'textures/stale.png').write_bytes(b'new texture')
            raise ValueError('geometry failed')
        _,_,report=refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,lambda *_:self.response(),fail)
        self.assertEqual(report['status'],'original_retained')
        self.assertEqual((self.folder/'model.glb').read_bytes(),b'original-model.glb')
        self.assertEqual((self.folder/'scene.json').read_bytes(),b'original-scene.json')
        self.assertEqual((self.folder/'model.fbx').read_bytes(),b'original fbx')
        self.assertEqual((self.folder/'textures/skin.png').read_bytes(),b'original skin')
        self.assertFalse((self.folder/'model.obj').exists())
        self.assertFalse((self.folder/'textures/stale.png').exists())

    def test_cancellation_after_provider_does_not_start_a_rebuild(self):
        def generate(*_):self.cancel.set();return self.response()
        build=Mock()
        with self.assertRaises(InterruptedError):refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,generate,build)
        build.assert_not_called()

    def test_identity_scope_and_missing_views_stop_refinement(self):
        changed=deepcopy(self.scene);changed['parts'][0]['name']='different-person'
        build=Mock()
        _,_,report=refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,lambda *_:self.response(changed),build)
        self.assertEqual(report['status'],'original_retained');build.assert_not_called()
        (self.folder/'review/face.png').unlink();generate=Mock()
        refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,generate,build)
        generate.assert_not_called()

    def test_exhausted_budget_never_buys_another_plan(self):
        generate=Mock();build=Mock()
        _,_,report=refine(self.scene,'Kobieta w sukni',[],self.folder,self.cancel,generate,build,599,899)
        self.assertEqual(report['status'],'budget_exhausted');generate.assert_not_called();build.assert_not_called()


if __name__=='__main__':unittest.main()
