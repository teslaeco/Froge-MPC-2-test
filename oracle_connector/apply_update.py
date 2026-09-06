"""Apply the worker-only update on the existing Oracle VM without resetting pairing."""
import json
import os
from pathlib import Path
import pwd
import sqlite3
import subprocess
import time
import urllib.request
from runtime_check import RuntimeUnavailable, setup_runtime

FILES = ('code_policy.py', 'ai_stream.py', 'openai_provider.py', 'runtime_check.py', 'server.py', 'runtime/run.py')
EXPECTED_VERSION = 4


def replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.update-tmp')
    temporary.write_bytes(data)
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def update(source, target):
    state = target / 'state'
    config_path = state / 'config.json'
    db_path = state / 'jobs.sqlite'
    if not config_path.is_file() or not db_path.is_file():
        raise RuntimeError('Nie znaleziono obecnej instalacji Froge. Nie zmieniono plikow.')
    incoming = {name: (source / name).read_bytes() for name in FILES}
    for name, data in incoming.items():
        compile(data, name, 'exec')
    original = {name: (target / name).read_bytes() if (target / name).exists() else None for name in FILES}
    command = ['systemctl', '--user']
    # Hold the queue lock until the HTTP worker stops, preventing a new job from
    # being accepted between checking the queue and replacing its running code.
    with sqlite3.connect(db_path, timeout=15) as db:
        db.execute('BEGIN IMMEDIATE')
        busy = db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]
        if busy:
            raise RuntimeError('Zlecenie jest jeszcze aktywne. Poczekaj na wynik lub anuluj je na stronie, potem ponow aktualizacje.')
        try:
            setup_runtime()
        except RuntimeUnavailable as error:
            raise RuntimeError('Kontener Blendera nadal nie startuje. Nie zmieniono programu. Pokaz ten komunikat: ' + error.detail) from None
        subprocess.run(command + ['stop', 'froge-worker.service'], check=True, timeout=30)
    try:
        backup = state / 'code-backups' / str(time.time_ns())
        backup.mkdir(parents=True, mode=0o700)
        for name, data in original.items():
            if data is not None:
                replace(backup / name, data)
        for name, data in incoming.items():
            replace(target / name, data)
        subprocess.run(command + ['start', 'froge-worker.service'], check=True, timeout=30)
        # Use the existing credential locally; it is never printed or changed.
        token = json.loads(config_path.read_text())['token']
        request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + token})
        for _ in range(20):
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    if json.loads(response.read(10000)).get('connectorVersion') == EXPECTED_VERSION:
                        print('FROGE_UPDATE_OK')
                        print('Odswiez Froge. W Ustawieniach serwera wybierz OpenAI i podlacz klucz API, potem ponow opis.')
                        return
            except (OSError, ValueError):
                pass
            time.sleep(0.5)
        raise RuntimeError('Nowy program nie potwierdzil uruchomienia.')
    except Exception:
        subprocess.run(command + ['stop', 'froge-worker.service'], check=False, timeout=30)
        for name, data in original.items():
            if data is None:
                (target / name).unlink(missing_ok=True)
            else:
                replace(target / name, data)
        subprocess.run(command + ['start', 'froge-worker.service'], check=False, timeout=30)
        raise


if __name__ == '__main__':
    try:
        if pwd.getpwuid(os.getuid()).pw_name != 'opc':
            raise RuntimeError('Uruchom aktualizacje na serwerze Oracle jako opc.')
        update(Path(__file__).resolve().parent, Path.home() / 'froge-connector')
    except Exception as error:
        print('FROGE_UPDATE_ERROR: ' + str(error))
        raise SystemExit(1)
