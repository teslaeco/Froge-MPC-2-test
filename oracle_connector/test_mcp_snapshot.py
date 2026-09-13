"""Bounded MCP reads and actionable failed edits; renderer bytes are fixtures."""
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

from blender_mcp import JobTools, SNAPSHOT_MAX_BYTES, serve, write


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        write(self.folder/'agent-request.json', {'prompt':'A detailed object', 'instructions':'Preserve geometry'})
        self.scene = json.loads((Path(__file__).parent/'examples/rocket.scene.json').read_text())
        def renderer(folder):
            (folder/'model.glb').write_bytes(b'control-plane-fixture-not-a-real-model')
            write(folder/'result.json', {'triangles':100,'object_names':['hull','window']})
        self.job = JobTools(self.folder, build=renderer, finalize=lambda _:None)
        self.request_id = 0

    def invoke(self, name, arguments, error=False):
        self.request_id += 1
        request = {'jsonrpc':'2.0','id':self.request_id,'method':'tools/call',
                   'params':{'name':name,'arguments':arguments}}
        output = io.StringIO()
        serve(self.job, io.StringIO(json.dumps(request)+'\n'), output)
        response = json.loads(output.getvalue())
        self.assertEqual(response['id'], self.request_id)
        self.assertEqual(response['result']['isError'], error, response)
        # This is the exact serialized MCP envelope, not a raw-string estimate.
        if not error and name in ('build_model','edit_model','get_current_model','finish_model'):
            self.assertLessEqual(len(json.dumps(response['result']).encode('utf-8')), SNAPSHOT_MAX_BYTES)
        text = response['result']['content'][0]['text']
        return text if error else json.loads(text)

    def build(self):
        return self.invoke('build_model', {'scene_json':json.dumps(self.scene),'expected_revision':0})

    def read_section(self, section, limit=16000):
        snapshot = self.invoke('get_current_model', {})
        descriptor = snapshot['sections'][section]
        offset = 0; chunks = []; pages = []
        while True:
            page = self.invoke('get_current_model', {'section':section,'offset':offset,'limit':limit,
                'expected_revision':snapshot['revision'],'expected_sha256':descriptor['sha256']})
            self.assertEqual(page['offset_unit'], 'unicode_code_points')
            self.assertEqual(page['offset'], offset)
            self.assertEqual(page['sha256'], descriptor['sha256'])
            chunks.append(page['text']); pages.append(page)
            if page['next_offset'] is None:
                self.assertTrue(page['complete'])
                break
            self.assertFalse(page['complete'])
            self.assertGreater(page['next_offset'], offset)
            self.assertEqual(page['next_offset'], offset+len(page['text']))
            offset = page['next_offset']
        text = ''.join(chunks)
        self.assertEqual(len(text), descriptor['characters'])
        self.assertEqual(len(text.encode('utf-8')), descriptor['bytes'])
        self.assertEqual(hashlib.sha256(text.encode('utf-8')).hexdigest(), descriptor['sha256'])
        return text, pages

    def test_small_scene_keeps_existing_fields_and_empty_snapshot_stays_compatible(self):
        empty = self.invoke('get_current_model', {})
        self.assertFalse(empty['has_model']); self.assertEqual(empty['revision'], 0)
        built = self.build()
        current = self.invoke('get_current_model', {'expected_revision':1})
        self.assertEqual(current, built)
        self.assertTrue(current['has_model'])
        self.assertEqual(current['scene']['parts'], self.scene['parts'])
        self.assertEqual(current['edits'], '')
        self.assertEqual(current['report']['object_names'], ['hull','window'])
        self.assertTrue(all(info['inline'] for info in current['sections'].values()))

    def test_near_maximum_scene_build_is_bounded_and_pages_restore_exact_json(self):
        rng = random.Random(17)
        vertices = [[rng.uniform(-1,1) for _ in range(3)] for _ in range(3920)]
        self.scene['parts'] = [{'kind':'mesh','name':'detail','material':'ceramic',
                                'vertices':vertices,'faces':[[0,1,2]]}]
        scene_text = json.dumps(self.scene)
        self.assertGreater(len(scene_text), 240000)
        self.assertLess(len(scene_text), 256000)
        snapshot = self.build()
        self.assertIsNone(snapshot['scene']); self.assertFalse(snapshot['sections']['scene']['inline'])
        restored, pages = self.read_section('scene')
        self.assertGreater(len(pages), 20)
        self.assertEqual(restored, (self.job.current/'scene.json').read_text(encoding='utf-8'))
        self.assertEqual(json.loads(restored)['parts'][0]['vertices'], vertices)

    def test_accumulated_edits_are_lossless_and_edit_results_are_bounded(self):
        self.build()
        code = '# '+('ż😀\\"'*1500)+'\nx = 1'
        for revision in (1,2,3):
            snapshot = self.invoke('edit_model', {'code':code,'expected_revision':revision})
            self.assertEqual(snapshot['revision'], revision+1)
        self.assertFalse(snapshot['sections']['edits']['inline']); self.assertIsNone(snapshot['edits'])
        restored, pages = self.read_section('edits')
        self.assertGreater(len(pages), 3)
        self.assertEqual(restored, (self.job.current/'edits.py').read_text(encoding='utf-8'))
        self.assertEqual(restored.count('x = 1'), 3)

    def test_unicode_object_names_and_report_arrays_cannot_overflow_snapshot_or_pages(self):
        self.build()
        report = {'triangles':100,'object_names':[str(i)+'😀"\\'*32 for i in range(256)],
                  'warnings':['Zażółć\n"😀\\'*100 for _ in range(50)]}
        write(self.job.current/'result.json', report)
        snapshot = self.invoke('get_current_model', {})
        self.assertIsNone(snapshot['report']); self.assertFalse(snapshot['sections']['report']['inline'])
        restored, pages = self.read_section('report')
        self.assertGreater(len(pages), 10)
        self.assertEqual(json.loads(restored), report)
        self.assertTrue(any(len(page['text'].encode('utf-8')) > len(page['text']) for page in pages))

    def test_finished_visual_review_is_paginated_without_dropping_issues(self):
        self.build()
        verdict = {'expected_revision':1,'accepted':False,
                   'issues':['😀'*400 for _ in range(12)],'summary':'ż'*1200}
        response = self.invoke('finish_model', verdict)
        self.assertFalse(response['accepted']); self.assertEqual(response['issues_count'], 12)
        self.assertFalse(response['sections']['visual_review']['inline'])
        self.assertEqual(self.invoke('finish_model', verdict), response)
        snapshot = self.invoke('get_current_model', {})
        self.assertTrue(snapshot['finished']); self.assertEqual(snapshot['builds_remaining'], 0)
        self.assertIsNone(snapshot['visual_review'])
        restored, pages = self.read_section('visual_review')
        self.assertGreater(len(pages), 3)
        self.assertEqual(json.loads(restored)['issues'], verdict['issues'])
        self.assertEqual(json.loads(restored)['summary'], verdict['summary'])

    def test_page_revision_and_digest_prevent_mixing_changed_sections(self):
        self.build()
        snapshot = self.invoke('get_current_model', {})
        args = {'section':'report','offset':1,'expected_revision':1,
                'expected_sha256':snapshot['sections']['report']['sha256']}
        write(self.job.current/'result.json', {'triangles':101})
        error = self.invoke('get_current_model', args, error=True)
        self.assertIn('CONFLICT', error)
        args.pop('expected_sha256'); args['expected_revision'] = 0
        self.assertIn('CONFLICT', self.invoke('get_current_model', args, error=True))

    def test_invalid_page_arguments_fail_explicitly_and_next_valid_read_succeeds(self):
        self.build()
        for args in ({'section':'other'}, {'section':'scene','offset':-1},
                     {'section':'scene','limit':0}, {'section':'scene','limit':16001},
                     {'section':'scene','offset':1}, {'section':'scene','offset':999999,'expected_revision':1},
                     {'section':'scene','expected_sha256':'broken'}, {'offset':1}, {'unexpected':True}):
            with self.subTest(args=args):
                self.invoke('get_current_model', args, error=True)
        self.assertTrue(self.invoke('get_current_model', {})['has_model'])
        self.assertEqual(self.job.attempts, 1)

    def test_failed_anatomy_edit_returns_counts_and_keeps_previous_candidate(self):
        self.build(); previous = self.job.current
        roles = ('heads','eyes','hands','nails')
        diagnostic = {'structural_checks_passed':False,
            'expected':dict(zip(roles,(1,2,2,10))), 'actual':dict(zip(roles,(1,1,2,8))),
            'missing':dict(zip(roles,(0,1,0,2))), 'excess':dict.fromkeys(roles,0),
            'objects':{role:['😀'*80 for _ in range(64)] for role in roles},
            'removed_or_untagged':{'eyes':['missing_eye'], 'nails':['missing_nail']},
            'violations':[{'code':'component_missing','component':'eyes','message':'Missing eye'} for _ in range(256)],
            'repair_hint':'Restore removed anatomical objects before checking the next render.'}
        def fail(folder):
            write(folder/'anatomy-failure.json', diagnostic)
            raise RuntimeError('Blender failed: ValueError: generic anatomy failure')
        self.job.build_callback = fail
        error = self.invoke('edit_model', {'code':'x = 1','expected_revision':1}, error=True)
        self.assertTrue(error.startswith('ANATOMY_VALIDATION: '))
        detail = json.loads(error.split(': ',1)[1])
        self.assertEqual(detail['missing'], diagnostic['missing'])
        self.assertEqual(detail['actual'], diagnostic['actual'])
        self.assertGreater(detail['omitted']['objects']['heads'], 0)
        self.assertGreater(detail['omitted']['violations'], 0)
        self.assertLess(len(json.dumps({'content':[{'type':'text','text':error}],'isError':True}).encode('utf-8')), 8000)
        self.assertEqual(self.job.current, previous); self.assertEqual(self.job.revision, 1)
        self.assertTrue((previous/'model.glb').is_file())
        self.assertTrue((self.folder/'candidates'/'2'/'anatomy-failure.json').is_file())

    def test_invalid_anatomy_diagnostic_does_not_hide_original_error(self):
        self.build()
        def fail(folder):
            write(folder/'anatomy-failure.json', {'structural_checks_passed':False,'expected':{'heads':'wrong'}})
            raise RuntimeError('ValueError: real original cause')
        self.job.build_callback = fail
        error = self.invoke('edit_model', {'code':'x = 1','expected_revision':1}, error=True)
        self.assertEqual(error, 'ValueError: real original cause')


if __name__ == '__main__':
    unittest.main()
