import subprocess
import unittest
from unittest.mock import patch

import runtime_check


class RuntimeCheckTests(unittest.TestCase):
    def test_8k_memory_preflight_refuses_before_container_or_ai(self):
        with patch.object(runtime_check,'available_memory_bytes',return_value=9*1024**3),patch.object(runtime_check.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'Nie zamowiono instrukcji AI'):runtime_check.verify_runtime(8)
            run.assert_not_called()

    def test_8k_profile_preserves_isolation_without_swap(self):
        with patch.object(runtime_check,'available_memory_bytes',return_value=12*1024**3),patch.object(runtime_check.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')) as run:
            runtime_check.verify_runtime(8)
        command=run.call_args.args[0]
        for flag in ('--memory=8g','--memory-swap=8g','--cpus=2','--network=none','--read-only','--pids-limit=256','FROGE_EXPORT_MEMORY_GIB=8'):
            self.assertIn(flag,command)
        for value in (True,3,16,'8'):
            with self.assertRaises(ValueError):runtime_check.sandbox_options(value)

    def test_probe_retains_all_limits_and_runs_no_generated_code(self):
        with patch.object(runtime_check.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            runtime_check.verify_runtime()
        command = run.call_args.args[0]
        for option in ('--cpus=2', '--memory=4g', '--memory-swap=4g', '--pids-limit=256', '--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--entrypoint=/bin/true'):
            self.assertIn(option, command)
        self.assertNotIn('-v', command)
        self.assertNotIn('--privileged', command)

    def test_missing_cpu_controller_configures_only_current_user_then_checks_again(self):
        missing = runtime_check.RuntimeUnavailable('controller `cpu` is not available')
        with patch.object(runtime_check, 'verify_runtime', side_effect=[missing, None]) as probe, patch.object(runtime_check.os, 'getuid', return_value=1000), patch.object(runtime_check.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            runtime_check.setup_runtime()
        self.assertEqual(probe.call_count, 2)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn('/etc/systemd/system/user@1000.service.d/90-froge-cpu-delegation.conf', commands[1])
        self.assertIn('Delegate=cpu memory pids', run.call_args_list[1].kwargs['input'])
        self.assertEqual(commands[-1][-2:], ['user@1000.service', 'CPUAccounting=yes'])
        self.assertFalse(any('restart' in command or '--privileged' in command for command in commands))

    def test_other_runtime_errors_do_not_change_system_configuration(self):
        with patch.object(runtime_check, 'verify_runtime', side_effect=runtime_check.RuntimeUnavailable('image missing')), patch.object(runtime_check.subprocess, 'run') as run:
            with self.assertRaises(runtime_check.RuntimeUnavailable):
                runtime_check.setup_runtime()
            run.assert_not_called()

    def test_failed_second_probe_does_not_report_success(self):
        with patch.object(runtime_check, 'verify_runtime', side_effect=runtime_check.RuntimeUnavailable('controller `cpu` is not available')), patch.object(runtime_check.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
            with self.assertRaises(runtime_check.RuntimeUnavailable):
                runtime_check.setup_runtime()


if __name__ == '__main__':
    unittest.main()
