"""Release identity, real worker response and packaged-source regressions.

Packaging uses tiny synthetic asset fixtures only to exercise the archive path;
CI separately verifies the checked-in production assets and real Blender.
"""
import ast
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import apply_update
import codex_runner
import server
from test_agent_lifecycle import fixture_build, fixture_finalize
import test_worker_handoff as worker_fixture
JOB = worker_fixture.JOB
ROOT = Path(__file__).resolve().parent
from blender_mcp import JobTools, completed_outcome
from runtime.model_checkpoint import save_ready


def assigned_literal(source, name):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('Missing release field: ' + name)


class ReleaseContractTests(unittest.TestCase):
    def test_running_health_reports_the_installers_actual_release(self):
        with patch.object(server, 'ai_settings', return_value={'provider':'openai','api_key':'fixture'}), \
                patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')):
            health = server.health()
        self.assertEqual(health['connectorVersion'], 35)
        self.assertEqual(apply_update.EXPECTED_VERSION, 35)
        self.assertEqual(health['referenceAcceptanceRevision'], 1)
        self.assertEqual(health['workerRelease'], 'v35-reference-acceptance')

    def test_missing_capability_or_wrong_release_rolls_back(self):
        with patch.object(server, 'ai_settings', return_value={'provider':'openai','api_key':'fixture'}), \
                patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')):
            good = server.health()
        variants = [('missing_gate', {k:v for k,v in good.items() if k != 'referenceAcceptanceRevision'}),
                    ('wrong_release', {**good, 'workerRelease':'v34-reference-acceptance'}),
                    ('old_worker', {**good, 'connectorVersion':33})]
        for name, health in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); source = root/'incoming'; target = root/'installed'
                (target/'state').mkdir(parents=True); source.mkdir()
                for filename in apply_update.FILES:
                    path = source/filename; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'fixture = True\n' if filename.endswith('.py') else b'synthetic fixture asset')
                assets = ('anatomy.json.gz','male-skin.png','female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png')
                (source/'runtime/assets/manifest.json').write_text(json.dumps({n:hashlib.sha256((source/'runtime/assets'/n).read_bytes()).hexdigest() for n in assets}))
                (target/'server.py').write_text('previous = True\n')
                (target/'state/config.json').write_text('{"token":"fixture-only","client":"owner"}')
                original = (target/'state/config.json').read_bytes()
                with sqlite3.connect(target/'state/jobs.sqlite') as db:
                    db.execute('CREATE TABLE jobs(state TEXT)')
                with patch.object(apply_update, 'setup_runtime'), patch('install_codex.install'), \
                        patch.object(apply_update.subprocess, 'run'), patch.object(apply_update.time, 'sleep'), \
                        patch.object(apply_update.urllib.request, 'urlopen', side_effect=lambda *a, **kw: io.BytesIO(json.dumps(health).encode())):
                    with self.assertRaisesRegex(RuntimeError, 'nie potwierdzil'):
                        apply_update.update(source, target)
                self.assertEqual((target/'server.py').read_text(), 'previous = True\n')
                self.assertEqual((target/'state/config.json').read_bytes(), original)

    def test_archive_embeds_v35_sources_and_matching_payload(self):
        repo = ROOT.parent
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary); worker = project/'oracle_connector'; worker.mkdir()
            for name in (*apply_update.FILES, 'apply_update.py'):
                destination = worker/name; destination.parent.mkdir(parents=True, exist_ok=True)
                original = ROOT/name
                if original.is_file():
                    shutil.copyfile(original, destination)
                else:
                    self.assertIn(name, ['runtime/assets/'+n for n in ('male-skin.png','female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png')])
                    destination.write_bytes(b'synthetic package-only asset')
            manifest = json.loads((worker/'runtime/assets/manifest.json').read_text())
            manifest = {n:hashlib.sha256((worker/'runtime/assets'/n).read_bytes()).hexdigest() for n in manifest}
            (worker/'runtime/assets/manifest.json').write_text(json.dumps(manifest))
            for name in ('scripts/package-v35.py','scripts/cloud-shell-v35.template.py','docs/reviews/v35/POLECENIE-CODEX.txt'):
                destination = project/name; destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(repo/name, destination)
            subprocess.run([sys.executable, str(project/'scripts/package-v35.py')], check=True, capture_output=True)
            with zipfile.ZipFile(project/'public/downloads/froge-v35.zip') as archive:
                self.assertIsNone(archive.testzip())
                program = archive.read('froge-v35.py').decode()
            raw = gzip.decompress(base64.b64decode(assigned_literal(program, 'PAYLOAD_B64'), validate=True))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), assigned_literal(program, 'PAYLOAD_SHA256'))
            data = json.loads(raw)
            source = base64.b64decode(data['files']['server.py']).decode()
            updater = base64.b64decode(data['files']['apply_update.py']).decode()
            self.assertEqual(source, (ROOT/'server.py').read_text())
            self.assertEqual(updater, (ROOT/'apply_update.py').read_text())
            self.assertEqual(assigned_literal(source, 'CONNECTOR_VERSION'), 35)
            self.assertEqual(assigned_literal(updater, 'EXPECTED_VERSION'), 35)
            self.assertIn('referenceAcceptanceRevision', source)
            self.assertIn("workerRelease') == 'v35-reference-acceptance'", updater)
            self.assertIn('runtime/reference_reconstruction.py', data['files'])


