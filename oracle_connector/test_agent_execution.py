import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from blender_mcp import write
from codex_runner import Gateway, code_errors
from paid_trial import prepare


class ExecutionDiagnosticsTests(unittest.TestCase):
    def test_errors_inside_realistic_code_mode_wrappers_are_retained_without_reasoning(self):
        value={'output':[{'type':'text','text':'Script failed\nUncaught ReferenceError: scene is not defined'},
                         {'type':'reasoning','text':'Error: private reasoning'},
                         {'type':'image','data':'Error: image bytes'}]}
        self.assertEqual(code_errors(json.dumps(value)),['ReferenceError: scene is not defined'])

    def test_execution_outputs_are_deduplicated_and_never_include_prompt_code_or_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);gateway=Gateway('sk-secretfixture',folder,threading.Event())
            try:
                output={'type':'custom_tool_call_output','call_id':'exec_1','output':{'content':[
                    {'type':'text','text':'Script failed\nTypeError: sk-secretfixture data:image/png;base64,AAAA'}]}}
                payload={'input':[{'type':'reasoning','text':'DO_NOT_SAVE'},
                       {'type':'custom_tool_call','input':'SECRET_CODE'},output]}
                gateway.observe_execution(payload);gateway.observe_execution(payload)
                saved=(folder/'agent-execution.json').read_text()
                self.assertEqual(len(json.loads(saved)['calls']),1)
                for text in ('sk-secretfixture','AAAA','DO_NOT_SAVE','SECRET_CODE'):self.assertNotIn(text,saved)
                self.assertIn('TypeError',saved)
                self.assertIn('Correct this exact error',gateway.execution_guidance())
                write(folder/'agent-candidate.json',{'revision':2})
                self.assertIn('current revision=2',gateway.execution_guidance())
            finally:gateway.server.server_close()

    def test_repeated_pre_mcp_code_failures_stop_without_upstream_request(self):
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp,patch('codex_runner.urllib.request.build_opener') as upstream:
            with Gateway('unused',Path(temp),threading.Event()) as gateway:
                payload={'model':'gpt-6-astra','tools':[{'type':'custom','name':'exec'}],'input':[
                    {'type':'custom_tool_call_output','call_id':str(i),'output':'Script error: ReferenceError: scene is not defined'} for i in range(3)]}
                request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                    data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+gateway.token})
                with self.assertRaises(urllib.error.HTTPError) as error:client.open(request,timeout=3)
                self.assertIn(b'FORGE_REPEATED_CODE_ERROR',error.exception.read())
                self.assertEqual(gateway.requests,0);upstream.assert_not_called()

    def test_owner_approved_budget_allows_the_thirteenth_request(self):
        captured=[]
        class Upstream:
            def open(self,request,timeout):
                captured.append(json.loads(request.data))
                return io.BytesIO(b'data: {"type":"response.completed","response":{"usage":{"input_tokens":100,"output_tokens":20}}}\n\n')
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory() as temp,patch('codex_runner.urllib.request.build_opener',return_value=Upstream()):
            with Gateway('unused',Path(temp),threading.Event()) as gateway:
                gateway.requests=12
                req=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                    data=json.dumps({'model':'gpt-6-astra','tools':[{'type':'custom','name':'exec'}],'input':[]}).encode(),
                    headers={'Authorization':'Bearer '+gateway.token})
                with client.open(req,timeout=3) as response:response.read()
                self.assertEqual(gateway.requests,13);self.assertEqual(len(captured),1)
                self.assertIn('has_model=false',captured[0]['input'][-1]['content'][0]['text'])


class PaidTrialPreparationTests(unittest.TestCase):
    def test_repeating_after_disconnect_preserves_one_job_id_and_original_brief(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source='cda58443-da3f-4010-96d7-88432fd3fb21'
            folder=root/'state/jobs'/source;folder.mkdir(parents=True)
            with sqlite3.connect(root/'state/jobs.sqlite') as db:
                db.execute('CREATE TABLE jobs(id TEXT,prompt TEXT,state TEXT)')
                db.execute('INSERT INTO jobs VALUES(?,?,?)',(source,'Original task','failed'))
            write(folder/'agent-instructions.json',{'text':'Original edited instructions'})
            with patch('paid_trial.read_photos',return_value=[{'name':'original.jpg','view':'front','bytes':b'reference bytes','textureMaxSize':4096}]):
                first=prepare(root,source);again=prepare(root,source)
            self.assertEqual(first,again);self.assertNotEqual(first['id'],source)
            self.assertEqual(first['prompt'],'Original task')
            self.assertEqual(first['agentInstructions'],'Original edited instructions')
            self.assertEqual(first['photos'][0]['textureMaxSize'],4096)
            self.assertEqual(first['photos'][0]['dataUrl'],'data:image/jpeg;base64,cmVmZXJlbmNlIGJ5dGVz')


if __name__=='__main__':unittest.main()
