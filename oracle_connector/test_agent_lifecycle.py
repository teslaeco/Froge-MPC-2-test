"""Lifecycle/integrity regressions. Fixture geometry; no paid AI or likeness test."""
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from blender_mcp import JobTools, completed_outcome, current_candidate, serve, tool_error, write
from codex_runner import Gateway, run
from image3d_fixture import make_fixture
from runtime.model_checkpoint import save_ready


ROOT=Path(__file__).resolve().parent


def fixture_build(folder):
    (folder/'model.glb').write_bytes(make_fixture())
    report={'triangles':12,'master_export':{'formats':['glb']}}
    write(folder/'result.json',report)
    save_ready(folder,report,'core_export')
    (folder/'review').mkdir()
    for view in ('front','side','back','face','three-quarter'):
        (folder/'review'/(view+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n'+bytes(30))


def fixture_finalize(folder):
    report=json.loads((folder/'result.json').read_text())
    save_ready(folder,report,'interchange_exports')


def finish_fixture(folder):
    job=JobTools(folder,build=fixture_build,finalize=fixture_finalize)
    scene=json.loads((ROOT/'examples/rocket.scene.json').read_text())
    job.call('build_model',{'scene_json':json.dumps(scene),'expected_revision':0})
    for view in ('front','side','back'):
        job.call('inspect_render',{'view':view,'expected_revision':1})
    job.call('finish_model',{'expected_revision':1,'accepted':True,'issues':[],'summary':'Fixture only'})
    return job


class FinalizedModelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        write(self.folder/'agent-request.json',{'prompt':'Rocket model','instructions':'Blue fins'})

    def test_finish_allows_read_tools_and_same_finish_does_not_export_twice(self):
        job=finish_fixture(self.folder)
        job.finalize_callback=lambda _:self.fail('Final exports repeated')
        requests=[{'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':name,'arguments':args}}
                  for i,(name,args) in enumerate([
                      ('get_current_model',{}),('get_modeling_contract',{}),
                      ('inspect_render',{'view':'front','expected_revision':1}),
                      ('finish_model',{'expected_revision':1,'accepted':True,'issues':[],'summary':'Fixture only'})],1)]
        output=io.StringIO();serve(job,io.StringIO('\n'.join(map(json.dumps,requests))+'\n'),output)
        responses=list(map(json.loads,output.getvalue().splitlines()))
        self.assertEqual([value['id'] for value in responses],[1,2,3,4])
        self.assertTrue(all(value['result']['isError'] is False for value in responses))
        snapshot=json.loads(responses[0]['result']['content'][0]['text'])
        self.assertTrue(snapshot['finished']);self.assertEqual(snapshot['builds_remaining'],0)
        self.assertTrue(completed_outcome(self.folder)['accepted'])
        job.started-=2000
        self.assertTrue(job.call('get_current_model',{})['finished'])
        with self.assertRaisesRegex(ValueError,'nowego zlecenia'):
            job.call('edit_model',{'expected_revision':1,'code':'x = 1'})
        with self.assertRaisesRegex(ValueError,'nowego zlecenia'):
            job.call('finish_model',{'expected_revision':1,'accepted':False,'issues':['Changed verdict'],'summary':'Changed'})

    def test_stale_revision_different_execution_or_changed_model_cannot_finish(self):
        finish_fixture(self.folder)
        outcome_path=self.folder/'agent-outcome.json'
        outcome=json.loads(outcome_path.read_text())
        for bad in ({**outcome,'revision':2},{**outcome,'execution_id':'previous-run'},
                    {**outcome,'model_sha256':'old-model'}):
            with self.subTest(bad=bad):
                write(outcome_path,bad);self.assertIsNone(completed_outcome(self.folder))
        write(outcome_path,outcome)
        model=self.folder/'model.glb';data=model.read_bytes()
        model.write_bytes(data[:-1]+bytes([data[-1]^1]))
        self.assertIsNone(completed_outcome(self.folder))
        model.write_bytes(data)
        self.assertIsNotNone(completed_outcome(self.folder))
        request=json.loads((self.folder/'agent-request.json').read_text());request['execution_id']='new-run'
        write(self.folder/'agent-request.json',request)
        self.assertIsNone(completed_outcome(self.folder));self.assertIsNone(current_candidate(self.folder))

    def test_partial_or_unverified_artifact_is_not_a_completed_model(self):
        job=finish_fixture(self.folder)
        checkpoint=job.current/'model-ready.json'
        ready=checkpoint.read_bytes();checkpoint.unlink()
        self.assertIsNone(completed_outcome(self.folder));self.assertIsNone(current_candidate(self.folder))
        checkpoint.write_bytes(ready)
        (job.current/'model.glb').write_bytes(b'glTF')
        self.assertIsNone(completed_outcome(self.folder));self.assertIsNone(current_candidate(self.folder))

    def test_model_status_requires_terminal_state_and_matching_accepted_glb(self):
        from quality_report import model_status
        finish_fixture(self.folder)
        self.assertEqual(model_status(self.folder,'building'),{'modelStatus':'none'})
        expected=completed_outcome(self.folder)['model_sha256']
        self.assertEqual(model_status(self.folder,'succeeded'),{'modelStatus':'reviewed','modelSha256':expected})
        model=self.folder/'model.glb';data=model.read_bytes()
        model.write_bytes(data[:-1]+bytes([data[-1]^1]))
        self.assertEqual(model_status(self.folder,'succeeded'),{'modelStatus':'draft'})

    def test_no_new_provider_request_after_verified_finish_even_at_budget(self):
        finish_fixture(self.folder)
        client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with patch('codex_runner.urllib.request.build_opener') as upstream:
            with Gateway('unused-secret',self.folder,threading.Event()) as gateway:
                gateway.requests=32
                request=urllib.request.Request('http://127.0.0.1:%d/v1/responses'%gateway.server.server_port,
                    data=b'{"model":"gpt-6-astra","tools":[{"type":"custom","name":"exec"}]}',
                    headers={'Authorization':'Bearer '+gateway.token})
                with self.assertRaises(urllib.error.HTTPError) as caught:client.open(request,timeout=2)
                self.assertIn(b'FORGE_JOB_FINISHED',caught.exception.read())
                self.assertTrue(gateway.completed);self.assertIsNone(gateway.error)
                upstream.assert_not_called();self.assertEqual(gateway.requests,32)

    def test_runner_stops_lingering_process_after_real_finish_receipt(self):
        script=('import sys,time; from pathlib import Path; sys.path.insert(0,'+repr(str(ROOT))+'); '
                'from test_agent_lifecycle import finish_fixture; sys.stdin.read(); '
                'finish_fixture(Path('+repr(str(self.folder))+')); '
                'print(\'{"type":"error","message":"Trailing CLI failure after saved finish"}\',flush=True); '
                'time.sleep(60)')
        started=time.monotonic()
        with patch('codex_runner.command',return_value=[sys.executable,'-c',script]), \
                patch('codex_runner.urllib.request.build_opener') as upstream:
            result=run(self.folder,'Rocket model','Blue fins','unused-secret',threading.Event(),lambda _:None,binary=sys.executable)
        self.assertTrue(result['finished']);self.assertTrue(result['accepted'])
        self.assertLess(time.monotonic()-started,10)
        self.assertFalse((self.folder/'agent-cancelled').exists())
        self.assertTrue(json.loads((self.folder/'agent-usage.json').read_text())['completed'])
        upstream.assert_not_called()

    def test_runner_never_returns_previous_finished_model_for_new_execution(self):
        finish_fixture(self.folder)
        script='import sys;sys.stdin.read()'
        with patch('codex_runner.command',return_value=[sys.executable,'-c',script]), \
                patch('codex_runner.urllib.request.build_opener') as upstream:
            with self.assertRaisesRegex(RuntimeError,'aktualnego uruchomienia'):
                run(self.folder,'Different model','Different photo','unused-secret',threading.Event(),lambda _:None,binary=sys.executable)
        upstream.assert_not_called()

    def test_progress_puts_actual_exception_before_long_traceback_and_redacts_it(self):
        job=JobTools(self.folder,build=fixture_build)
        error=ValueError('Blender failed:\nTraceback (most recent call last):\n'+
                        '  File "/work/edits.py", line 13, in <module>\n'*35+
                        "TypeError: ellipsoid() got an unexpected keyword argument 'radius'\nBlender quit\n")
        job.record('edit_model','failed',error)
        message=json.loads((self.folder/'agent-progress.json').read_text())['detail']
        self.assertIn("TypeError: ellipsoid() got an unexpected keyword argument 'radius'",message)
        self.assertNotIn('Traceback',message)
        self.assertNotIn('sk-secret',tool_error(TypeError('sk-secret')))

    def test_invalid_python_edit_returns_corrective_error_without_killing_mcp(self):
        job=JobTools(self.folder,build=fixture_build)
        scene=json.loads((ROOT/'examples/rocket.scene.json').read_text())
        job.call('build_model',{'scene_json':json.dumps(scene),'expected_revision':0})
        requests=[{'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'edit_model',
                   'arguments':{'code':'x = (','expected_revision':1}}},
                  {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'get_current_model','arguments':{}}}]
        output=io.StringIO();serve(job,io.StringIO('\n'.join(map(json.dumps,requests))+'\n'),output)
        responses=list(map(json.loads,output.getvalue().splitlines()))
        self.assertTrue(responses[0]['result']['isError'])
        self.assertIn('SyntaxError',responses[0]['result']['content'][0]['text'])
        self.assertFalse(responses[1]['result']['isError'])
        self.assertEqual(job.attempts,1)


if __name__=='__main__':unittest.main()
