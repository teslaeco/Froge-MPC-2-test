"""Exercise real HTTP/curl delays; no actual AI quality or Blender rendering claims."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import unittest
import urllib.request

from ai_stream import stream_chat
from code_policy import CodePolicyError, StreamPolicyGuard


class DelayedOllama(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        self.server.payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        time.sleep(self.server.delay)
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson')
            self.end_headers()
            for delay, item in self.server.events:
                time.sleep(delay)
                self.wfile.write(json.dumps(item).encode() + b'\n')
                self.wfile.flush()
        except OSError:
            pass  # Expected when the client cancels or reaches its deadline.


class StreamTests(unittest.TestCase):
    def setUp(self):
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), DelayedOllama)
        self.http.delay = 0.2
        self.http.events = [(0, {'message': {'content': 'import math\n'}}),
                            (0.25, {'message': {'content': 'angle = math.pi\n'}}),
                            (0, {'done': True})]
        self.thread = threading.Thread(target=self.http.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:%d/api/chat' % self.http.server_port
        self.payload = {'model': 'fixture', 'messages': [{'role': 'user', 'content': 'Dąb'}]}

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()

    def test_silent_loading_and_mid_stream_wait_report_progress_and_finish(self):
        # Reproduce the old per-socket timeout using a scaled-down delay.
        request = urllib.request.Request(self.url, data=json.dumps(self.payload).encode())
        with self.assertRaises(TimeoutError):
            urllib.request.urlopen(request, timeout=0.05)
        reports = []
        text = stream_chat(self.url, self.payload, threading.Event(), lambda *args: reports.append(args), timeout=2, interval=0.03)
        self.assertEqual(text, 'import math\nangle = math.pi\n')
        self.assertTrue(any(count == 0 and elapsed >= 0.1 for count, elapsed, _ in reports))
        self.assertTrue(any(count > 0 and silent > 0.1 for count, _, silent in reports))
        self.assertEqual(self.http.payload, self.payload)

    def test_total_deadline_includes_wait_before_http_headers(self):
        self.http.delay = 0.7
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            stream_chat(self.url, self.payload, threading.Event(), lambda *_: None, timeout=0.15)
        self.assertLess(time.monotonic() - started, 0.6)

    def test_can_cancel_before_http_headers_without_waiting_for_socket_timeout(self):
        self.http.delay = 0.7
        cancelled = threading.Event()
        timer = threading.Timer(0.1, cancelled.set); timer.start()
        started = time.monotonic()
        try:
            with self.assertRaises(InterruptedError):
                stream_chat(self.url, self.payload, cancelled, lambda *_: None, timeout=3)
        finally:
            timer.cancel()
        self.assertLess(time.monotonic() - started, 0.6)

    def test_partial_code_without_done_is_never_a_success(self):
        self.http.delay = 0
        self.http.events = [(0, {'message': {'content': 'import math\n'}})]
        with self.assertRaisesRegex(ValueError, 'kompletnego skryptu'):
            stream_chat(self.url, self.payload, threading.Event(), lambda *_: None, timeout=2)

    def test_forbidden_load_stops_the_real_http_stream_before_the_rest_arrives(self):
        self.http.delay = 0
        self.http.events = [(0, {'message': {'content': 'bpy.data.images.load("missing.png")\n'}}),
                            (0.8, {'done': True})]
        started = time.monotonic()
        with self.assertRaises(CodePolicyError):
            stream_chat(self.url, self.payload, threading.Event(), lambda *_: None,
                        timeout=2, validate_chunk=StreamPolicyGuard().feed)
        self.assertLess(time.monotonic() - started, 0.5)

    def test_truncated_response_and_model_errors_are_explicit(self):
        self.http.delay = 0
        for record, message in [({'done': True, 'done_reason': 'length'}, 'uciety'),
                                ({'error': 'runner failed'}, 'runner failed')]:
            with self.subTest(record=record):
                self.http.events = [(0, record)]
                with self.assertRaisesRegex(ValueError, message):
                    stream_chat(self.url, self.payload, threading.Event(), lambda *_: None, timeout=2)


if __name__ == '__main__':
    unittest.main()
