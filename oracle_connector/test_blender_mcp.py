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
from codex_runner import Gateway, command, safe_message, LITE_HEADER
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

    def test_invalid_frame_is_not_counted_as_visual_inspection(self):
        self.build()
        write(self.job.current/'review'/'render-settings.json',
              {'views_completed':[{'label':'face','framing_valid':False}]})
        with self.assertRaisesRegex(ValueError,'nieprawidlowy kadr'):
            self.job.call('inspect_render',{'view':'face','expected_revision':1})
        self.assertNotIn('face',self.job.seen)

    def test_hybrid_cannot_be_accepted_with_blocked_or_unchecked_socket(self):
        self.scene=json.loads((Path(__file__).parent/'examples/portrait-floor-components.scene.json').read_text())
        self.scene['parts'][0]['eye_states']={'left':'empty_socket','right':'present',
                                             'evidence':'The image shows an empty skull orbit on viewer right.'}
        self.build()
        for view in ('front','side','back','face'):
            self.job.call('inspect_render',{'view':view,'expected_revision':1})
        for clearance in ({},{'required':True,'passed':False}):
            write(self.job.current/'result.json',{'reference_socket_checks':clearance})
            with self.assertRaisesRegex(ValueError,'Pusty oczodol'):
                self.job.call('finish_model',{'expected_revision':1,'accepted':True,'issues':[],'summary':'done'})
        result=self.job.call('finish_model',{'expected_revision':1,'accepted':False,
                                            'issues':['Socket still needs sculpting.'],'summary':'Draft.'})
        self.assertFalse(result['accepted'])
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

    def test_invalid_arguments_return_tool_error_with_same_id_and_repair_is_possible(self):
        requests=[{'jsonrpc':'2.0','id':7,'method':'tools/call','params':{'name':'build_model','arguments':{'scene_json':'{}'}}},
                  {'jsonrpc':'2.0','id':8,'method':'tools/call','params':{'name':'build_model','arguments':{'scene_json':json.dumps(self.scene),'expected_revision':0}}}]
        output=io.StringIO();serve(self.job,io.StringIO('\n'.join(map(json.dumps,requests))+'\n'),output)
        responses=list(map(json.loads,output.getvalue().splitlines()))
        self.assertEqual(responses[0]['id'],7)
        self.assertTrue(responses[0]['result']['isError'])
        self.assertIn('expected_revision',responses[0]['result']['content'][0]['text'])
        self.assertFalse(responses[1]['result']['isError'])
        trace=json.loads((self.folder/'agent-tools.json').read_text())
        self.assertEqual(trace['failures'],1);self.assertEqual(trace['build_attempts'],1)
        self.assertNotIn('Rocket model',json.dumps(trace))

    def test_finish_empty_issues_validates_through_real_stdio_handler(self):
        self.build()
        for view in ('front','side','back'):self.job.call('inspect_render',{'view':view,'expected_revision':1})
        request={'jsonrpc':'2.0','id':42,'method':'tools/call','params':{'name':'finish_model','arguments':{
                 'expected_revision':1,'accepted':True,'issues':[],'summary':'Fixture verdict'}}}
        output=io.StringIO();serve(self.job,io.StringIO(json.dumps(request)+'\n'),output)
        response=json.loads(output.getvalue())
        self.assertEqual(response['id'],42);self.assertFalse(response['result']['isError'])
        self.assertTrue((self.folder/'agent-outcome.json').is_file())

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
                return io.BytesIO(b'data: {"type":"response.completed","response":{"usage":{"input_tokens":100,"output_tokens":96000}}}\n\n')
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
                self.assertEqual(failure.exception.code,422);self.assertEqual(len(captured),1)
                self.assertIn(b'FORGE_JOB_BUDGET',failure.exception.read())
                self.assertEqual(gateway.error_source,'forge')
                self.assertEqual(json.loads(captured[0].data)['max_output_tokens'],16000)

    def test_provider_quota_is_not_retried_or_replaced_by_local_budget(self):
        class Opener:
            calls=0
            def open(self,request,timeout):
                self.calls+=1
                raise urllib.error.HTTPError(request.full_url,429,'Too Many Requests',{'Retry-After':'30'},
                    io.BytesIO(b'{"error":{"code":"credit_balance_exhausted","message":"private provider detail"}}'))
        upstream=Opener();client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp,patch('codex_runner.urllib.request.build_opener',return_value=upstream):
            with Gateway('sk-fixture-private',Path(temp),threading.Event()) as gateway:
                for _ in range(3):
                    request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                        data=b'{"model":"gpt-6-astra","tools":[{"type":"custom","name":"exec"}]}',headers={'Authorization':'Bearer '+gateway.token})
                    with self.assertRaises(urllib.error.HTTPError) as caught:client.open(request,timeout=2)
                    self.assertEqual(caught.exception.code,422);caught.exception.close()
                self.assertEqual(upstream.calls,1);self.assertEqual(gateway.requests,1)
                receipt=json.loads((Path(temp)/'agent-usage.json').read_text())
                self.assertEqual(receipt['error_source'],'openai');self.assertEqual(receipt['upstream_status'],429)
                self.assertEqual(receipt['error_code'],'credit_balance_exhausted');self.assertEqual(receipt['retry_after'],'30')

    def test_repeated_identical_tool_errors_stop_before_another_paid_request(self):
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp,patch('codex_runner.urllib.request.build_opener') as upstream:
            folder=Path(temp)
            write(folder/'agent-tools.json',{'calls':[{'tool':'build_model','status':'failed','error':'invalid revision'}]*3})
            with Gateway('unused-fixture-key',folder,threading.Event()) as gateway:
                request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                    data=b'{"model":"gpt-6-astra","tools":[{"type":"custom","name":"exec"}]}',headers={'Authorization':'Bearer '+gateway.token})
                with self.assertRaises(urllib.error.HTTPError) as caught:client.open(request,timeout=2)
                self.assertIn(b'FORGE_REPEATED_TOOL_ERROR',caught.exception.read())
                self.assertEqual(gateway.requests,0);upstream.assert_not_called()

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
    def test_actual_astra_lite_request_preserves_tools_and_protocol_header(self):
        payload={'model':'gpt-6-astra','input':[{'type':'additional_tools','role':'developer','tools':[{'type':'namespace','name':'functions','tools':[{'type':'custom','name':'exec'}]}]}]}
        fixture=Fixture('nonce'); captured=[]
        class Opener:
            def open(self,request,timeout):
                captured.append(request)
                return fixture.open(request,timeout)
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp, patch('codex_runner.urllib.request.build_opener',return_value=Opener()):
            with Gateway('upstream-test-key',Path(temp),threading.Event()) as gateway:
                request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,data=json.dumps(payload).encode(),
                    headers={'Authorization':'Bearer '+gateway.token,LITE_HEADER:'true','X-Unrelated':'do-not-forward'})
                with client.open(request,timeout=2) as response:self.assertIn(b'custom_tool_call',response.read())
                headers={k.lower():v for k,v in captured[0].header_items()}
                self.assertEqual(headers[LITE_HEADER],'true');self.assertNotIn('x-unrelated',headers)
                self.assertNotIn('tools',json.loads(captured[0].data))
                self.assertEqual(json.loads(captured[0].data)['input'][:-1],payload['input'])
                self.assertIn('GPT-6 Astra',json.loads(captured[0].data)['input'][-1]['content'][0]['text'])
                self.assertEqual(gateway.requests,1)

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
