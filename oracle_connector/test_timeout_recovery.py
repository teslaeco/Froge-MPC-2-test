"""Timeout regression checks; no paid inference and no customer jobs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock

import server
from ai_stream import AIStreamTimeout
from image3d_fixture import make_fixture
from runtime.model_checkpoint import save_ready,recover_ready,NAME

JOB='12345678-1234-4234-8234-123456789abc'


class ModelCheckpointTests(unittest.TestCase):
    def test_retains_verified_model_and_never_claims_unfinished_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);model=make_fixture();(folder/'model.glb').write_bytes(model)
            save_ready(folder,{'triangles':12,'master_export':{'formats':['glb','blend']}},'core_export')
            report=recover_ready(folder)
            self.assertEqual(report['triangles'],12)
            self.assertNotIn('interchange_exports',report)
            self.assertFalse(report['timeout_recovery']['review_complete'])
            self.assertEqual((folder/'model.glb').read_bytes(),model)
            self.assertEqual(json.loads((folder/'result.json').read_text()),report)
            (folder/'model.glb').write_bytes(model[:-1]+bytes([model[-1]^1]))
            self.assertIsNone(recover_ready(folder))

    def test_partial_model_and_stale_checkpoint_are_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'model.glb').write_bytes(b'glTF')
            self.assertIsNone(recover_ready(folder))
            with self.assertRaises(ValueError):save_ready(folder,{'triangles':12},'core_export')
            (folder/NAME).write_text('{}')
            self.assertIsNone(recover_ready(folder))


class WorkerTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.paths=patch.multiple(server,STATE=root/'state',JOBS=root/'state/jobs',CONFIG=root/'state/config.json')
        self.paths.start();server.initialize();server.CANCEL.clear();server.RUNNING.clear()

    def tearDown(self):
        server.CANCEL.clear();server.RUNNING.clear();self.paths.stop();self.temp.cleanup()

    def test_ai_timeout_reports_real_stage_and_retains_draft_without_retry(self):
        with server.database() as db:db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',(JOB,'Model drzewa','queued',''))
        with patch.object(server,'WAKE') as wake,patch.object(server,'verify_runtime'), \
             patch.object(server,'ai_settings',return_value={'provider':'openai','api_key':'fixture'}), \
             patch.object(server,'generate_code',side_effect=AIStreamTimeout('Limit 600 s','{"version":',600)) as ai:
            wake.wait.side_effect=[None,StopIteration]
            with self.assertRaises(StopIteration):server.worker()
            ai.assert_called_once()
        folder=server.JOBS/JOB
        failure=json.loads((folder/'failure.json').read_text())
        self.assertEqual(failure['phase'],'astra_plan')
        self.assertFalse(failure['scene_saved'])
        self.assertEqual((folder/'incomplete-response.txt').read_text(),'{"version":')
        with server.database() as db:row=db.execute('SELECT * FROM jobs WHERE id=?',(JOB,)).fetchone()
        self.assertEqual(row['state'],'failed')
        self.assertIn('plan Astry',row['detail']);self.assertNotIn('Qwen',row['detail'])
        self.assertEqual(json.loads((folder/'timing.json').read_text())['last_phase'],'astra_plan')
        self.assertNotIn(JOB,server.RUNNING)

    def test_identical_old_timeout_can_reuse_saved_scene_but_not_other_request(self):
        scene=(Path(__file__).parent/'examples/textures-eight.scene.json').read_text()
        folder=server.JOBS/JOB;folder.mkdir();(folder/'scene.json').write_text(scene)
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',(JOB,'Model','failed','Przekroczono limit czasu. Nie uruchamiam kolejnej dlugiej proby.'))
            recovered=server.recoverable_review_scene(db,'Model',[])
            self.assertEqual(recovered['scene'],scene)
            self.assertIsNone(server.recoverable_review_scene(db,'Different',[]))
        # Without a complete plan the request must not pretend to be reusable.
        (folder/'scene.json').unlink()
        with server.database() as db:self.assertIsNone(server.recoverable_review_scene(db,'Model',[]))

    def test_renderer_timeout_recovers_only_the_current_build(self):
        folder=server.JOBS/JOB;folder.mkdir()
        model=make_fixture();(folder/'model.glb').write_bytes(model)
        cancel=Mock();cancel.wait.return_value=False;cancel.is_set.return_value=False
        def launch(*args,**kwargs):
            process=Mock();process.poll.side_effect=[None,0]
            if make_current[0]:save_ready(folder,{'triangles':12},'core_export')
            return process
        for current in (False,True):
            make_current=[current]
            save_ready(folder,{'triangles':12},'core_export') # stale at process start
            with patch.object(server.subprocess,'Popen',side_effect=launch),patch.object(server.subprocess,'run'):
                if current:server.run_blender(JOB,folder,cancel,timeout=0)
                else:
                    with self.assertRaises(TimeoutError):server.run_blender(JOB,folder,cancel,timeout=0)
        self.assertEqual((folder/'model.glb').read_bytes(),model)


if __name__=='__main__':unittest.main()
