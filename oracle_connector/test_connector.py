"""Contract tests use a real HTTP handler/SQLite; they do not simulate AI quality or a Blender render."""
import base64
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import server
from code_policy import CodePolicyError, StreamPolicyGuard, extract_code, prepare_code, repair_instruction, validate_code

JOB = '12345678-1234-4234-8234-123456789abc'

class CodePolicyTests(unittest.TestCase):
    def test_restores_reserved_helper_and_preserves_model_calls(self):
        raw = 'def make_material(name, rgb, pattern):\n    image.generated_type = "RGBA"\n    return None\nbark = make_material("trunk", (0.27,0.14,0.06), "bark")\n'
        code, replaced = prepare_code(raw)
        calls = []
        def trusted(*args):
            calls.append(args)
            return 'trusted material'
        scope = {'make_material': trusted}
        exec(code, scope)
        self.assertEqual(scope['bark'], 'trusted material')
        self.assertEqual(calls, [('trunk', (0.27,0.14,0.06), 'bark')])
        self.assertEqual(replaced, ['make_material'])
        self.assertNotIn('generated_type', code)
        for shadow in ['make_material = 4', 'def outer(make_material):\n    pass', 'from math import sin as make_material', 'def outer():\n    def make_material():\n        pass']:
            with self.subTest(shadow=shadow), self.assertRaises(ValueError):
                prepare_code(shadow)

    def test_helper_restoration_never_hides_forbidden_file_operations(self):
        with self.assertRaises(CodePolicyError):
            prepare_code('def make_material(name, rgb, pattern):\n    return bpy.data.images.load("file.png")\n')

    def test_rejects_load_while_streaming_and_gives_a_safe_material_repair(self):
        guard = StreamPolicyGuard()
        guard.feed('import bpy\ntexture = bpy.data.images.lo')
        with self.assertRaises(CodePolicyError) as failure:
            guard.feed('ad("invented_bark.png")\n')
        error = failure.exception
        self.assertEqual(error.operation, 'load')
        self.assertIn('invented_bark.png', error.partial_code)
        guidance = repair_instruction(error)
        self.assertIn('NO INPUT ASSET FILES EXIST', guidance)
        self.assertIn('make_material', guidance)
        self.assertIn('ORIGINAL requested object', guidance)

    def test_early_check_ignores_strings_comments_and_partial_attribute_names(self):
        guard = StreamPolicyGuard()
        for fragment in ['# Never call .load()\n', 'label = ".load()"\n',
                         '"""example: .load()\nstill just text"""\n',
                         'obj.lo', 'ad_more()\n']:
            guard.feed(fragment)
        validate_code(extract_code(guard.text))

    def test_complete_ast_check_still_rejects_file_access_and_hidden_operations(self):
        for bad in ['bpy.data.images.load("file.png")', 'open("file.png")',
                    'bpy.data.libraries.load("scene.blend")', 'import os',
                    'f"{bpy.data.images.load(chr(120))}"']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_code(bad)

    def test_material_examples_are_valid_and_use_existing_helpers(self):
        script = ('bark = make_material("oak_bark", (0.27, 0.14, 0.06), "bark")\n'
                  'leaves = make_material("oak_leaves", (0.12, 0.36, 0.05), "leaf")\n'
                  'tube("trunk", [(0,0,0), (0,0,2)], [0.2,0.1], bark)\n'
                  'mesh_object("leaf", [(0,0,2), (0.3,0.1,2.1), (0.1,0.3,2)], [(0,1,2)], leaves)\n')
        guard = StreamPolicyGuard()
        for line in script.splitlines(True):
            guard.feed(line)
        self.assertEqual(validate_code(script), script)

    def test_accepts_modeling_and_rejects_files_network_and_introspection(self):
        code = 'import math\nm = make_material("bark", (0.3, 0.2, 0.1), "bark")\nfor n in range(5):\n    ellipsoid("leaf", (n, 0, 1), (1, 1, 1), m)'
        self.assertEqual(validate_code(extract_code('```python\n' + code + '\n```')), code)
        for bad in ['import os', 'from pathlib import Path', 'open("/etc/passwd")', 'bpy.app.handlers', 'x.__class__', 'eval("1")', 'bpy.ops.wm.save_as_mainfile(filepath="x")']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_code(bad)

    def test_generated_code_container_has_only_scoped_mounts_and_limits(self):
        command = server.blender_command(JOB, Path('/jobs') / JOB)
        mounts = [command[i + 1] for i, arg in enumerate(command) if arg == '-v']
        self.assertEqual(len(mounts), 2)
        self.assertTrue(mounts[0].endswith('/runtime:/runner:ro,Z'))
        self.assertEqual(mounts[1], '/jobs/' + JOB + ':/work:rw,Z')
        for flag in ['--network=none', '--read-only', '--cap-drop=ALL', '--userns=keep-id', '--memory=4g', '--pids-limit=256']:
            self.assertIn(flag, command)

class WorkerHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = patch.multiple(server, STATE=root / 'state', JOBS=root / 'state/jobs', CONFIG=root / 'state/config.json')
        self.paths.start(); server.PAIR_ATTEMPTS.clear(); server.CANCEL.clear()
        server.initialize()
        self.config = json.loads(server.CONFIG.read_text())
        self.ready = patch.object(server, 'health', return_value={'ready': True, 'model': 'local-coder', 'detail': 'ready'})
        self.ready.start()
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True); self.thread.start()

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        self.ready.stop(); self.paths.stop(); self.temp.cleanup()

    def call(self, path, data=None, token=None):
        req = urllib.request.Request('http://127.0.0.1:%d%s' % (self.http.server_port, path), data=None if data is None else json.dumps(data).encode(), headers={'Authorization': 'Bearer ' + (self.config['token'] if token is None else token), 'Content-Type': 'application/json'})
        try:
            result = urllib.request.urlopen(req, timeout=3)
        except urllib.error.HTTPError as error:
            result = error
        with result:
            return result.status, json.loads(result.read())

    def test_pairing_is_expiring_client_bound_and_health_requires_token(self):
        self.assertEqual(self.call('/v1/health', token='invalid')[0], 401)
        status, data = self.call('/v1/pair', {'client': 'owner-a'}, self.config['code'])
        self.assertEqual(status, 200); self.assertEqual(data['token'], self.config['token'])
        self.assertEqual(self.call('/v1/pair', {'client': 'owner-b'}, self.config['code'])[0], 409)
        config = json.loads(server.CONFIG.read_text()); config['expires'] = time.time() - 1
        server.write_json(server.CONFIG, config)
        self.assertEqual(self.call('/v1/pair', {'client': 'owner-a'}, self.config['code'])[0], 401)
        self.assertNotIn(self.config['token'], json.dumps(self.call('/v1/health')))

    def test_saved_script_rebuild_preserves_original_and_never_calls_ai(self):
        original = 'def make_material(name, rgb, pattern):\n    image.generated_type = "RGBA"\nbark = make_material("trunk", (0.27,0.14,0.06), "bark")\n'
        folder = server.JOBS / JOB
        folder.mkdir(); (folder / 'generate.py').write_text(original)
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)', (JOB, 'Dab z lampkami', 'failed', 'RGBA'))
        rebuilt = '12345678-1234-4234-8234-123456789abd'
        status, _ = self.call('/v1/jobs', {'id': rebuilt, 'prompt': 'Dab z lampkami', 'sourceJobId': JOB})
        self.assertEqual(status, 202)
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'), patch.object(server, 'generate_code') as ai, patch.object(server, 'run_blender') as blender:
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()
            ai.assert_not_called()
            blender.assert_called_once()
        self.assertEqual((folder / 'generate.py').read_text(), original)
        self.assertNotIn('generated_type', (server.JOBS / rebuilt / 'generate.py').read_text())
        status, result = self.call('/v1/jobs/' + rebuilt)
        self.assertEqual(result['state'], 'succeeded')
        self.assertIn('bez nowego zapytania do AI', result['detail'])
        other = '12345678-1234-4234-8234-123456789abe'
        self.assertEqual(self.call('/v1/jobs', {'id': other, 'prompt': 'Inny obiekt', 'sourceJobId': JOB})[0], 409)
        self.assertEqual(self.call('/v1/jobs', {'id': other, 'prompt': 'Dab z lampkami', 'sourceJobId': '../../secret'})[0], 400)

    def test_ai_configuration_requires_the_worker_credential_and_rejects_busy_jobs(self):
        key = 'sk-fixture-' + 'a' * 30
        with patch.object(server.openai_provider, 'verify_key', return_value=key) as verify:
            self.assertEqual(self.call('/v1/ai', {'provider': 'openai', 'apiKey': key}, token='invalid')[0], 401)
            verify.assert_not_called()
            status, data = self.call('/v1/ai', {'provider': 'openai', 'apiKey': key})
            self.assertEqual(status, 200)
            self.assertEqual(data, {'saved': True})
            self.assertNotIn(key, json.dumps(data))
        self.call('/v1/jobs', {'id': JOB, 'prompt': 'Dab'})
        self.assertEqual(self.call('/v1/ai', {'provider': 'ollama'})[0], 409)

    def test_saved_scene_replay_preserves_photos_is_idempotent_and_never_calls_ai(self):
        scene = (Path(__file__).parent / 'examples/textures-eight.scene.json').read_text()
        folder = server.JOBS / JOB
        folder.mkdir(); (folder / 'scene.json').write_text(scene)
        image = bytes([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
        photos = server.photo_input.validate_photos([{'name': 'front.jpg', 'view': 'front', 'dataUrl': 'data:image/jpeg;base64,' + base64.b64encode(image).decode()}])
        (folder / 'reference-0.jpg').write_bytes(image)
        server.write_json(folder / 'reference-photos.json', server.photo_input.metadata(photos))
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)', (JOB, 'Model ze zdjecia', 'failed', 'Use at most 8 materials and 8 images.'))
        rebuilt = '12345678-1234-4234-8234-123456789abd'
        request = {'id': rebuilt, 'prompt': 'Model ze zdjecia', 'sourceJobId': JOB}
        server.health.return_value = {'ready': False, 'provider': 'ollama', 'photoInput': False}
        self.assertEqual(self.call('/v1/jobs', {**request, 'photos': []})[0], 400)
        self.assertEqual(self.call('/v1/jobs', {**request, 'prompt': 'Other model'})[0], 409)
        self.assertEqual(self.call('/v1/jobs', request)[0], 202)
        self.assertEqual(self.call('/v1/jobs', request)[0], 200)
        self.assertEqual(self.call('/v1/jobs', {'id': rebuilt, 'prompt': request['prompt']})[0], 409)
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'), patch.object(server, 'ai_settings') as settings, patch.object(server, 'generate_code') as ai, patch.object(server, 'run_blender') as blender:
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()
            settings.assert_not_called(); ai.assert_not_called(); blender.assert_called_once()
        self.assertEqual(self.call('/v1/jobs/' + rebuilt)[1]['state'], 'succeeded')
        self.assertEqual((folder / 'scene.json').read_text(), scene)
        self.assertEqual((server.JOBS / rebuilt / 'reference-0.jpg').read_bytes(), image)
        self.assertEqual(json.loads((server.JOBS / rebuilt / 'timing.json').read_text())['ai_seconds'], 0)

    def test_identical_retry_after_oidn_error_reuses_scene_without_ai(self):
        scene=(Path(__file__).parent/'examples/textures-eight.scene.json').read_text()
        folder=server.JOBS/JOB;folder.mkdir();(folder/'scene.json').write_text(scene)
        image=bytes([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
        raw={'name':'front.jpg','view':'front','dataUrl':'data:image/jpeg;base64,'+base64.b64encode(image).decode()}
        photos=server.photo_input.validate_photos([raw])
        (folder/'reference-0.jpg').write_bytes(image)
        server.write_json(folder/'reference-photos.json',server.photo_input.metadata(photos))
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',(JOB,'Model','failed',
                'Failed to denoise, build has no OpenImageDenoise support'))
            self.assertIsNone(server.recoverable_review_scene(db,'Different',[]))
            self.assertIsNone(server.recoverable_review_scene(db,'Model',[]))
            changed=server.photo_input.validate_photos([{**raw,'view':'back'}])
            self.assertIsNone(server.recoverable_review_scene(db,'Model',changed))
        rebuilt='12345678-1234-4234-8234-123456789abd'
        server.health.return_value={'ready':False,'photoInput':False,'provider':'ollama'}
        request={'id':rebuilt,'prompt':'Model','photos':[raw]}
        self.assertEqual(self.call('/v1/jobs',request)[0],202)
        self.assertEqual(self.call('/v1/jobs',request)[0],200)
        self.assertEqual((server.JOBS/rebuilt/'saved-scene.json').read_text(),scene)
        with patch.object(server,'WAKE') as wake,patch.object(server,'verify_runtime'), \
             patch.object(server,'ai_settings') as settings,patch.object(server,'generate_code') as ai, \
             patch.object(server,'run_blender') as blender:
            wake.wait.side_effect=[None,StopIteration]
            with self.assertRaises(StopIteration):server.worker()
            settings.assert_not_called();ai.assert_not_called();blender.assert_called_once()
        self.assertEqual(self.call('/v1/jobs/'+rebuilt)[1]['state'],'succeeded')
        self.assertEqual((server.JOBS/rebuilt/'reference-0.jpg').read_bytes(),image)
        self.assertTrue(json.loads((server.JOBS/rebuilt/'review-request.json').read_text())['enabled'])
        self.assertEqual(json.loads((server.JOBS/rebuilt/'timing.json').read_text())['ai_seconds'],0)

    def test_renderer_limit_does_not_buy_a_second_ai_plan(self):
        self.call('/v1/jobs', {'id': JOB, 'prompt': 'Eight fabrics'})
        scene = (Path(__file__).parent / 'examples/textures-eight.scene.json').read_text()
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'), patch.object(server, 'generate_code', return_value=scene) as ai, patch.object(server, 'run_blender', side_effect=ValueError('Export limit: 8 used materials and 16 used texture images.')):
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()
            ai.assert_called_once()
        self.assertEqual(self.call('/v1/jobs/' + JOB)[1]['state'], 'failed')
        self.assertTrue((server.JOBS / JOB / 'scene.json').is_file())

    def test_queue_idempotency_cancellation_and_no_phantom_artifact(self):
        data = {'id': JOB, 'prompt': 'Duży dąb z liśćmi'}
        self.assertEqual(self.call('/v1/jobs', data)[0], 202)
        self.assertEqual(self.call('/v1/jobs', data)[0], 200)
        self.assertEqual(self.call('/v1/jobs', {**data, 'prompt': 'smok'})[0], 409)
        other = {**data, 'id': JOB[:-1] + 'd'}
        self.assertEqual(self.call('/v1/jobs', other)[0], 409)
        self.assertEqual(self.call('/v1/jobs/' + JOB + '/model')[0], 409)
        self.assertEqual(self.call('/v1/jobs/' + JOB + '/cancel', {})[0], 200)
        server.status(JOB, 'succeeded', 'late completion')
        self.assertEqual(self.call('/v1/jobs/' + JOB)[1]['state'], 'cancelled')
        self.assertEqual(self.call('/v1/jobs', other)[0], 202)

    def test_photo_queue_persists_bytes_and_forwards_them_to_the_scene_planner(self):
        # Structural JPEG transport fixture; this does not claim visual fidelity.
        image = bytes([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
        photo = {'name': 'front.jpg', 'view': 'front', 'dataUrl': 'data:image/jpeg;base64,' + base64.b64encode(image).decode()}
        data = {'id': JOB, 'prompt': 'A rocket', 'photos': [photo]}
        self.assertEqual(self.call('/v1/jobs', data)[0], 409)
        server.health.return_value = {'ready': True, 'provider': 'openai', 'photoInput': True}
        self.assertEqual(self.call('/v1/jobs', data, token='invalid')[0], 401)
        self.assertEqual(self.call('/v1/jobs', data)[0], 202)
        self.assertEqual(self.call('/v1/jobs', data)[0], 200)
        self.assertEqual(self.call('/v1/jobs', {**data, 'photos': [{**photo, 'view': 'back'}]})[0], 409)
        folder = server.JOBS / JOB
        self.assertEqual((folder / 'reference-0.jpg').read_bytes(), image)
        self.assertEqual((folder / 'reference-0.jpg').stat().st_mode & 0o777, 0o600)
        self.assertNotIn('base64', (folder / 'reference-photos.json').read_text())
        # The mocked Blender finish normally writes the structural report.
        (folder / 'result.json').write_text('{}')
        scene = (Path(__file__).parent / 'examples/rocket.scene.json').read_text()
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime'), patch.object(server, 'ai_settings', return_value={'provider': 'openai'}), patch.object(server, 'generate_code', return_value=scene) as ai, patch.object(server, 'run_blender') as blender:
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()
            blender.assert_called_once()
            content = ai.call_args.args[0][1]['content']
            self.assertEqual([item['image_url'] for item in content if item['type'] == 'input_image'], [photo['dataUrl']])
        result = self.call('/v1/jobs/' + JOB)[1]
        self.assertEqual(result['state'], 'succeeded')
        self.assertIn('1 zdjec', result['detail'])

    def test_rejects_invalid_photos_before_creating_a_queue_entry(self):
        for value in [[{'name': 'a.jpg', 'view': 'front', 'dataUrl': 'https://example.test/a.jpg'}], [None] * 5, [{'name': 'x', 'view': 'front', 'dataUrl': 'data:image/jpeg;base64,YWJj'}]]:
            self.assertEqual(self.call('/v1/jobs', {'id': JOB, 'prompt': 'Model', 'photos': value})[0], 400)
        with server.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 0)

    def test_prompt_boundary_matches_editor_utf16_units(self):
        accepted={'id':JOB,'prompt':'x'*5000}
        self.assertEqual(self.call('/v1/jobs',accepted)[0],202)
        self.assertEqual(self.call('/v1/jobs/'+JOB+'/cancel',{})[0],200)
        for prompt in ('x'*5001,'😀'*2501):
            status,_=self.call('/v1/jobs',{'id':JOB[:-1]+'d','prompt':prompt})
            self.assertEqual(status,400)

if __name__ == '__main__':
    unittest.main()
