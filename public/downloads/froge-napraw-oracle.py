#!/usr/bin/env python3
"""Run the verified Froge v19 update from Oracle Cloud Shell; never start AI jobs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

HOST = 'opc@141.148.242.30'
PAYLOAD_HASH = '5f3168a03c7c760187107e503f8289facd1832861a63a93ab3a51318fea8a379'
MAX_BYTES = 32 * 1024 * 1024


def verified_archive(path):
    try:
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return False
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if not 1 <= len(entries) <= 64 or sum(item.file_size for item in entries) > MAX_BYTES:
                return False
            names = [item.filename for item in entries]
            if len(set(names)) != len(names) or any(Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name for name in names):
                return False
            digest = hashlib.sha256()
            for name in sorted(names):
                digest.update(name.encode() + b'\0' + hashlib.sha256(archive.read(name)).digest())
            return digest.hexdigest() == PAYLOAD_HASH
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
        return False


def choose_archive(directories, explicit=None):
    candidates = [explicit] if explicit else list({path for directory in directories for path in directory.glob('*.zip')})
    valid = [path for path in candidates if path and verified_archive(path)]
    if not valid:
        raise RuntimeError('Nie znaleziono poprawnej paczki v19. Przeslij froge-oracle-update.zip do Cloud Shell obok tego skryptu. Nazwa ZIP moze zawierac dopisek (1).')
    return max(valid, key=lambda path: path.stat().st_mtime)


def remote_program(remote_archive, archive_hash):
    # All paths originate here, never from the selected ZIP filename.
    return '''import hashlib, json, os, pwd, subprocess, sys, urllib.request, zipfile
from pathlib import Path
if pwd.getpwuid(os.getuid()).pw_name != 'opc':
    raise SystemExit('FROGE_REPAIR_ERROR: wymagane konto opc na Oracle.')
archive_path = Path(%s)
if hashlib.sha256(archive_path.read_bytes()).hexdigest() != %s:
    raise SystemExit('FROGE_REPAIR_ERROR: przeslany ZIP jest niekompletny.')
staging = archive_path.with_suffix('')
staging.mkdir(mode=0o700)
with zipfile.ZipFile(archive_path) as archive:
    archive.extractall(staging)
print('3/4 Instaluje v19 na Oracle. Zachowuje dane i ustawienia.', flush=True)
result = subprocess.run([sys.executable, str(staging / 'apply_update.py')])
if result.returncode:
    raise SystemExit(result.returncode)
print('4/4 Sprawdzam odpowiedz uruchomionego generatora.', flush=True)
config = json.loads((Path.home() / 'froge-connector/state/config.json').read_text())
request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + config['token']})
try:
    with urllib.request.urlopen(request, timeout=15) as response:
        health = json.loads(response.read(10000))
except Exception:
    raise SystemExit('FROGE_REPAIR_ERROR: usluga nie odpowiedziala na sprawdzenie po instalacji.')
version = health.get('connectorVersion')
provider = 'openai' if health.get('provider') == 'openai' else 'ollama'
ready = health.get('ready') is True
photos = version == 19 and provider == 'openai' and ready and health.get('photoInput') is True
print('FROGE_DIAG ' + json.dumps({'version': version if type(version) is int else None, 'provider': provider, 'ready': ready, 'photos': photos}), flush=True)
if version != 19:
    raise SystemExit('FROGE_REPAIR_ERROR: uruchomiona usluga nie potwierdza v19.')
print('FROGE_REPAIR_OK: na Oracle dziala generator v19.', flush=True)
if photos:
    print('Obsluga zdjec gotowa. Na stronie wybierz Sprawdz serwer po aktualizacji, potem Generuj.', flush=True)
elif provider != 'openai':
    print('Generowanie ze zdjec jeszcze wymaga OpenAI. Na stronie otworz Ustawienia serwera / Podlacz Astre. Lokalny Qwen obsluguje tylko tekst.', flush=True)
else:
    print('OpenAI nie jest jeszcze gotowe. Sprawdz jego ustawienia na stronie.', flush=True)
''' % (repr(remote_archive), repr(archive_hash))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Instalacja wgranego ZIP v19 na istniejacej maszynie Oracle. Uruchom w Cloud Shell.')
    parser.add_argument('--archive', type=Path, help='Opcjonalna sciezka do ZIP; domyslnie szuka w katalogu domowym i biezacym.')
    args = parser.parse_args(argv)
    cloud_home = Path.home()
    ssh_key = cloud_home / 'ssh-key-2026-09-06.key'
    if not ssh_key.is_file():
        raise RuntimeError('Brakuje ssh-key-2026-09-06.key w katalogu domowym Cloud Shell. Klucz pozostaje w Cloud Shell; nie przesylaj go do czatu.')
    archive = choose_archive({cloud_home, Path.cwd(), Path(__file__).resolve().parent}, args.archive)
    print('1/4 Zweryfikowana paczka v19: ' + archive.name, flush=True)
    options = ['-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-i', str(ssh_key)]
    remote_archive = '/home/opc/froge-update-' + uuid.uuid4().hex + '.zip'
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    print('2/4 Przesylam aktualizacje na Oracle.', flush=True)
    subprocess.run(['scp', *options, str(archive.resolve()), HOST + ':' + remote_archive], check=True, timeout=120)
    subprocess.run(['ssh', '-T', *options, HOST, 'python3 -'], input=remote_program(remote_archive, archive_hash), text=True, check=True, timeout=300)


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        print('FROGE_REPAIR_ERROR: przekroczono czas oczekiwania. Operacja na Oracle mogla jeszcze trwac; zachowaj komunikaty powyzej i sprawdz status na stronie.', file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as error:
        print('FROGE_REPAIR_ERROR: etap zakonczyl sie kodem %d. Przyczyna jest w komunikacie bezposrednio powyzej.' % error.returncode, file=sys.stderr)
        raise SystemExit(1)
    except (OSError, RuntimeError) as error:
        print('FROGE_REPAIR_ERROR: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
