"""Control-plane regression tests; no paid API or Blender process required."""
import ast
import io
import json
from pathlib import Path
import tempfile
import unittest
from code_policy import prepare_code
from blender_mcp import JobTools, anatomy_build_error, serve, write


class ValidationPreflightTests(unittest.TestCase):
    def test_context_syntax_is_rejected_before_dispatch(self):
        for code in ('return 1', 'break', 'continue', 'yield 1'):
            with self.subTest(code=code):
                ast.parse(code)  # Reproduces the old validation gap.
                with self.assertRaises(SyntaxError):
                    prepare_code(code)

    def test_valid_nested_control_flow_still_works(self):
        code = 'def shape():\n    for x in range(3):\n        if x == 1: break\n    return x\nvalue = shape()'
        prepared, replaced = prepare_code(code)
        self.assertEqual(replaced, [])
        namespace = {}
        exec(compile(prepared, '<fixture>', 'exec'), namespace)
        self.assertEqual(namespace['value'], 1)

    def test_preflight_failure_preserves_attempt_revision_and_model(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            write(folder/'agent-request.json', {'prompt':'fixture','instructions':'fixture'})
            calls = []
            def build(candidate):
                calls.append(candidate)
                (candidate/'model.glb').write_bytes(b'control-plane-fixture')
                write(candidate/'result.json', {'triangles':12})
            job = JobTools(folder, build=build)
            job.build({'subject_type':'object','parts':[], 'materials':[], 'reference_views':[]})
            before = job.current
            job.seen = {'front'}
            for code in ('return 1', 'break', 'continue', 'yield 1', 'if :'):
                with self.subTest(code=code), self.assertRaises(SyntaxError):
                    job.call('edit_model', {'code':code,'expected_revision':1})
            self.assertEqual((job.attempts, job.revision), (1, 1))
            self.assertEqual(job.current, before)
            self.assertEqual(job.seen, {'front'})
            self.assertEqual(len(calls), 1)
            self.assertEqual((before/'model.glb').read_bytes(), b'control-plane-fixture')

    def test_stdio_syntax_retry_records_failure_without_extra_blender_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            write(folder/'agent-request.json', {'prompt':'fixture','instructions':'fixture'})
            def build(candidate):
                (candidate/'model.glb').write_bytes(b'fixture')
                write(candidate/'result.json', {'triangles':12})
            job = JobTools(folder, build=build)
            job.build({'subject_type':'object','parts':[], 'materials':[], 'reference_views':[]})
            requests = [
                {'jsonrpc':'2.0','id':i,'method':'tools/call','params':{
                    'name':'edit_model','arguments':{'code':code,'expected_revision':1}}}
                for i,code in [(1,'return 1'),(2,'value = 1')]]
            output = io.StringIO()
            serve(job, io.StringIO('\n'.join(map(json.dumps,requests))+'\n'), output)
            replies = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertTrue(replies[0]['result']['isError'])
            self.assertIn('SyntaxError', replies[0]['result']['content'][0]['text'])
            self.assertFalse(replies[1]['result']['isError'])
            trace = json.loads((folder/'agent-tools.json').read_text())
            self.assertEqual(trace['failures'], 1)
            self.assertEqual(trace['build_attempts'], 2)  # first model plus valid edit
            self.assertEqual(trace['revision'], 2)
            completed = [call for call in trace['calls'] if call['status'] != 'started']
            self.assertEqual([call['attempt'] for call in completed], [None, 2])
            self.assertEqual([call['build_attempts'] for call in completed], [1, 2])

    def test_failed_candidate_records_attempt_but_preserves_current_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            write(folder/'agent-request.json', {'prompt':'fixture','instructions':'fixture'})
            def build(candidate):
                (candidate/'model.glb').write_bytes(b'fixture')
                write(candidate/'result.json', {'triangles':12})
            job = JobTools(folder, build=build)
            job.build({'subject_type':'object','parts':[], 'materials':[], 'reference_views':[]})
            def fail(candidate): raise ValueError('skin_atlas fixture')
            job.build_callback = fail
            request = {'jsonrpc':'2.0','id':1,'method':'tools/call','params':{
                'name':'edit_model','arguments':{'code':'value = 1','expected_revision':1}}}
            serve(job, io.StringIO(json.dumps(request)+'\n'), io.StringIO())
            call = json.loads((folder/'agent-tools.json').read_text())['calls'][-1]
            self.assertEqual(call['attempt'], 2)
            self.assertEqual(call['revision'], 1)
            self.assertEqual(job.current.name, '1')

    def test_atlas_failure_keeps_material_evidence_with_matching_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            counts = {'heads':1,'eyes':2,'hands':2,'nails':10}
            zero = dict.fromkeys(counts, 0)
            report = {'structural_checks_passed':False, 'expected':counts, 'actual':counts,
                      'missing':zero, 'excess':zero, 'violations':[
                          {'code':'skin_atlas','object':'head','minimum_edge':2048,
                           'largest_image_edge':512,'observed_materials':'new_skin',
                           'observed_images':'new_skin-UV (512x512)',
                           'atlas_scope':'effective_head_materials_including_groups',
                           'message':'Head material has only 512px.'}],
                      'repair_hint':'Preserve existing head atlas and UV.'}
            write(folder/'anatomy-failure.json', report)
            error = anatomy_build_error(folder, ValueError('Blender failed'))
            detail = json.loads(str(error).split(': ', 1)[1])
            self.assertEqual(detail['expected'], detail['actual'])
            self.assertEqual(detail['violations'][0]['largest_image_edge'], 512)
            self.assertEqual(detail['violations'][0]['minimum_edge'], 2048)
            self.assertIn('new_skin', detail['violations'][0]['observed_materials'])


if __name__ == '__main__': unittest.main()
