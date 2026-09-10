"""Check the real container before AI work; keep every resource/isolation limit."""
import os
import pwd
import subprocess
from pathlib import Path

IMAGE = 'localhost/froge-blender:local'


def available_memory_bytes():
    """Available RAM with the enclosing cgroup accounted for, without swap."""
    try:
        values = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        available = int(values['MemAvailable'].split()[0]) * 1024
        maximum = Path('/sys/fs/cgroup/memory.max').read_text().strip()
        if maximum.isdigit():
            current = int(Path('/sys/fs/cgroup/memory.current').read_text())
            available = min(available, max(0, int(maximum)-current))
        return available
    except (OSError, ValueError, KeyError):
        return 0


def job_memory_gib(folder):
    from runtime.reference_quality import requested_edge
    return 8 if requested_edge(folder) == 8192 else 4


def sandbox_options(memory_gib=4):
    if type(memory_gib) is not int or memory_gib not in (4, 8):
        raise ValueError('Unsupported Blender memory profile.')
    return ['--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--userns=keep-id', '--memory=%dg' % memory_gib, '--memory-swap=%dg' % memory_gib, '--cpus=2', '--pids-limit=256',
            '--tmpfs', '/tmp:rw,size=256m', '--shm-size=128m', '-e', 'HOME=/tmp',
            '-e', 'FROGE_EXPORT_MEMORY_GIB=%d' % memory_gib]


class RuntimeUnavailable(RuntimeError):
    def __init__(self, detail):
        self.detail = detail[-2000:]
        self.cpu_missing = 'controller' in detail and 'cpu' in detail and ('not available' in detail or 'not found' in detail)
        super().__init__('Blender nie moze wystartowac na Oracle. Zainstaluj aktualizacje froge-oracle-openai.zip. Instrukcje AI nie zostaly zamowione.')


def verify_runtime(memory_gib=4):
    if memory_gib == 8 and available_memory_bytes() < 10 * 1024**3:
        raise ValueError('Tryb 8K potrzebuje 8 GiB dla Blendera i 2 GiB zapasu wolnej pamieci. '
                         'Wybierz 4K albo zwolnij RAM na serwerze. Nie zamowiono instrukcji AI.')
    # Execute only /bin/true, without job files, network or model/API credentials.
    command = ['podman', 'run', '--rm', '--pull=never'] + sandbox_options(memory_gib) + ['--entrypoint=/bin/true', IMAGE]
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeUnavailable(str(error)) from None
    if result.returncode:
        raise RuntimeUnavailable(result.stderr or result.stdout)


def setup_runtime():
    try:
        verify_runtime()
        return
    except RuntimeUnavailable as error:
        if not error.cpu_missing:
            raise
    # Configure only this account's user manager. Do not remove the CPU limit,
    # use privileged containers, restart the user manager, or restart the tunnel.
    unit = 'user@%d.service' % os.getuid()
    directory = '/etc/systemd/system/' + unit + '.d'
    commands = [
        (['sudo', '-n', 'install', '-d', '-m', '0755', directory], None),
        (['sudo', '-n', 'tee', directory + '/90-froge-cpu-delegation.conf'], '[Service]\nDelegate=cpu memory pids\n'),
        (['sudo', '-n', 'systemctl', 'daemon-reload'], None),
        # A supported live resource property makes systemd realize the updated
        # controller configuration without terminating existing user services.
        (['sudo', '-n', 'systemctl', 'set-property', unit, 'CPUAccounting=yes'], None),
    ]
    for command, payload in commands:
        try:
            result = subprocess.run(command, input=payload, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeUnavailable(str(error)) from None
        if result.returncode:
            raise RuntimeUnavailable(result.stderr or result.stdout)
    verify_runtime()


if __name__ == '__main__':
    try:
        if pwd.getpwuid(os.getuid()).pw_name != 'opc':
            raise RuntimeError('Uruchom na serwerze Oracle jako opc.')
        setup_runtime()
        print('FROGE_RUNTIME_OK')
    except RuntimeUnavailable as error:
        print('FROGE_RUNTIME_ERROR: ' + error.detail)
        raise SystemExit(1)
