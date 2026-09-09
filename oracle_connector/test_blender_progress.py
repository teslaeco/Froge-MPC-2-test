import json
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch
import server


class BlenderProgressTests(unittest.TestCase):
    def test_progress_uses_elapsed_not_absolute_monotonic_clock(self):
        process=Mock();process.poll.side_effect=[None,None,0];process.returncode=0
        cancelled=Mock();cancelled.wait.return_value=False
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);raw=json.dumps({'asset':{'version':'2.0'}}).encode();raw+=b' '*((-len(raw))%4)
            (path/'model.glb').write_bytes(struct.pack('<IIIII',0x46546c67,2,20+len(raw),len(raw),0x4e4f534a)+raw)
            with patch.object(server.subprocess,'Popen',return_value=process),patch.object(server.time,'monotonic',side_effect=[1000000,1000000,1000001,1000010,1000011]),patch.object(server,'status') as progress:
                server.run_blender('test',path,cancelled)
            self.assertEqual(progress.call_count,2)
            self.assertIn('0:00',progress.call_args_list[0].args[2])
            self.assertIn('0:10',progress.call_args_list[1].args[2])

    def test_cancel_forces_cleanup_even_when_container_commands_time_out(self):
        process=Mock();process.poll.return_value=None
        cancelled=threading.Event();cancelled.set()
        with tempfile.TemporaryDirectory() as folder,patch.object(server.subprocess,'Popen',return_value=process),patch.object(server.subprocess,'run',side_effect=subprocess.TimeoutExpired('podman',15)) as command,patch.object(server,'status'):
            with self.assertRaises(InterruptedError):server.run_blender('cancel-test',Path(folder),cancelled)
        process.kill.assert_called_once()
        self.assertEqual(command.call_args_list[-1].args[0],['podman','rm','--force','froge-job-cancel-test'])
        process.wait.assert_called_with(timeout=5)


if __name__=='__main__':unittest.main()
