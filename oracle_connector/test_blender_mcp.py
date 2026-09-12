"""MCP/runner control-plane tests use fixtures; they do not evaluate AI likeness."""
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from blender_mcp import JobTools, serve, write
from codex_runner import Gateway, command, safe_message
from codex_smoke import Fixture, result_verified

class McpWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        write(self.folder/'agent-request.json',{'prompt':'Rocket model','instructions':'Use blue fins'})
        self.scene=json.loads((Path(__file__).parent/'examples/rocket.scene.json').read_text())
        def build(folder):
            (folder/'model.glb').write_bytes(b'control-plane-fixture-not-a-real-model')
            write(folder/'result.json',{'triangles':100})
            (folder/'review').mkdir()
            for view in ('front','side','back','face','three-quarter'):
                (folder/'review'/(view+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n'+bytes(30))
        self.job=JobTools(self.folder,build=build,finalize=lambda _:None)
    def build(self):
        return self.job.call('build_model',{'scene_json':json.dumps(self.scene),'expected_revision':0})
    def test_real_dispatch_required_and_uninspected_model_cannot_be_accepted(self):
        with self.assertRaisesRegex(ValueError,'CONFLICT|Brak modelu'):
            self.job.call('finish_model',{'expected_revision':0,'accepted':True,'issues':[],'summary':'done'})
        self.build()
        with self.assertRaisesRegex(ValueError,'Akceptacja'):
            self.job.call('finish_model',{'expected_revision':1,'accepted':True,'issues':[],'summary':'done'})
        for view in ('front','side','back'):
            blocks=self.job.call('inspect_render',{'view':view,'expected_revision':1})
            self.assertEqual(blocks[1]['type'],'image')
        report=self.job.call('finish_model',{'expected_revision':1,'accepted':True,'issues':[],'summary':'Fixture verdict'})
        self.assertTrue(report['assessment_completed'])
        self.assertTrue((self.folder/'model.glb').is_file())
    def test_edits_invalidate_review_and_previous_revision_survives_failed_build(self):
        self.build()
        self.job.call('inspect_render',{'view':'front','expected_revision':1})
        before=(self.job.current/'model.glb').read_bytes()
        def fail(folder):raise ValueError('bad geometry')
        self.job.build_callback=fail
        with self.assertRaisesRegex(ValueError,'bad geometry'):
            self.job.call('edit_model',{'code':'x = 1','expected_revision':1})
        self.assertEqual(self.job.revision,1)
        self.assertEqual((self.job.current/'model.glb').read_bytes(),before)
        self.assertEqual(self.job.seen,{'front'})
        with self.assertRaisesRegex(ValueError,'CONFLICT'):
            self.job.call('edit_model',{'code':'x = 1','expected_revision':0})
    def test_mcp_cannot_run_file_network_or_host_code(self):
        self.build()
        for code in ('import os\nos.system("true")','open("/etc/passwd").read()','bpy.data.images.load("secret.png")'):
            with self.subTest(code=code),self.assertRaises(ValueError):
                self.job.call('edit_model',{'code':code,'expected_revision':1})
        self.assertEqual(self.job.attempts,1)
    def test_stdio_handshake_and_named_tool_invocation(self):
        stream=io.StringIO('\n'.join(json.dumps(v) for v in [
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26'}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_current_model','arguments':{}}}])+'\n')
        output=io.StringIO();serve(self.job,stream,output)
        responses=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([r['id'] for r in responses],[1,2,3])
        self.assertEqual(responses[0]['result']['serverInfo']['name'],'forge-blender')
        self.assertIn('edit_model',[t['name'] for t in responses[1]['result']['tools']])
        self.assertFalse(json.loads(responses[2]['result']['content'][0]['text'])['has_model'])

