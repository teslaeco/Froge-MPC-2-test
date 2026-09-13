"""Actual HTTP queue and worker routing; fixture models, no paid API or likeness claim."""
import base64
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import codex_runner
import server
from blender_mcp import JobTools, completed_outcome
from image3d_fixture import make_fixture
from runtime.model_checkpoint import save_ready


JOB = '12345678-1234-4234-8234-123456789abc'
REPLAY = '12345678-1234-4234-8234-123456789abd'
FAKE_KEY = 'sk-queue-fixture-' + 'x' * 30
ROOT = Path(__file__).resolve().parent


class WorkerHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = patch.multiple(server, STATE=root / 'state', JOBS=root / 'state/jobs', CONFIG=root / 'state/config.json')
        self.paths.start()
        server.RUNNING.clear(); server.CANCEL.clear(); server.initialize()
        server.write_json(server.STATE / 'ai-provider.json', {'provider': 'openai', 'api_key': FAKE_KEY})
        self.token = json.loads(server.CONFIG.read_text())['token']
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        server.RUNNING.clear(); server.CANCEL.clear()
        self.paths.stop(); self.temp.cleanup()

    def call(self, path, data=None):
        request = urllib.request.Request('http://127.0.0.1:%d%s' % (self.http.server_port, path),
            data=None if data is None else json.dumps(data).encode(),
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def drain_one(self):
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'):
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()

    def test_queued_photo_instructions_reach_codex_and_unaccepted_model_stays_draft(self):
        image = bytes([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
        photo = {'name': 'front.jpg', 'view': 'front', 'dataUrl': 'data:image/jpeg;base64,' + base64.b64encode(image).decode()}
        request = {'id': JOB, 'prompt': 'Rakieta', 'agentInstructions': 'Dodaj pomaranczowe stateczniki', 'photos': [photo]}

        def run_fixture(folder, prompt, instructions, key, cancelled, progress):
            self.assertEqual((folder / 'reference-0.jpg').read_bytes(), image)
            self.assertEqual((prompt, instructions, key), (request['prompt'], request['agentInstructions'], FAKE_KEY))
            self.assertEqual(json.loads((folder / 'provider.json').read_text())['executor'], 'codex-mcp')
            server.write_json(folder / 'agent-request.json', {'prompt': prompt, 'instructions': instructions})

            def build(current):
                (current / 'model.glb').write_bytes(make_fixture())
                report = {'triangles': 12, 'master_export': {'formats': ['glb']}}
                server.write_json(current / 'result.json', report)
                save_ready(current, report, 'core_export')

            def finalize(current):
                save_ready(current, json.loads((current / 'result.json').read_text()), 'interchange_exports')

            job = JobTools(folder, build=build, finalize=finalize)
            scene = json.loads((ROOT / 'examples/rocket.scene.json').read_text())
            scene['version'] = 2
            scene['reference_views'] = [{'photo_index': 0, 'position': [0,-3,1], 'target': [0,0,1], 'up': [0,0,1],
                'projection': 'orthographic', 'vertical_span': 3, 'fov': 1,
                'regions': [{'part': 'hull', 'polygon': [[0,0],[1,0],[1,1],[0,1]]}]}]
            job.call('build_model', {'scene_json': json.dumps(scene), 'expected_revision': 0})
            job.call('finish_model', {'expected_revision': 1, 'accepted': False,
                'issues': ['Fixture requires visual review'], 'summary': 'Queue fixture only'})
            progress('Zapisano wynik roboczy.')
            return completed_outcome(folder)

        with patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')) as executable, \
             patch.object(codex_runner, 'run', side_effect=run_fixture) as run, \
             patch.object(server, 'generate_code') as legacy, patch.object(server.openai_provider, 'generate') as api:
            self.assertEqual(self.call('/v1/jobs', request)[0], 202)
            self.drain_one()
            executable.assert_called(); run.assert_called_once(); legacy.assert_not_called(); api.assert_not_called()
        result = self.call('/v1/jobs/' + JOB)[1]
        self.assertEqual(result['state'], 'succeeded', result['detail'])
        self.assertEqual(result['modelStatus'], 'draft')
        self.assertIn('Wynik roboczy', result['detail'])
        report = self.call('/v1/jobs/' + JOB + '/quality')[1]
        self.assertEqual(report['executor'], 'codex-mcp')
        self.assertTrue(report['hasModel']); self.assertFalse(report['automaticQualityAccepted'])
        self.assertFalse(report['agent']['accepted'])
        self.assertEqual((server.JOBS / JOB / 'model.glb').read_bytes(), make_fixture())

    def test_missing_verified_codex_is_unready_and_rejected_before_queue_or_paid_api(self):
        with patch.object(codex_runner, 'executable', return_value=None), \
             patch.object(codex_runner, 'run') as run, patch.object(server, 'generate_code') as legacy, \
             patch.object(server.openai_provider, 'generate') as api:
            health = self.call('/v1/health')[1]
            self.assertFalse(health['ready']); self.assertFalse(health['textReady']); self.assertFalse(health['photoInput'])
            self.assertFalse(health['codexReady']); self.assertEqual(health['executionEngine'], 'codex-mcp')
            status, result = self.call('/v1/jobs', {'id': JOB, 'prompt': 'Rakieta'})
            self.assertEqual(status, 409); self.assertIn('Codex + Blender MCP', result['error'])
            self.assertNotIn(FAKE_KEY, json.dumps(health) + json.dumps(result))
            self.assertFalse((server.JOBS / JOB).exists())
            with server.database() as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 0)
            run.assert_not_called(); legacy.assert_not_called(); api.assert_not_called()

    def test_codex_disappearing_after_admission_fails_without_legacy_fallback(self):
        with patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')):
            self.assertEqual(self.call('/v1/jobs', {'id': JOB, 'prompt': 'Rakieta'})[0], 202)
        with patch.object(codex_runner, 'executable', return_value=None), \
             patch.object(codex_runner, 'run') as run, patch.object(server, 'generate_code') as legacy, \
             patch.object(server.openai_provider, 'generate') as api, patch.object(server, 'run_blender') as blender:
            self.drain_one()
            run.assert_not_called(); legacy.assert_not_called(); api.assert_not_called(); blender.assert_not_called()
        result = self.call('/v1/jobs/' + JOB)[1]
        self.assertEqual(result['state'], 'failed'); self.assertEqual(result['modelStatus'], 'none')
        self.assertIn('Nie wyslano platnego', result['detail'])
        provider = json.loads((server.JOBS / JOB / 'provider.json').read_text())
        self.assertEqual(provider['executor'], 'codex-mcp')
        self.assertFalse((server.JOBS / JOB / 'scene.json').exists())

    def save_source(self, name, text):
        folder = server.JOBS / JOB; folder.mkdir(exist_ok=True)
        (folder / name).write_text(text, encoding='utf-8')
        with server.database() as db:
            db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,0,0)', (JOB, 'Obiekt kontrolny', 'failed', 'Fixture'))
        return {'id': REPLAY, 'prompt': 'Obiekt kontrolny', 'sourceJobId': JOB}

    def test_large_supported_scene_replays_without_codex_or_any_ai(self):
        scene = json.loads((ROOT / 'examples/rocket.scene.json').read_text())
        scene['parts'] = [{'kind': 'mesh', 'name': 'grid', 'material': 'ceramic',
            'vertices': [[x / 63, y / 63, 0] for y in range(64) for x in range(64)],
            'faces': [[y * 64 + x, y * 64 + x + 1, (y + 1) * 64 + x + 1, (y + 1) * 64 + x]
                      for y in range(63) for x in range(63)]}]
        text = json.dumps(scene, separators=(',', ':'))
        self.assertGreater(len(text.encode()), 60000); self.assertLessEqual(len(text.encode()), 256000)
        server.parse_scene(text, 'Obiekt kontrolny')
        request = self.save_source('scene.json', text)
        with patch.object(codex_runner, 'executable', return_value=None), \
             patch.object(codex_runner, 'run') as run, patch.object(server, 'generate_code') as legacy, \
             patch.object(server.openai_provider, 'generate') as api, patch.object(server, 'run_blender') as blender, \
             patch.object(server, 'ai_settings') as settings:
            self.assertEqual(self.call('/v1/jobs', request)[0], 202)
            self.drain_one()
            run.assert_not_called(); legacy.assert_not_called(); api.assert_not_called(); settings.assert_not_called()
            blender.assert_called_once()
        self.assertEqual((server.JOBS / JOB / 'scene.json').read_text(), text)
        self.assertEqual((server.JOBS / REPLAY / 'saved-scene.json').read_text(), text)
        self.assertEqual(self.call('/v1/jobs/' + REPLAY)[1]['state'], 'succeeded')

    def test_scene_and_python_replay_keep_distinct_size_limits_and_originals(self):
        scene = (ROOT / 'examples/rocket.scene.json').read_text()
        too_large = scene + ' ' * (256001 - len(scene.encode()))
        request = self.save_source('scene.json', too_large)
        self.assertEqual(self.call('/v1/jobs', request)[0], 409)
        self.assertFalse((server.JOBS / REPLAY).exists())
        self.assertEqual((server.JOBS / JOB / 'scene.json').read_text(), too_large)
        (server.JOBS / JOB / 'scene.json').unlink()
        script = '#' + 'x' * 60000
        self.save_source('generate.py', script)
        status, result = self.call('/v1/jobs', request)
        self.assertEqual(status, 409); self.assertIn('60000', result['error'])
        self.assertFalse((server.JOBS / REPLAY).exists())
        self.assertEqual((server.JOBS / JOB / 'generate.py').read_text(), script)

    def test_saved_python_replays_with_openai_selected_without_buying_codex_run(self):
        script = 'metal = make_material("metal", (0.2,0.3,0.4), "metal")\n'
        request = self.save_source('generate.py', script)
        with patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')), \
             patch.object(codex_runner, 'run') as run, patch.object(server, 'generate_code') as legacy, \
             patch.object(server.openai_provider, 'generate') as api, patch.object(server, 'run_blender') as blender:
            self.assertEqual(self.call('/v1/jobs', request)[0], 202)
            self.drain_one()
            run.assert_not_called(); legacy.assert_not_called(); api.assert_not_called(); blender.assert_called_once()
        self.assertEqual(json.loads((server.JOBS / REPLAY / 'provider.json').read_text())['provider'], 'saved-script')
        self.assertEqual((server.JOBS / JOB / 'generate.py').read_text(), script)


if __name__ == '__main__':
    unittest.main()
