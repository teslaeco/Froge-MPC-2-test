"""Review capability/failure checks; no paid AI or simulated quality claims."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PNG=b'\x89PNG\r\n\x1a\n'+b'0'*32+b'\x00\x00\x00\x00IEND\xaeB`\x82'
OIDN='Error: Failed to denoise, build has no OpenImageDenoise support'


class ReviewViewTests(unittest.TestCase):
    def setUp(self):
        self.bpy=SimpleNamespace(ops=SimpleNamespace(render=SimpleNamespace(render=Mock())))
        spec=importlib.util.spec_from_file_location('review_fixture',Path(__file__).parent/'runtime/review_views.py')
        self.module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'bpy':self.bpy,'mathutils':SimpleNamespace(Vector=Mock())}):
            spec.loader.exec_module(self.module)
        self.scene=SimpleNamespace(render=SimpleNamespace(),cycles=SimpleNamespace(denoising_use_gpu=True))
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def test_supported_and_unsupported_builds_use_cpu_with_bounded_samples(self):
        for available in (True,False):
            with self.subTest(available=available),patch.dict(sys.modules,{'_cycles':SimpleNamespace(with_openimagedenoise=available)}):
                settings=self.module.configure_review(self.scene)
                self.assertEqual(self.scene.cycles.use_denoising,available)
                self.assertEqual(self.scene.cycles.samples,12 if available else 64)
                self.assertEqual(settings['device'],'CPU')
                if available:self.assertFalse(self.scene.cycles.denoising_use_gpu)
        with patch.dict(sys.modules,{'_cycles':None}):
            self.assertEqual(self.module.configure_review(self.scene)['denoiser'],'none')

    def test_known_runtime_error_retries_once_without_denoising(self):
        with patch.dict(sys.modules,{'_cycles':SimpleNamespace(with_openimagedenoise=True)}):
            settings=self.module.configure_review(self.scene)
            calls=[]
            def render(**kwargs):
                calls.append(self.scene.cycles.use_denoising)
                if len(calls)==1:raise RuntimeError(OIDN)
                Path(self.scene.render.filepath).write_bytes(PNG)
            self.bpy.ops.render.render.side_effect=render
            self.module.render_frame(self.scene,self.folder/'front.png',settings)
            self.assertEqual(calls,[True,False])
            self.assertEqual(settings['reason'],'oidn_runtime_unavailable')
            self.assertEqual((self.folder/'front.png').read_bytes(),PNG)
            self.assertFalse((self.folder/'front.pending.png').exists())

    def test_repeated_and_unrelated_failures_do_not_loop(self):
        for message,calls in ((OIDN,2),('Out of memory',1)):
            with self.subTest(message=message),patch.dict(sys.modules,{'_cycles':SimpleNamespace(with_openimagedenoise=True)}):
                settings=self.module.configure_review(self.scene)
                self.bpy.ops.render.render.reset_mock()
                self.bpy.ops.render.render.side_effect=RuntimeError(message)
                with self.assertRaises(RuntimeError):
                    self.module.render_frame(self.scene,self.folder/'front.png',settings)
                self.assertEqual(self.bpy.ops.render.render.call_count,calls)

    def test_truncated_render_is_not_published(self):
        with patch.dict(sys.modules,{'_cycles':None}):settings=self.module.configure_review(self.scene)
        self.bpy.ops.render.render.side_effect=lambda **kw:Path(self.scene.render.filepath).write_bytes(PNG[:-6])
        with self.assertRaises(ValueError):self.module.render_frame(self.scene,self.folder/'front.png',settings)
        self.assertFalse((self.folder/'front.png').exists())

    def test_optional_review_failure_preserves_model_and_removes_stale_views(self):
        model=self.folder/'model.glb';model.write_bytes(b'preserved-model')
        review=self.folder/'review';review.mkdir()
        for label in self.module.LABELS:(review/(label+'.png')).write_bytes(PNG)
        with patch.object(self.module,'render_review',side_effect=RuntimeError('render failed')):
            report=self.module.render_review_checked(model,review)
        self.assertEqual(report['status'],'unavailable')
        self.assertFalse(report['likeness_verified'])
        self.assertEqual(model.read_bytes(),b'preserved-model')
        self.assertFalse(list(review.glob('*.png')))


if __name__=='__main__':unittest.main()
