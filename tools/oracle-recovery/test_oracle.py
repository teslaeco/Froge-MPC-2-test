import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('forge_oracle', Path(__file__).with_name('forge-oracle.py'))
app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)


class OracleRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.root = self.base/'froge-connector'
        (self.root/'state'/'jobs').mkdir(parents=True)
        (self.root/'server.py').write_text('CONNECTOR_VERSION = 34\n')
        (self.root/'state'/'config.json').write_text('{"token":"DO-NOT-EXPORT"}')
        with sqlite3.connect(self.root/'state'/'jobs.sqlite') as db:
            db.execute('CREATE TABLE jobs (id TEXT, state TEXT)')

    def job(self, name='Julia', state='succeeded'):
        jid = app.JOBS[name]; folder = self.root/'state'/'jobs'/jid; folder.mkdir()
        with sqlite3.connect(self.root/'state'/'jobs.sqlite') as db:
            db.execute('INSERT INTO jobs VALUES (?,?)', (jid, state))
        content = b'saved-geometry-fixture'; (folder/'model.glb').write_bytes(content)
        (folder/'model-ready.json').write_text(json.dumps({'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}))
        (folder/'agent-request.json').write_text('{"secret":"EXCLUDED"}')
        return folder

    def test_no_downgrade_and_no_active_update(self):
        self.assertEqual(app.plan_update({'installed_version':35,'active_jobs':0}), 'keep-newer')
        self.assertEqual(app.plan_update({'installed_version':34,'active_jobs':0}), 'keep-current')
        self.assertEqual(app.plan_update({'installed_version':33,'active_jobs':0}), 'install-v34')
        with self.assertRaises(ValueError): app.plan_update({'installed_version':33,'active_jobs':1})

    def test_only_exact_jobs_and_no_secrets(self):
        folder = self.job(); original = (folder/'model.glb').read_bytes()
        other = self.root/'state'/'jobs'/'another-model'; other.mkdir(); (other/'model.glb').write_bytes(b'WRONG')
        output = self.base/'models.zip'; result = app.export_models(self.root, output)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read('Julia/model.glb'), original)
            self.assertEqual(set(archive.namelist()), {'Julia/model.glb','Julia/model-ready.json','RECOVERY.json'})
            self.assertNotIn(b'DO-NOT-EXPORT', b''.join(archive.read(n) for n in archive.namelist()))
        self.assertEqual(result['report']['jobs']['Krolowa-Neptuna']['status'], 'missing')
        self.assertEqual((folder/'model.glb').read_bytes(), original)

    def test_active_job_is_not_exported(self):
        self.job(state='running'); result = app.export_models(self.root,self.base/'models.zip')
        self.assertEqual(result['report']['jobs']['Julia']['status'], 'active-not-exported')
        self.assertFalse(result['report']['jobs']['Julia']['files'])

    def test_checkpoint_mismatch_aborts_without_partial_archive(self):
        folder = self.job(); (folder/'model.glb').write_bytes(b'CHANGED')
        output = self.base/'models.zip'
        with self.assertRaisesRegex(ValueError, 'model-ready'): app.export_models(self.root,output)
        self.assertFalse(output.exists()); self.assertFalse(output.with_suffix('.pending').exists())

    def test_symlink_is_rejected(self):
        folder = self.job(); (folder/'model.glb').unlink()
        (folder/'model.glb').symlink_to(self.root/'state'/'config.json')
        with self.assertRaisesRegex(ValueError, 'Dowiazanie'): app.export_models(self.root,self.base/'models.zip')

    def test_existing_archive_is_preserved(self):
        self.job(); output = self.base/'models.zip'; output.write_bytes(b'ORIGINAL')
        with self.assertRaises(ValueError): app.export_models(self.root,output)
        self.assertEqual(output.read_bytes(),b'ORIGINAL')

    def test_inventory_only_reads_version_ast(self):
        self.job(); (self.root/'server.py').write_text('CONNECTOR_VERSION = 35\nraise RuntimeError("must-not-execute")\n')
        state = app.inventory(self.root)
        self.assertEqual(state['installed_version'],35); self.assertEqual(state['active_jobs'],0)


if __name__ == '__main__': unittest.main()