class GatewayTests(unittest.TestCase):
    def test_terminal_event_releases_request_slot_without_waiting_for_connection_close(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def __iter__(self):
                yield b'data: {"type":"response.completed","response":{"usage":{"input_tokens":10,"output_tokens":20}}}\n'
                raise AssertionError('Gateway waited after terminal event')
        class Opener:
            def open(self,*args,**kwargs):return Response()
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp,patch('codex_runner.urllib.request.build_opener',return_value=Opener()):
            with Gateway('fixture-key',Path(temp),threading.Event()) as gateway:
                for _ in range(2):
                    request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                        data=b'{"model":"gpt-6-astra","tools":[{"type":"custom","name":"exec"}]}',headers={'Authorization':'Bearer '+gateway.token})
                    with client.open(request,timeout=2) as response:
                        self.assertIn(b'response.completed',response.read())
                self.assertEqual(gateway.requests,2)
                self.assertEqual(gateway.output,40)
                self.assertFalse(gateway.unknown_usage)
    def test_private_key_stays_in_gateway_and_budget_stops_new_requests(self):
        captured=[]
        class Opener:
            def open(self,request,timeout):
                captured.append(request)
                return io.BytesIO(b'data: {"type":"response.completed","response":{"usage":{"input_tokens":100,"output_tokens":36000}}}\n\n')
        with tempfile.TemporaryDirectory() as temp, patch('codex_runner.urllib.request.build_opener',return_value=Opener()):
            with Gateway('sk-private-fixture',Path(temp),threading.Event()) as gateway:
                # urllib's default opener is independent of the patched trusted
                # upstream opener and communicates over the real loopback socket.
                client=urllib.request.OpenerDirector()
                client.add_handler(urllib.request.HTTPHandler())
                client.add_handler(urllib.request.HTTPDefaultErrorHandler())
                client.add_handler(urllib.request.HTTPErrorProcessor())
                url='http://127.0.0.1:%d/v1/responses'%gateway.server.server_port
                def request(token):
                    return client.open(urllib.request.Request(url,data=b'{"model":"gpt-6-astra","input":"test","tools":[{"type":"custom","name":"exec"}]}',headers={'Authorization':'Bearer '+token}),timeout=3)
                with self.assertRaises(urllib.error.HTTPError) as failure:request('wrong-token')
                self.assertEqual(failure.exception.code,403);self.assertFalse(captured)
                with request(gateway.token) as response:response.read()
                self.assertEqual(captured[0].get_header('Authorization'),'Bearer sk-private-fixture')
                self.assertNotIn('sk-private-fixture',json.dumps(command('/tmp/codex',Path(temp),1234)))
                with self.assertRaises(urllib.error.HTTPError) as failure:request(gateway.token)
                self.assertEqual(failure.exception.code,429);self.assertEqual(len(captured),1)
                self.assertEqual(json.loads(captured[0].data)['max_output_tokens'],16000)

class AstraCodeModeTests(unittest.TestCase):
    def test_empty_catalog_from_oracle_screenshot_cannot_spend_api_budget(self):
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp, patch('codex_runner.urllib.request.build_opener') as upstream:
            with Gateway('never-send-key',Path(temp),threading.Event()) as gateway:
                request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                    data=b'{"model":"gpt-6-astra","tools":[]}',headers={'Authorization':'Bearer '+gateway.token})
                with self.assertRaises(urllib.error.HTTPError) as caught: client.open(request,timeout=2)
                self.assertEqual(caught.exception.code,422)
                self.assertIn(b'CODEX_TOOLS_MISSING',caught.exception.read())
                self.assertEqual(gateway.requests,0); upstream.assert_not_called()
    def test_fixture_calls_advertised_code_mode_with_namespace(self):
        fixture=Fixture('nonce')
        request=urllib.request.Request('http://fixture',data=json.dumps({'tools':[{'type':'namespace','name':'functions','tools':[{'type':'custom','name':'exec'}]}]}).encode())
        events=[json.loads(line[6:]) for line in fixture.open(request,1).getvalue().decode().splitlines() if line.startswith('data: ')]
        call=events[1]['item']
        self.assertEqual((call['type'],call['name'],call['namespace']),('custom_tool_call','exec','functions'))
        self.assertIn('await tools[tool.name]',call['input'])
    def test_empty_direct_only_catalog_is_rejected_by_smoke(self):
        for tools in ([],[{'type':'function','name':'mcp__blender__get_current_model'}]):
            with self.subTest(tools=tools),self.assertRaisesRegex(ValueError,'CODEX_EXEC_MISSING'):
                Fixture('nonce').open(urllib.request.Request('http://fixture',data=json.dumps({'tools':tools}).encode()),1)
    def test_probe_requires_actual_matching_call_output_and_six_mcp_tools(self):
        result={'forge_probe':'nonce','tool_names':['mcp__blender__'+t for t in ('get_modeling_contract','build_model','edit_model','get_current_model','inspect_render','finish_model')],
                'result':{'content':[{'type':'text','text':json.dumps({'revision':0,'has_model':False})}]}}
        output={'type':'custom_tool_call_output','call_id':'call_fixture','output':json.dumps({'output':[{'type':'text','text':json.dumps(result)}]})}
        self.assertTrue(result_verified({'input':[output]},'nonce'))
        self.assertFalse(result_verified({'input':[output]},'wrong-nonce'))
        self.assertFalse(result_verified({'input':[{**output,'type':'custom_tool_call'}]},'nonce'))
        result['tool_names']=[]; output['output']=json.dumps(result)
        self.assertFalse(result_verified({'input':[output]},'nonce'))
        output['output']='Tool unavailable: revision=0, has_model=false'
        self.assertFalse(result_verified({'input':[output]},'nonce'))
    def test_diagnostics_redact_credentials(self):
        value=safe_message('Failure Bearer secret-value, sk-abc123 data:image/png;base64,AAAA',('secret-value',))
        for secret in ('secret-value','sk-abc123','AAAA'):self.assertNotIn(secret,value)
    def test_job_keeps_code_mode_but_has_no_host_shell_or_external_tools(self):
        args=command('/tmp/codex',Path('/tmp/job'),1234)
        disabled=[args[i+1] for i,x in enumerate(args[:-1]) if x=='--disable']
        self.assertNotIn('code_mode_host',disabled)
        self.assertIn('features.code_mode_only=true',args)
        self.assertIn('features.code_mode_host.enabled=true',args)
        for name in ('shell_tool','unified_exec','apps','plugins','multi_agent'):self.assertIn(name,disabled)

if __name__=='__main__':unittest.main()
