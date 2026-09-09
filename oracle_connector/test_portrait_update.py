import base64,json,runpy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from runtime.scene_contract import parse_scene

ROOT=Path(__file__).resolve().parents[1]
installer=SimpleNamespace(**runpy.run_path(str(ROOT/'public/downloads/froge-v19.py')))


class PortraitInstallerTests(unittest.TestCase):
    def test_payload_exactly_contains_reviewed_runtime_and_a_real_anatomical_fixture(self):
        data=installer.payload()
        for name,raw in data['files'].items():self.assertEqual(base64.b64decode(raw),(ROOT/'oracle_connector'/name).read_bytes())
        scene=parse_scene(json.dumps(data['fixture']))
        self.assertEqual(sum(p['kind']=='reference_character' for p in scene['parts']),1)
        self.assertEqual(set(data['files']),set(data['staged_files']))
        self.assertIn('runtime/assets/anatomy.json.gz',data['files'])
        self.assertIn("health.get('connectorVersion') != 19",(ROOT/'public/downloads/froge-v19.py').read_text())
        self.assertIn('runtime/portrait_hands.py',data['staged_files'])

    def test_unknown_installation_is_untouched(self):
        import pwd
        with tempfile.TemporaryDirectory() as folder,patch.object(installer.Path,'home',return_value=Path(folder)),patch.object(pwd,'getpwuid',return_value=SimpleNamespace(pw_name='opc')),patch.object(installer.subprocess,'run') as commands:
            with self.assertRaisesRegex(RuntimeError,'Nie znaleziono obecnej instalacji'):installer.apply_remote(installer.payload())
            commands.assert_not_called()

    def test_cloud_shell_transfers_only_reviewed_installer_not_the_ssh_key(self):
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder);(home/'ssh-key-2026-09-06.key').write_text('fixture-secret-key')
            with patch.object(installer.Path,'home',return_value=home),patch.object(installer.subprocess,'run') as commands:installer.main([])
        commands.assert_called_once()
        self.assertEqual(commands.call_args.args[0][-2:],[installer.HOST,'python3 - --on-oracle'])
        self.assertNotIn('fixture-secret-key',commands.call_args.kwargs['input'])
        compile(commands.call_args.kwargs['input'],'installer','exec')


if __name__=='__main__':unittest.main()