class WorkerReleaseAcceptanceTests(unittest.TestCase):
    """Exercise the existing HTTP fixture queue with a real agent attestation."""

    setUp = worker_fixture.WorkerHandoffTests.setUp
    tearDown = worker_fixture.WorkerHandoffTests.tearDown
    call = worker_fixture.WorkerHandoffTests.call
    drain_one = worker_fixture.WorkerHandoffTests.drain_one

    def test_raw_agent_acceptance_cannot_make_worker_detail_claim_review_passed(self):
        def run_fixture(folder, prompt, instructions, key, cancelled, progress):
            server.write_json(folder/'agent-request.json', {'prompt':prompt,'instructions':instructions})
            def build(candidate):
                fixture_build(candidate)
                report = json.loads((candidate/'result.json').read_text())
                report['portrait_quality'] = {'structural_checks_passed':True, 'actual':{'heads':1,'eyes':2}}
                server.write_json(candidate/'result.json', report); save_ready(candidate, report, 'core_export')
                # Force photo-reference review without pretending these tiny
                # synthetic fixture renders are valid reference evidence.
                server.write_json(candidate/'reference-spec.json', {})
            job = JobTools(folder, build=build, finalize=fixture_finalize)
            scene = json.loads((ROOT/'examples/rocket.scene.json').read_text())
            job.call('build_model', {'scene_json':json.dumps(scene),'expected_revision':0})
            for view in ('front','side','back'):
                job.call('inspect_render', {'view':view,'expected_revision':1})
            job.call('finish_model', {'expected_revision':1,'accepted':True,'issues':[],'summary':'Synthetic regression fixture'})
            result = completed_outcome(folder)
            self.assertTrue(result['accepted'])
            return result
        with patch.object(codex_runner, 'executable', return_value=Path('/fixture/codex')), \
                patch.object(codex_runner, 'run', side_effect=run_fixture):
            self.assertEqual(self.call('/v1/jobs', {'id':JOB,'prompt':'Rakieta'})[0], 202)
            self.drain_one()
        result = self.call('/v1/jobs/'+JOB)[1]
        self.assertEqual(result['state'], 'succeeded', result['detail'])
        self.assertEqual(result['modelStatus'], 'draft')
        self.assertIn('Wynik roboczy', result['detail'])
        report = self.call('/v1/jobs/'+JOB+'/quality')[1]
        self.assertTrue(report['agent']['reportedAccepted'])
        self.assertFalse(report['agent']['accepted'])
        self.assertFalse(report['automaticQualityAccepted'])


if __name__ == '__main__':
    unittest.main()
