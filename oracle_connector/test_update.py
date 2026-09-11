import io
import json
from pathlib import Path
import sqlite3
import shutil
import tempfile
import unittest
from unittest.mock import patch

import apply_update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source, self.target = self.root / 'incoming', self.root / 'installed'
        self.source.mkdir(); (self.target / 'state').mkdir(parents=True)
        (self.source / 'server.py').write_text('version = 2\n')
        (self.source / 'ai_stream.py').write_text('updated = True\n')
        (self.source / 'openai_provider.py').write_text('model = "gpt-6-astra"\n')
        (self.source / 'photo_input.py').write_text('max_photos = 4\n')
        (self.source / 'image3d_fixture.py').write_text('offline_only = True\n')
        (self.source / 'face_measurement.py').write_text('measurement_revision = 1\n')
        (self.source / 'visual_review.py').write_text('max_refinements = 1\n')
        for name in ('generation_budget.py','quality_report.py','v23_fixture.py'):
            (self.source/name).write_text('v23 = True\n')
        (self.source / 'runtime_check.py').write_text('cpu_limit = 2\n')
        (self.source / 'code_policy.py').write_text('policy = "strict-with-early-check"\n')
        (self.target / 'code_policy.py').write_text('policy = "strict"\n')
        (self.target / 'server.py').write_text('version = 1\n')
        (self.source / 'runtime').mkdir()
        for name in ('freeform_geometry.py','projection_math.py','photo_projection.py','model_checkpoint.py'):
            (self.source/'runtime'/name).write_text('v23 = True\n')
        (self.target / 'runtime').mkdir()
        (self.source / 'runtime/run.py').write_text('preserve_packed_images = True\n')
        (self.source / 'runtime/scene_contract.py').write_text('schema_version = 1\n')
        (self.source / 'runtime/build_scene.py').write_text('data_only = True\n')
        (self.source / 'runtime/detailed_geometry.py').write_text('geometry_version = 7\n')
        (self.target / 'runtime/run.py').write_text('preserve_packed_images = False\n')
        (self.source / 'runtime/anatomy.py').write_text('anatomy_version = 8\n')
        (self.source / 'runtime/wardrobe.py').write_text('wardrobe_version = 10\n')
        (self.source / 'runtime/textiles.py').write_text('textiles_version = 10\n')
        for name in ('portrait.py','portrait_eyes.py','portrait_shape.py','portrait_orbits.py','portrait_hands.py','portrait_hair.py','portrait_hair_surface.py','portrait_locks.py','fashion.py','couture.py','couture_geometry.py','couture_qa.py','review_views.py','scene_exports.py','imported_asset.py'):
            (self.source/'runtime'/name).write_text('quality_revision = 1\n')
        shutil.copytree(Path(__file__).parent/'runtime/assets', self.source/'runtime/assets')
        for name in ('photo_face.py','photo_face_color.py','reference_surfaces.py','reference_quality.py','reference_match.py'):
            (self.source/'runtime'/name).write_text('face_fit_revision = 1\n')
        self.config = self.target / 'state/config.json'
        self.config.write_text(json.dumps({'token': 'local-test-token', 'client': 'owner', 'code': 'unchanged'}))
        self.original_config = self.config.read_bytes()
        with sqlite3.connect(self.target / 'state/jobs.sqlite') as db:
            db.execute('CREATE TABLE jobs(state TEXT)')
        self.runtime_check = patch.object(apply_update, 'setup_runtime')
        self.runtime_check.start()

    def tearDown(self):
        self.runtime_check.stop()
        self.temp.cleanup()

    def test_export_check_failure_restores_code_and_preserves_state(self):
        original = (self.target / 'runtime/run.py').read_bytes()
        def fail_export(target):
            self.assertEqual((target / 'runtime/run.py').read_bytes(), (self.source / 'runtime/run.py').read_bytes())
            raise RuntimeError('GLB lost normal maps')
        with patch.object(apply_update.subprocess, 'run') as service, self.assertRaisesRegex(RuntimeError, 'GLB lost normal maps'):
            apply_update.update(self.source, self.target, verify=fail_export)
        self.assertEqual((self.target / 'runtime/run.py').read_bytes(), original)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual(service.call_args.args[0][-2:], ['start', 'froge-worker.service'])

    def test_update_preserves_pairing_and_keeps_backup(self):
        with patch.object(apply_update.subprocess, 'run') as service, patch.object(apply_update.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps({'connectorVersion': apply_update.EXPECTED_VERSION, 'freeformGeometryRevision':1, 'photoProjectionRevision':1, 'photoReviewReservedSeconds':240, 'astraPhotoRevision': 1, 'rendererRevision': 3, 'portraitRevision': 2, 'characterStandard': 20, 'coutureRevision': 2, 'referenceQualityRevision': 1, 'materialQualityRevision': 2, 'interchangeRevision': 2, 'portraitGeometryRevision': 2, 'registeredReferenceRevision': 1}).encode())):
            apply_update.update(self.source, self.target)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 2\n')
        self.assertEqual((self.target / 'code_policy.py').read_text(), 'policy = "strict-with-early-check"\n')
        self.assertEqual((self.target / 'runtime/run.py').read_text(), 'preserve_packed_images = True\n')
        self.assertTrue((self.target / 'runtime/scene_contract.py').is_file())
        self.assertTrue((self.target / 'runtime/build_scene.py').is_file())
        self.assertTrue((self.target / 'runtime/detailed_geometry.py').is_file())
        self.assertTrue((self.target / 'photo_input.py').is_file())
        backups = list((self.target / 'state/code-backups').glob('*/server.py'))
        self.assertEqual(backups[0].read_text(), 'version = 1\n')
        self.assertEqual((backups[0].parent / 'runtime/run.py').read_text(), 'preserve_packed_images = False\n')
        self.assertEqual([call.args[0][-1] for call in service.call_args_list], ['froge-worker.service'] * 2)

    def test_active_job_prevents_service_stop_and_code_replacement(self):
        with sqlite3.connect(self.target / 'state/jobs.sqlite') as db:
            db.execute("INSERT INTO jobs VALUES ('generating')")
        with patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError, 'aktywne'):
                apply_update.update(self.source, self.target)
            service.assert_not_called()
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_failed_health_check_restores_previous_code_and_pairing(self):
        with patch.object(apply_update.subprocess, 'run'), patch.object(apply_update.urllib.request, 'urlopen', side_effect=OSError('offline')), patch.object(apply_update.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'nie potwierdzil'):
                apply_update.update(self.source, self.target)
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertFalse((self.target / 'ai_stream.py').exists())
        self.assertFalse((self.target / 'openai_provider.py').exists())
        self.assertFalse((self.target / 'photo_input.py').exists())
        self.assertFalse((self.target / 'runtime/scene_contract.py').exists())
        self.assertFalse((self.target / 'runtime/build_scene.py').exists())
        self.assertFalse((self.target / 'runtime/detailed_geometry.py').exists())
        self.assertEqual((self.target / 'code_policy.py').read_text(), 'policy = "strict"\n')
        self.assertEqual((self.target / 'runtime/run.py').read_text(), 'preserve_packed_images = False\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_missing_anatomy_keeps_installed_worker_running(self):
        (self.source / 'runtime/assets/anatomy.json.gz').unlink()
        with patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaises(FileNotFoundError):apply_update.update(self.source,self.target)
            service.assert_not_called()
        self.assertEqual(self.config.read_bytes(),self.original_config)

    def test_damaged_skin_is_rejected_before_service_stop(self):
        (self.source / 'runtime/assets/male-skin.png').write_bytes(b'truncated')
        with patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError,'uszkodzone'):apply_update.update(self.source,self.target)
            service.assert_not_called()
        self.assertEqual((self.target / 'server.py').read_text(),'version = 1\n')

    def test_runtime_failure_stops_update_before_replacing_code_or_stopping_worker(self):
        with patch.object(apply_update, 'setup_runtime', side_effect=apply_update.RuntimeUnavailable('controller `cpu` is not available')), patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError, 'Kontener Blendera'):
                apply_update.update(self.source, self.target)
            service.assert_not_called()
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)


if __name__ == '__main__':
    unittest.main()
