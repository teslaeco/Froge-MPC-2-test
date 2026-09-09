from pathlib import Path
import base64
import hashlib
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from runtime.scene_contract import parse_scene
import json

ROOT = Path(__file__).resolve().parents[1]
repair = SimpleNamespace(**runpy.run_path(str(ROOT / 'public/downloads/froge-napraw-tekstury.py')))


class TextureRepairTests(unittest.TestCase):
    def test_embedded_patch_matches_reviewed_source_and_fixture_has_eight_fabrics(self):
        data = repair.payload()
        frozen=json.loads((ROOT/'scripts/texture-repair-frozen.json').read_text())
        for name, encoded in data['files'].items():
            self.assertEqual(hashlib.sha256(base64.b64decode(encoded)).hexdigest(),frozen[name])
        scene = parse_scene(json.dumps(data['fixture']))
        self.assertEqual(len(scene['materials']), 8)
        self.assertEqual({m['pattern'] for m in scene['materials']}, {'cotton', 'denim'})

    def test_cloud_shell_uses_existing_vm_and_transfers_only_self_contained_code(self):
        with tempfile.TemporaryDirectory() as folder:
            cloud = Path(folder)
            (cloud / 'ssh-key-2026-09-06.key').write_text('fixture-key-never-transferred')
            with patch.object(repair.Path, 'home', return_value=cloud), patch.object(repair.subprocess, 'run') as execute:
                repair.main([])
        execute.assert_called_once()
        self.assertEqual(execute.call_args.args[0][-2:], [repair.HOST, 'python3 - --on-oracle'])
        transferred = execute.call_args.kwargs['input']
        compile(transferred, 'remote-texture-repair', 'exec')
        self.assertNotIn('fixture-key-never-transferred', transferred)
        self.assertIn('verify_export', transferred)

    def test_unknown_installed_code_is_rejected_before_any_service_changes(self):
        import pwd
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(repair.Path, 'home', return_value=Path(folder)), patch.object(pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='opc')), patch.object(repair.subprocess, 'run') as execute:
                with self.assertRaisesRegex(RuntimeError, 'Nie zmieniono instalacji'):
                    repair.apply_remote(repair.payload())
                execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
