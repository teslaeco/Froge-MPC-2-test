from pathlib import Path
import runpy
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
repair = SimpleNamespace(**runpy.run_path(str(ROOT / 'public/downloads/froge-napraw-oracle.py')))


class CloudShellRepairTests(unittest.TestCase):
    def test_accepts_verified_v14_despite_browser_filename_suffix(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'aktualizacja v14 (1).zip'
            shutil.copyfile(ROOT / 'public/downloads/froge-oracle-update.zip', archive)
            self.assertEqual(repair.choose_archive([root]), archive)

    def test_rejects_an_archive_with_replaced_installer_even_if_version_stays_v14(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'modified.zip'
            with zipfile.ZipFile(ROOT / 'public/downloads/froge-oracle-update.zip') as source, zipfile.ZipFile(archive, 'w') as target:
                for name in source.namelist():
                    target.writestr(name, b'print("unexpected installer")' if name == 'apply_update.py' else source.read(name))
            self.assertFalse(repair.verified_archive(archive))

    def test_runs_only_the_existing_vm_and_checks_health_without_submitting_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'update with spaces.zip'
            shutil.copyfile(ROOT / 'public/downloads/froge-oracle-update.zip', archive)
            (root / 'ssh-key-2026-09-06.key').write_text('fixture-not-a-real-key')
            with patch.object(repair.Path, 'home', return_value=root), patch.object(repair.subprocess, 'run') as execute:
                repair.main(['--archive', str(archive)])
            calls = execute.call_args_list
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0].args[0][0], 'scp')
            self.assertIn(str(archive), calls[0].args[0])
            self.assertTrue(calls[0].args[0][-1].startswith(repair.HOST + ':/home/opc/froge-update-'))
            self.assertEqual(calls[1].args[0][-2:], [repair.HOST, 'python3 -'])
            program = calls[1].kwargs['input']
            compile(program, 'remote-repair', 'exec')
            self.assertIn('/v1/health', program)
            self.assertNotIn('/v1/jobs', program)
            self.assertNotIn('fixture-not-a-real-key', program)


if __name__ == '__main__':
    unittest.main()
