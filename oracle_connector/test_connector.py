"""Contract tests use a real HTTP handler/SQLite; they do not simulate AI quality or a Blender render."""
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
from code_policy import extract_code, validate_code

JOB = '12345678-1234-4234-8234-123456789abc'

class CodePolicyTests(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
