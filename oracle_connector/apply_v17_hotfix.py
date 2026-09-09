"""Upgrade an existing Froge Oracle worker v10-v16 to v17 without resetting state.

This small updater changes only planner/provider/version files, creates a local backup,
compiles every patched Python file before replacement, restarts the user service and
rolls back automatically unless /v1/health confirms connectorVersion 17.
"""
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.request

TARGET = Path.home() / 'froge-connector'
FILES = ('server.py', 'openai_provider.py', 'runtime/scene_contract.py')
GUIDANCE_MARKER = '# FROGE_V17_REFERENCE_GUIDANCE'
GUIDANCE = r'''

# FROGE_V17_REFERENCE_GUIDANCE
PROMPT += """
V17 reference-quality rules:
For reference-driven people preserve the visible outfit instead of replacing it with
generic armor or unrelated clothing. If a reference shows a fitted dress or couture
gown, keep the torso and waist close to the anatomical silhouette and reconstruct a
cropped lower body as a coherent long skirt/gown. Use the existing person as a complete
anatomical base, then add only a few compact loft/mesh/extrusion parts for the dress.
Dress and crystal panels must remain thin relative to human scale; do not inflate them
into thick shells. Preserve collar, shoulders, belt, jewelry, hair ornaments and other
recognizable clothing details before adding decoration. For a sculpted updo, augment
short fitted hair with a few compact ellipsoids/lofts rather than a helmet-sized shell.
For a fan or technological prop preserve handle, thickness and repeated mechanisms.
Prefer one compact turbine/rotor component plus copies for repeated devices. Prefer
procedural parts and copies over giant raw vertex/face arrays so the plan completes
within the bounded JSON contract. Never trade anatomy or outfit identity for polygon count.
"""
'''


def patch_files(original):
    server = original['server.py'].decode()
    match = re.search(r'^CONNECTOR_VERSION = (\d+)$', server, re.M)
    if not match:
        raise RuntimeError('Nie rozpoznano wersji worker-a.')
    version = int(match.group(1))
    if version < 10 or version > 17:
        raise RuntimeError('Hotfix v17 wymaga worker-a w wersji 10-17; wykryto %d.' % version)
    server = re.sub(r'^CONNECTOR_VERSION = \d+$', 'CONNECTOR_VERSION = 17', server, count=1, flags=re.M)

    provider = original['openai_provider.py'].decode()
    if 'MAX_OUTPUT_TOKENS = 9000' not in provider:
        if 'TIME_LIMIT = 180\n' not in provider:
            raise RuntimeError('Nie rozpoznano konfiguracji OpenAI.')
        provider = provider.replace('TIME_LIMIT = 180\n', 'TIME_LIMIT = 180\nMAX_OUTPUT_TOKENS = 9000\n', 1)
    provider = provider.replace("'max_output_tokens': 4500", "'max_output_tokens': MAX_OUTPUT_TOKENS")
    if "'max_output_tokens': MAX_OUTPUT_TOKENS" not in provider:
        raise RuntimeError('Nie udalo sie ustawic budzetu odpowiedzi Astra.')

    contract = original['runtime/scene_contract.py'].decode()
    if GUIDANCE_MARKER not in contract:
        contract += GUIDANCE

    patched = {'server.py': server.encode(), 'openai_provider.py': provider.encode(),
               'runtime/scene_contract.py': contract.encode()}
    for name, data in patched.items():
        compile(data, name, 'exec')
    return patched


def replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.v17-tmp')
    tmp.write_bytes(data)
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def install():
    if pwd.getpwuid(os.getuid()).pw_name != 'opc':
        raise RuntimeError('Uruchom jako uzytkownik opc.')
    state = TARGET / 'state'
    config = state / 'config.json'
    database = state / 'jobs.sqlite'
    if not config.is_file() or not database.is_file():
        raise RuntimeError('Nie znaleziono istniejacej instalacji Froge.')
    original = {name: (TARGET / name).read_bytes() for name in FILES}
    patched = patch_files(original)
    with sqlite3.connect(database, timeout=15) as db:
        db.execute('BEGIN IMMEDIATE')
        active = db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]
        if active:
            raise RuntimeError('Na Oracle trwa generowanie. Poczekaj lub anuluj zadanie.')
        subprocess.run(['systemctl', '--user', 'stop', 'froge-worker.service'], check=True, timeout=30)
    backup = state / 'code-backups' / ('v17-' + str(time.time_ns()))
    backup.mkdir(parents=True, mode=0o700)
    try:
        for name, data in original.items():
            replace(backup / name, data)
        for name, data in patched.items():
            replace(TARGET / name, data)
        subprocess.run(['systemctl', '--user', 'start', 'froge-worker.service'], check=True, timeout=30)
        token = json.loads(config.read_text())['token']
        request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + token})
        for _ in range(20):
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    result = json.loads(response.read(10000))
                    if result.get('connectorVersion') == 17:
                        print('FROGE_V17_OK')
                        print('Oracle worker v17 dziala; pairing, klucz OpenAI i poprzednie modele zostaly zachowane.')
                        return
            except (OSError, ValueError):
                pass
            time.sleep(.5)
        raise RuntimeError('Worker nie potwierdzil connectorVersion 17.')
    except Exception:
        subprocess.run(['systemctl', '--user', 'stop', 'froge-worker.service'], check=False, timeout=30)
        for name, data in original.items():
            replace(TARGET / name, data)
        subprocess.run(['systemctl', '--user', 'start', 'froge-worker.service'], check=False, timeout=30)
        raise


if __name__ == '__main__':
    try:
        install()
    except Exception as error:
        print('FROGE_V17_ERROR: ' + str(error))
        raise SystemExit(1)
