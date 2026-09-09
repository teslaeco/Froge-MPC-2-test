"""Apply the worker-only update on the existing Oracle VM without resetting pairing."""
import json
import hashlib
import os
from pathlib import Path
import pwd
import sqlite3
import subprocess
import time
import urllib.request
from runtime_check import RuntimeUnavailable, setup_runtime

ASSETS = ('anatomy.json.gz', 'male-skin.png', 'female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png', 'LICENSE.CC0.md', 'SOURCES.md', 'manifest.json')
FILES = ('code_policy.py', 'ai_stream.py', 'openai_provider.py', 'runtime_check.py', 'server.py', 'runtime/run.py', 'runtime/scene_contract.py', 'runtime/build_scene.py', 'runtime/detailed_geometry.py', 'runtime/anatomy.py', 'runtime/wardrobe.py', 'runtime/textiles.py') + tuple('runtime/assets/'+name for name in ASSETS)
EXPECTED_VERSION = 17


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
        if name.endswith('.py'):compile(data, name, 'exec')
    manifest=json.loads(incoming['runtime/assets/manifest.json'])
    if set(manifest) != {'anatomy.json.gz','male-skin.png','female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png'} or any(hashlib.sha256(incoming['runtime/assets/'+name]).hexdigest()!=digest for name,digest in manifest.items()):
        raise RuntimeError('Niekompletne lub uszkodzone dane anatomii. Pobierz ZIP ponownie. Nie zmieniono instalacji.')
    original = {name: (target / name).read_bytes() if (target / name).exists() else None for name in FILES}
    command = ['systemctl', '--user']
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
        token = json.loads(config_path.read_text())['token']
        request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + token})
        for _ in range(20):
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    if json.loads(response.read(10000)).get('connectorVersion') == EXPECTED_VERSION:
                        print('FROGE_UPDATE_OK')
                        print('Wersja 17 uruchomiona. Zwiekszono budzet kompletnego planu Astra i dodano zasady zachowania dopasowanej odziezy, sukien oraz powtarzalnych detali referencji. Klucz OpenAI, polaczenie i poprzednie modele zachowane.')
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
