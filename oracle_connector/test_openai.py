"""Real local SSE/curl transport and private configuration tests; no paid API calls."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error

from ai_stream import OpenAIServiceError, stream_chat
from code_policy import CodePolicyError, StreamPolicyGuard
import openai_provider
import server
import photo_input
from runtime.scene_contract import SCHEMA

FAKE_KEY = 'sk-local-fixture-' + 'x' * 30


class ResponseFixture(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        self.server.authorization = self.headers.get('Authorization')
        self.server.payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        try:
            time.sleep(self.server.delay)
            self.send_response(self.server.status)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for item in self.server.events:
                self.wfile.write(('event: %s\ndata: %s\n\n' % (item['type'], json.dumps(item))).encode())
                self.wfile.flush()
        except OSError:
            pass


class ResponsesTests(unittest.TestCase):
    def setUp(self):
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), ResponseFixture)
        self.http.delay, self.http.status = 0, 200
        self.http.events = [
            {'type': 'response.output_text.delta', 'delta': 'import math\n'},
            {'type': 'response.output_text.delta', 'delta': 'angle = math.pi\n'},
            {'type': 'response.completed', 'response': {'status': 'completed', 'usage': {'input_tokens': 11, 'output_tokens': 7, 'total_tokens': 18}}},
        ]
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:%d/v1/responses' % self.http.server_port

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()

    def call(self, cancel=None, **kwargs):
        return stream_chat(self.url, {'input': 'fixture'}, cancel or threading.Event(), lambda *_: None,
                           response_protocol='responses', api_key=FAKE_KEY, timeout=2, **kwargs)

    def test_streams_text_and_usage_without_putting_credentials_in_arguments_or_payload(self):
        import ai_stream
        original = ai_stream.subprocess.Popen
        commands, private_headers, usage = [], [], []
        def launch(command, **kwargs):
            commands.append(command)
            private_headers.extend(arg[1:] for arg in command if arg.startswith('@/'))
            return original(command, **kwargs)
        with patch.object(ai_stream.subprocess, 'Popen', side_effect=launch):
            result = self.call(usage_callback=usage.append)
        self.assertEqual(result, 'import math\nangle = math.pi\n')
        self.assertEqual(usage, [{'input_tokens': 11, 'output_tokens': 7, 'total_tokens': 18}])
        self.assertEqual(self.http.authorization, 'Bearer ' + FAKE_KEY)
        self.assertNotIn(FAKE_KEY, json.dumps(commands) + json.dumps(self.http.payload))
        self.assertTrue(private_headers)
        self.assertTrue(all(not Path(path).exists() for path in private_headers))

    def test_rejects_incomplete_refused_and_error_responses_without_echoing_secrets(self):
        cases = [({'type': 'response.incomplete'}, ValueError),
                 ({'type': 'response.refusal.delta', 'delta': 'no'}, OpenAIServiceError),
                 ({'type': 'error', 'error': {'code': 'invalid_api_key', 'message': FAKE_KEY}}, OpenAIServiceError)]
        for event, error_type in cases:
            with self.subTest(event=event):
                self.http.events = [self.http.events[0], event]
                with self.assertRaises(error_type) as failure:
                    self.call()
                self.assertNotIn(FAKE_KEY, str(failure.exception))
        self.http.events = [{'type': 'response.output_text.delta', 'delta': 'import math\n'}]
        with self.assertRaisesRegex(ValueError, 'kompletnego'):
            self.call()

    def test_http_quota_failure_and_cancellation_before_headers_are_explicit(self):
        self.http.status, self.http.events = 429, []
        with self.assertRaisesRegex(OpenAIServiceError, 'limit zapytan'):
            self.call()
        self.http.status, self.http.delay = 200, .7
        cancelled = threading.Event()
        timer = threading.Timer(.1, cancelled.set); timer.start()
        started = time.monotonic()
        try:
            with self.assertRaises(InterruptedError):
                self.call(cancelled)
        finally:
            timer.cancel()
        self.assertLess(time.monotonic() - started, .6)

    def test_openai_code_still_passes_the_early_policy_guard(self):
        self.http.events = [{'type': 'response.output_text.delta', 'delta': 'bpy.data.images.load("missing.png")\n'}]
        with self.assertRaises(CodePolicyError):
            self.call(validate_chunk=StreamPolicyGuard().feed)

    def test_astra_payload_uses_fixed_official_origin_low_reasoning_and_output_limit(self):
        with patch.object(openai_provider, 'stream_chat', return_value='code') as stream:
            openai_provider.generate([{'role': 'user', 'content': 'Dab'}], FAKE_KEY, threading.Event(), lambda *_: None, 120, None, lambda *_: None, schema=SCHEMA)
        args, kwargs = stream.call_args
        self.assertEqual(args[0], 'https://api.openai.com/v1/responses')
        self.assertEqual(args[1]['model'], 'gpt-6-astra')
        self.assertEqual(args[1]['reasoning'], {'effort': 'low'})
        self.assertEqual(args[1]['max_output_tokens'], 9000)
        self.assertFalse(args[1]['store'])
        self.assertEqual(args[1]['text']['format'], {'type':'json_schema','name':'froge_scene','strict':True,'schema':SCHEMA})
        self.assertNotIn(FAKE_KEY, json.dumps(args[1]))
        self.assertEqual(kwargs['api_key'], FAKE_KEY)

    def test_image_content_survives_the_real_responses_transport(self):
        image_url = 'data:image/jpeg;base64,transportfixture'
        messages = [{'role': 'user', 'content': photo_input.user_content('Model this object', [{'view': 'front', 'dataUrl': image_url}])}]
        with patch.object(openai_provider,'stream_chat',return_value='{}') as request:
            openai_provider.generate(messages,FAKE_KEY,threading.Event(),lambda *_:None,600,None,lambda *_:None,schema=SCHEMA)
        self.assertEqual(request.call_args.args[1]['reasoning'],{'effort':'max'})
        # Preserve provider payload creation, redirect only the network target to the local fixture.
        def local_transport(_url, *args, **kwargs):
            return stream_chat(self.url, *args, **kwargs)
        with patch.object(openai_provider, 'stream_chat', side_effect=local_transport):
            openai_provider.generate(messages, FAKE_KEY, threading.Event(), lambda *_: None, 2, None, lambda *_: None, schema=SCHEMA)
        self.assertEqual(self.http.payload['input'], messages)
        self.assertEqual(self.http.payload['input'][0]['content'][-1], {'type': 'input_image', 'image_url': image_url, 'detail': 'high'})
        self.assertNotIn(FAKE_KEY, json.dumps(self.http.payload))


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = patch.multiple(server, STATE=root / 'state', JOBS=root / 'state/jobs', CONFIG=root / 'state/config.json')
        self.paths.start(); server.RUNNING.clear(); server.initialize()

    def tearDown(self):
        server.RUNNING.clear(); self.paths.stop(); self.temp.cleanup()

    def test_provider_switch_keeps_key_private_and_never_calls_local_ai_when_openai_selected(self):
        with patch.object(openai_provider, 'verify_key', return_value=FAKE_KEY):
            self.assertTrue(server.configure_ai({'provider': 'openai', 'apiKey': FAKE_KEY}))
        path = server.STATE / 'ai-provider.json'
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with patch.object(server, 'ollama_json', side_effect=AssertionError('Local model must not be called')):
            state = server.health()
            self.assertEqual(state['provider'], 'openai')
            self.assertNotIn(FAKE_KEY, json.dumps(state))
            with patch.object(openai_provider, 'generate', return_value='import math') as generate:
                self.assertEqual(server.generate_code([], 'fixture', threading.Event()), 'import math')
                self.assertLessEqual(generate.call_args.args[4], 600)
        server.RUNNING.add('inflight')
        self.assertFalse(server.configure_ai({'provider': 'ollama'}))
        self.assertEqual(server.ai_settings()['provider'], 'openai')

    def test_key_validation_does_not_follow_redirects_or_echo_provider_errors(self):
        with patch.object(openai_provider.urllib.request, 'build_opener') as build:
            build.return_value.open.side_effect = urllib.error.HTTPError('https://api.openai.com/v1/models/gpt-6-astra', 401, FAKE_KEY, {}, io.BytesIO(FAKE_KEY.encode()))
            with self.assertRaises(OpenAIServiceError) as failure:
                openai_provider.verify_key(FAKE_KEY)
            self.assertNotIn(FAKE_KEY, str(failure.exception))
            self.assertTrue(any(isinstance(x, openai_provider.NoRedirect) for x in build.call_args.args))
        self.assertIsNone(openai_provider.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.test'))

    def test_container_failure_stops_the_job_before_any_ai_request(self):
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)', ('preflight-fixture', 'Dab z lampkami', 'queued', ''))
        with patch.object(server, 'WAKE') as wake, patch.object(server, 'verify_runtime', side_effect=RuntimeError('Blender unavailable')), patch.object(server, 'generate_code') as generate:
            wake.wait.side_effect = [None, StopIteration]
            with self.assertRaises(StopIteration):
                server.worker()
            generate.assert_not_called()
        with server.database() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?', ('preflight-fixture',)).fetchone()
        self.assertEqual(row['state'], 'failed')
        self.assertFalse(server.RUNNING)


if __name__ == '__main__':
    unittest.main()

