import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import apply_update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source, self.target = self.root / 'incoming', self.root / 'installed'
        self.source.mkdir(); (self.target / 'state').mkdir(parents=True)
        (self.source / 'server.py').write_text('version = 2\n')
        (self.source / 'ai_stream.py').write_text('updated = True\n')
        (self.target / 'server.py').write_text('version = 1\n')
        self.config = self.target / 'state/config.json'
        self.config.write_text(json.dumps({'token': 'local-test-token', 'client': 'owner', 'code': 'unchanged'}))
        self.original_config = self.config.read_bytes()
        with sqlite3.connect(self.target / 'state/jobs.sqlite') as db:
            db.execute('CREATE TABLE jobs(state TEXT)')

    def tearDown(self):
        self.temp.cleanup()

    def test_update_preserves_pairing_and_keeps_backup(self):
        with patch.object(apply_update.subprocess, 'run') as service, patch.object(apply_update.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"connectorVersion":2}')):
            apply_update.update(self.source, self.target)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 2\n')
        backups = list((self.target / 'state/code-backups').glob('*/server.py'))
        self.assertEqual(backups[0].read_text(), 'version = 1\n')
        self.assertEqual([call.args[0][-1] for call in service.call_args_list], ['froge-worker.service'] * 2)

    def test_active_job_prevents_service_stop_and_code_replacement(self):
        with sqlite3.connect(self.target / 'state/jobs.sqlite') as db:
            db.execute("INSERT INTO jobs VALUES ('generating')")
        with patch.object(apply_update.subprocess, 'run') as service:
            with self.assertRaisesRegex(RuntimeError, 'aktywne'):
                apply_update.update(self.source, self.target)
            service.assert_not_called()
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_failed_health_check_restores_previous_code_and_pairing(self):
        with patch.object(apply_update.subprocess, 'run'), patch.object(apply_update.urllib.request, 'urlopen', side_effect=OSError('offline')), patch.object(apply_update.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'nie potwierdzil'):
                apply_update.update(self.source, self.target)
        self.assertEqual((self.target / 'server.py').read_text(), 'version = 1\n')
        self.assertFalse((self.target / 'ai_stream.py').exists())
        self.assertEqual(self.config.read_bytes(), self.original_config)


if __name__ == '__main__':
    unittest.main()
