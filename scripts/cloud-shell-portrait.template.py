#!/usr/bin/env python3
"""One-file Froge v15 portrait standard update; run in Oracle Cloud Shell. No AI requests."""
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid

HOST = 'opc@141.148.242.30'
PAYLOAD_B64 = '__PAYLOAD_B64__'
PAYLOAD_SHA256 = '__PAYLOAD_SHA256__'


def payload():
    raw = gzip.decompress(base64.b64decode(PAYLOAD_B64, validate=True))
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise RuntimeError('Plik poprawki jest uszkodzony. Pobierz go ponownie.')
    data = json.loads(raw)
    for name, encoded in data['files'].items():
        if name not in data['staged_files']:
            raise RuntimeError('Nieprawidlowa zawartosc poprawki.')
        compile(base64.b64decode(encoded, validate=True), name, 'exec')
    return data


def verify_export(target, scene):
    sys.path.insert(0, str(target))
    import server
    with tempfile.TemporaryDirectory(prefix='portrait-export-check-', dir=target / 'state') as folder:
        work = Path(folder)
        (work / 'scene.json').write_text(json.dumps(scene), encoding='utf-8')
        print('4/5 Sprawdzam prawdziwy eksport twarzy, oczu, dloni i paznokci. Bez AI.', flush=True)
        server.run_blender(str(uuid.uuid4()), work, threading.Event(), timeout=180)
        raw = (work / 'model.glb').read_bytes()
        document = json.loads(raw[20:20 + int.from_bytes(raw[12:16], 'little')])
        report = json.loads((work / 'result.json').read_text())['portrait_quality']
        expected = {'anatomical_head': 1, 'anatomical_eye': 2, 'anatomical_hand': 2, 'anatomical_nail': 10}
        for key, count in expected.items():
            actual = sum(bool(node.get('extras', {}).get(key)) for node in document['nodes'])
            if actual != count:
                raise RuntimeError('Eksport GLB zgubil anatomie: ' + key)
        if report.get('revision') != 1 or report.get('structural_checks_passed') is not True:
            raise RuntimeError('Nie potwierdzono kontroli anatomii.')
        if not all('bufferView' in image for image in document.get('images', [])):
            raise RuntimeError('Tekstury nie zostaly osadzone w GLB.')
        print('FROGE_PORTRAIT_EXPORT_OK: twarz, 2 oczy, 2 dlonie, 10 paznokci.', flush=True)


def apply_remote(data):
    import pwd
    import shutil
    import urllib.request
    if pwd.getpwuid(os.getuid()).pw_name != 'opc':
        raise RuntimeError('Ta czesc poprawki wymaga konta opc na maszynie Oracle.')
    target = Path.home() / 'froge-connector'
    for name, expected in data['base_hashes'].items():
        path = target / name
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ''
        incoming = hashlib.sha256(base64.b64decode(data['files'][name])).hexdigest()
        if current not in (expected, incoming):
            raise RuntimeError('Zainstalowany plik %s nie pasuje do potwierdzonej instalacji v14 lub v15. Nie zmieniono instalacji.' % name)
    print('3/5 Potwierdzono pliki instalacji. Przygotowuje v15 z kopia zapasowa.', flush=True)
    with tempfile.TemporaryDirectory(prefix='froge-portrait-update-') as temporary:
        staging = Path(temporary)
        for name in data['staged_files']:
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name in data['files']:
                path.write_bytes(base64.b64decode(data['files'][name], validate=True))
            else:
                shutil.copyfile(target / name, path)
        sys.path.insert(0, str(staging))
        import apply_update
        apply_update.update(staging, target, verify=lambda root: verify_export(root, data['fixture']))
    config = json.loads((target / 'state/config.json').read_text())
    request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + config['token']})
    with urllib.request.urlopen(request, timeout=15) as response:
        health = json.loads(response.read(10000))
    if health.get('connectorVersion') != 15 or health.get('rendererRevision') != 3 or health.get('portraitRevision') != 1:
        raise RuntimeError('Serwer nie potwierdzil aktywnego standardu postaci v15.')
    print('5/5 FROGE_PORTRAIT_OK: v15 dziala. Test GLB przeszedl.', flush=True)
    print('Wroc do Froge, odswiez strone, wybierz Sprawdz polaczenie z Oracle, potem wygeneruj nowy model ze zdjec. Poprawiona figurka jest juz dostepna na stronie.', flush=True)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    data = payload()
    if arguments == ['--on-oracle']:
        return apply_remote(data)
    if arguments:
        raise RuntimeError('Uruchom bez dodatkowych argumentow w Oracle Cloud Shell.')
    key = Path.home() / 'ssh-key-2026-09-06.key'
    if not key.is_file():
        raise RuntimeError('Brakuje ssh-key-2026-09-06.key w Cloud Shell. Klucz pozostaje w Cloud Shell; nie przesylaj go do czatu.')
    print('1/5 Plik poprawki zweryfikowany. Nie potrzeba nowego ZIP-a.', flush=True)
    options = ['-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-i', str(key)]
    print('2/5 Lacze z Twoja istniejaca maszyna Oracle.', flush=True)
    subprocess.run(['ssh', '-T', *options, HOST, 'python3 - --on-oracle'], input=Path(__file__).read_text(encoding='utf-8'), text=True, check=True, timeout=360)


if __name__ == '__main__':
    try:
        main()
    except subprocess.TimeoutExpired:
        print('FROGE_PORTRAIT_ERROR: przekroczono czas polaczenia. Zachowaj komunikaty powyzej; sprawdz polaczenie na stronie przed ponowieniem.', file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as error:
        print('FROGE_PORTRAIT_ERROR: polecenie zakonczylo sie kodem %d. Przyczyna jest powyzej.' % error.returncode, file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print('FROGE_PORTRAIT_ERROR: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
