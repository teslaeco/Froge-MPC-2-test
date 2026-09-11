#!/usr/bin/env python3
"""One-file Froge v14 texture patch; run in Oracle Cloud Shell. No AI requests."""
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
    # The normal worker's isolated container is reused. No photos, credentials,
    # AI service, pairing, job queue or historical job files are touched.
    sys.path.insert(0, str(target))
    import server
    with tempfile.TemporaryDirectory(prefix='texture-export-check-', dir=target / 'state') as folder:
        work = Path(folder)
        (work / 'scene.json').write_text(json.dumps(scene), encoding='utf-8')
        print('4/5 Sprawdzam eksport 8 materialow z kolorem i normalnymi. Bez AI.', flush=True)
        server.run_blender(str(uuid.uuid4()), work, threading.Event(), timeout=120)
        raw = (work / 'model.glb').read_bytes()
        document = json.loads(raw[20:20 + int.from_bytes(raw[12:16], 'little')])
        materials, images = document.get('materials', []), document.get('images', [])
        if len(materials) != 8 or not 9 <= len(images) <= 16:
            raise RuntimeError('Test eksportu nie zachowal wszystkich materialow i tekstur.')
        if any('baseColorTexture' not in material.get('pbrMetallicRoughness', {}) or 'normalTexture' not in material for material in materials):
            raise RuntimeError('Test eksportu zgubil kolor lub mape normalnych.')
        if any('bufferView' not in image or document['bufferViews'][image['bufferView']]['byteLength'] < 100 for image in images):
            raise RuntimeError('Test eksportu nie osadzil tekstur w GLB.')
        print('FROGE_TEXTURE_EXPORT_OK: 8 materialow, %d osadzonych tekstur.' % len(images), flush=True)


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
            raise RuntimeError('Zainstalowany plik %s nie pasuje do potwierdzonego v14. Nie zmieniono instalacji.' % name)
    print('3/5 Potwierdzono v14. Przygotowuje poprawke z kopia zapasowa.', flush=True)
    with tempfile.TemporaryDirectory(prefix='froge-texture-patch-') as temporary:
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
    if health.get('rendererRevision') != 2 or health.get('sceneReplay') is not True:
        raise RuntimeError('Serwer nie potwierdzil poprawki tekstur i odtwarzania planu.')
    print('5/5 FROGE_TEXTURE_OK: poprawka 2 dziala. Test GLB przeszedl.', flush=True)
    print('Wroc do Froge, odswiez strone, wybierz Sprawdz polaczenie z Oracle, potem Wykonaj zapisany plan bez AI.', flush=True)


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
        print('FROGE_TEXTURE_ERROR: przekroczono czas polaczenia. Zachowaj komunikaty powyzej; sprawdz polaczenie na stronie przed ponowieniem.', file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as error:
        print('FROGE_TEXTURE_ERROR: polecenie zakonczylo sie kodem %d. Przyczyna jest powyzej.' % error.returncode, file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print('FROGE_TEXTURE_ERROR: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
