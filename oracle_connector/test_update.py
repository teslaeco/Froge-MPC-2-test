import io
import json
import os
from pathlib import Path
import sqlite3
import shutil
import stat
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
        for name in ('verify_anatomy_edit.py','verify_edit_runtime.py','agent_limits.py','paid_trial.py','generation_budget.py','quality_report.py','v23_fixture.py','scene_repair.py','blender_mcp.py','codex_runner.py','install_codex.py','codex_smoke.py'):
            (self.source/name).write_text('v23 = True\n')
        (self.source / 'runtime_check.py').write_text('cpu_limit = 2\n')
        (self.source / 'code_policy.py').write_text('policy = "strict-with-early-check"\n')
        (self.target / 'code_policy.py').write_text('policy = "strict"\n')
        (self.target / 'server.py').write_text('version = 1\n')
        (self.source / 'runtime').mkdir()
        for name in ('freeform_geometry.py','projection_math.py','photo_projection.py','model_checkpoint.py','finalize.py'):
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
        self.codex_install=patch('install_codex.install')
        self.codex_install.start()

    def tearDown(self):
        self.runtime_check.stop()
        self.codex_install.stop()
        self.temp.cleanup()

    def installed_tools(self):
        folder = self.target / 'tools' / 'codex'
        folder.mkdir(parents=True, exist_ok=True)
        result = {}
        for index, name in enumerate(apply_update.CODEX_FILES):
            path = folder / name
            path.write_bytes(('old-' + name).encode())
            mode = (0o750 if index else 0o700) if index < 2 else 0o600
            os.chmod(path, mode)
            result[name] = (path.read_bytes(), mode)
        return result

    def assert_tools_unchanged(self, expected):
        for name, (content, mode) in expected.items():
            path = self.target / 'tools' / 'codex' / name
            self.assertEqual(path.read_bytes(), content, name)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode, name)

    def stage_tools(self, folder):
        self.assertNotEqual(folder, self.target / 'tools' / 'codex')
        for name in apply_update.CODEX_FILES:
            path = folder / name
            path.write_bytes(('new-' + name).encode())
            os.chmod(path, 0o700 if name in ('codex', 'codex-code-mode-host') else 0o600)

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
        with patch.object(apply_update.subprocess, 'run') as service, patch.object(apply_update.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps({'executionEngine':'codex-mcp', 'connectorVersion': apply_update.EXPECTED_VERSION, 'instructionsRevision':1, 'freeformGeometryRevision':1, 'photoProjectionRevision':1, 'photoReviewReservedSeconds':240, 'astraPhotoRevision': 1, 'rendererRevision': 3, 'portraitRevision': 2, 'characterStandard': 20, 'coutureRevision': 2, 'referenceQualityRevision': 1, 'materialQualityRevision': 2, 'interchangeRevision': 2, 'portraitGeometryRevision': 2, 'registeredReferenceRevision': 1}).encode())):
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
        self.assertEqual([call.args[0][-1] for call in service.call_args_list if call.args[0][0]=='systemctl'], ['froge-worker.service'] * 2)
        self.assertTrue(any(call.args[0][-2:]==[str(self.target/'codex_smoke.py'),'--build'] for call in service.call_args_list))

    def test_failed_mcp_gate_restores_previous_verification_and_code(self):
        receipt=self.target/'tools/codex/verified.json';receipt.parent.mkdir(parents=True)
        receipt.write_text('{"old":"verified"}')
        def fail(args,**kwargs):
            if args[-2:]==[str(self.target/'codex_smoke.py'),'--build']:
                receipt.write_text('{"new":"invalid"}')
                raise RuntimeError('MCP gate failed')
        with patch.object(apply_update.subprocess,'run',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError,'MCP gate failed'):
                apply_update.update(self.source,self.target)
        self.assertEqual(receipt.read_text(),'{"old":"verified"}')
        self.assertEqual((self.target/'server.py').read_text(),'version = 1\n')
        self.assertEqual(self.config.read_bytes(),self.original_config)

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

    def test_partial_cli_or_host_install_failure_never_replaces_active_tools(self):
        original = self.installed_tools()
        for failed_phase in ('CLI', 'Code Mode host'):
            with self.subTest(failed_phase=failed_phase):
                def fail(folder):
                    self.stage_tools(folder)
                    raise RuntimeError(failed_phase + ' download failed')
                with patch('install_codex.install', side_effect=fail), patch.object(apply_update.subprocess, 'run') as service:
                    with self.assertRaisesRegex(RuntimeError, 'download failed'):
                        apply_update.update(self.source, self.target)
                    service.assert_not_called()
                self.assert_tools_unchanged(original)
                self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
                self.assertFalse(list(self.target.parent.glob('.froge-update-*')))
                self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_fresh_cli_install_then_host_failure_leaves_no_active_codex(self):
        def fail(folder):
            (folder / 'codex').write_bytes(b'new CLI before host failure')
            os.chmod(folder / 'codex', 0o700)
            raise RuntimeError('Code Mode host download failed')
        with patch('install_codex.install', side_effect=fail), patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError, 'host download failed'):
                apply_update.update(self.source, self.target)
            service.assert_not_called()
        self.assertFalse((self.target / 'tools' / 'codex').exists())
        self.assertFalse(list(self.target.parent.glob('.froge-update-*')))
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_failed_gate_restores_binaries_receipts_and_original_permissions(self):
        original = self.installed_tools()
        marker = self.target / 'tools' / 'codex' / 'existing-marker.txt'
        marker.write_text('preserve the complete installed directory')
        os.chmod(self.target / 'tools' / 'codex', 0o750)
        os.chmod(self.target / 'server.py', 0o640)
        os.chmod(self.target / 'runtime/run.py', 0o750)
        def fail_gate(args, **kwargs):
            if args[-2:] == [str(self.target / 'codex_smoke.py'), '--build']:
                self.assertEqual((self.target / 'tools/codex/codex').read_bytes(), b'new-codex')
                (self.target / 'tools/codex/verified.json').write_text('failed gate receipt')
                raise RuntimeError('new model gate failed')
        with patch('install_codex.install', side_effect=self.stage_tools), patch.object(apply_update.subprocess, 'run', side_effect=fail_gate):
            with self.assertRaisesRegex(RuntimeError, 'new model gate failed'):
                apply_update.update(self.source, self.target)
        self.assert_tools_unchanged(original)
        self.assertEqual(stat.S_IMODE((self.target / 'tools/codex').stat().st_mode), 0o750)
        self.assertEqual(stat.S_IMODE((self.target / 'server.py').stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE((self.target / 'runtime/run.py').stat().st_mode), 0o750)
        self.assertEqual(marker.read_text(), 'preserve the complete installed directory')
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_failed_gate_removes_new_tools_when_previous_install_had_none(self):
        def fail_gate(args, **kwargs):
            if args[-2:] == [str(self.target / 'codex_smoke.py'), '--build']:
                raise RuntimeError('fresh gate failed')
        with patch('install_codex.install', side_effect=self.stage_tools), patch.object(apply_update.subprocess, 'run', side_effect=fail_gate):
            with self.assertRaisesRegex(RuntimeError, 'fresh gate failed'):
                apply_update.update(self.source, self.target)
        self.assertFalse((self.target / 'tools/codex').exists())
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_job_accepted_during_download_keeps_original_running_installation(self):
        original = self.installed_tools()
        def download(folder):
            self.stage_tools(folder)
            # This succeeds only if downloading does not hold a queue write lock.
            with sqlite3.connect(self.target / 'state/jobs.sqlite', timeout=.1) as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute("INSERT INTO jobs VALUES ('queued')")
        with patch('install_codex.install', side_effect=download), patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError, 'aktywne'):
                apply_update.update(self.source, self.target)
            service.assert_not_called()
        self.assert_tools_unchanged(original)
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)


if __name__ == '__main__':
    unittest.main()
