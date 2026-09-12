"""Differential staging integrity; never touches a live worker or paid API."""
import base64
import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest


class DeltaStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.target=self.root/'installed';self.staging=self.root/'incoming'
        self.staging.mkdir();self.target.mkdir()
        self.stage=runpy.run_path(str(Path(__file__).parents[1]/'scripts/cloud-shell-v31.template.py'))['stage_update']
        self.data={'files':{'server.py':base64.b64encode(b'new_code=True\n').decode()},'base_assets':{}}
        for name in ('anatomy.json.gz','male-skin.png','female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png'):
            key='runtime/assets/'+name;path=self.target/key;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('unchanged fixture '+name).encode())
            self.data['base_assets'][key]=hashlib.sha256(path.read_bytes()).hexdigest()
        (self.target/'server.py').write_text('old_code=True\n')

    def test_complete_staging_contains_new_code_and_exact_pinned_assets_without_modifying_install(self):
        self.stage(self.data,self.target,self.staging)
        self.assertEqual((self.staging/'server.py').read_bytes(),b'new_code=True\n')
        for name in self.data['base_assets']:
            self.assertEqual((self.staging/name).read_bytes(),(self.target/name).read_bytes())
        self.assertEqual((self.target/'server.py').read_text(),'old_code=True\n')

    def test_modified_missing_or_symlink_base_fails_before_active_code_changes(self):
        name=next(iter(self.data['base_assets']));source=self.target/name;original=source.read_bytes()
        for mode in ('modified','missing','symlink'):
            with self.subTest(mode=mode):
                source.unlink(missing_ok=True)
                if mode=='modified':source.write_bytes(b'corrupt')
                if mode=='symlink':
                    other=self.root/'other';other.write_bytes(original);source.symlink_to(other)
                with self.assertRaisesRegex(RuntimeError,'Nie zmieniono instalacji'):
                    self.stage(self.data,self.target,self.staging)
                self.assertEqual((self.target/'server.py').read_text(),'old_code=True\n')


if __name__=='__main__':unittest.main()
