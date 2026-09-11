#!/usr/bin/env python3
"""FORGE v23: freeform geometry and masked photo projection on Oracle."""
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
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise RuntimeError('Nieprawidlowa sciezka w poprawce.')
        decoded = base64.b64decode(encoded, validate=True)
        if name.endswith('.py'):
            compile(decoded, name, 'exec')
    return data


def verify_export(target):
    sys.path.insert(0, str(target))
    import server
    from image3d_fixture import make_fixture
    with tempfile.TemporaryDirectory(prefix='image3d-install-check-', dir=target / 'state') as temporary:
        folder = Path(temporary)
        raw = make_fixture()
        (folder / 'model-master.glb').write_bytes(raw)
        (folder / 'image3d-manifest.json').write_text(json.dumps({'revision':1,
            'provider':'offline-installation-fixture','files':[{'path':'model-master.glb',
            'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}], 'textures':[],
            'likeness_verified':False}))
        print('Sprawdzam import modelu i eksport FBX/OBJ/STL. Plik testowy, bez platnego AI.', flush=True)
        server.run_blender(str(uuid.uuid4()), folder, threading.Event(), timeout=600)
        for format in ('master','fbx','obj','stl','blend'):
            server.export_files(folder, format)
        report = json.loads((folder / 'result.json').read_text())
        if report.get('triangles') != 12 or report.get('anatomy_template_used') is not False:
            raise RuntimeError('Test importu/eksportu nie przeszedl.')
        if (folder / 'model-master.glb').read_bytes() != raw:
            raise RuntimeError('Oryginal modelu zostal zmieniony.')
        print('FROGE_IMAGE3D_EXPORT_OK. Geometria i tekstura testowa zachowane.', flush=True)

    from v23_fixture import write_fixture
    with tempfile.TemporaryDirectory(prefix='v23-projection-install-check-', dir=target/'state') as temporary:
        folder=Path(temporary);write_fixture(folder)
        print('Sprawdzam nowe powierzchnie, dwie tekstury i zaslanianie. Dane kontrolne, bez AI.',flush=True)
        server.run_blender(str(uuid.uuid4()),folder,threading.Event(),timeout=300)
        report=json.loads((folder/'result.json').read_text())
        if report.get('photo_projection',{}).get('mapped_faces')!=2:
            raise RuntimeError('Test maskowania lub zaslaniania projekcji nie przeszedl.')
        for format in ('fbx','obj','stl','blend'):server.export_files(folder,format)
        print('FROGE_V23_GEOMETRY_PROJECTION_OK: narzedzia i eksporty sprawdzone.',flush=True)



def install_on_oracle(data):
    import pwd
    if pwd.getpwuid(os.getuid()).pw_name != 'opc':
        raise RuntimeError('Instalacja wymaga konta opc na Twojej maszynie Oracle.')
    target = Path.home() / 'froge-connector'
    with tempfile.TemporaryDirectory(prefix='froge-v23-update-') as temporary:
        staging = Path(temporary)
        for name, encoded in data['files'].items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(encoded, validate=True))
        sys.path.insert(0, str(staging))
        import apply_update
        apply_update.update(staging, target, verify=verify_export)
    print('FROGE_V23_OK: Astra + Blender zainstalowane. Test eksportow zakonczony; nie generowano postaci przez API.', flush=True)
    print('Astra Max obsluguje zdjecia. Zapisany klucz OpenAI pozostaje. Odswiez strone i sprawdz polaczenie.', flush=True)


def main():
    arguments = sys.argv[1:]
    if arguments == ['--on-oracle']:
        return install_on_oracle(payload())
    if arguments:
        raise RuntimeError('Uruchom bez dodatkowych argumentow. Aktualizacja korzysta z zapisanego OpenAI.')
    key = Path.home() / 'ssh-key-2026-09-06.key'
    if not key.is_file():
        raise RuntimeError('Brakuje klucza SSH w Oracle Cloud Shell. Uzyj swojego Cloud Shell z obecnym kluczem; nie przesylaj go do czatu.')
    options = ['-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=20',
               '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-i',str(key)]
    payload()
    print('Lacze z obecna maszyna Oracle. Aktualizacja zachowa polaczenie, klucze i modele.', flush=True)
    stopped = threading.Event()
    def progress():
        seconds = 0
        while not stopped.wait(15):
            seconds += 15
            print('Aktualizacja Oracle trwa: %d s. Czekam na wynik instalacji i testu eksportow.' % seconds, flush=True)
    ticker = threading.Thread(target=progress, daemon=True); ticker.start()
    try:
        subprocess.run(['ssh','-T',*options,HOST,'python3 -u - --on-oracle'],
            input=Path(__file__).read_text(encoding='utf-8'),text=True,check=True,timeout=900)
    finally:
        stopped.set(); ticker.join(timeout=1)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, subprocess.CalledProcessError):
            print('FROGE_V23_ERROR: operacja nie powiodla sie. Przyczyna jest powyzej.', file=sys.stderr)
        elif isinstance(error, subprocess.TimeoutExpired):
            print('FROGE_V23_ERROR: limit czasu polaczenia. Sprawdz status Oracle przed ponowieniem.', file=sys.stderr)
        else:
            print('FROGE_V23_ERROR: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
