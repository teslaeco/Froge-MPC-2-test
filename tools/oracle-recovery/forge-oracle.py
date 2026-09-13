#!/usr/bin/env python3
"""Run the verified v34 updater and export the user's exact saved model jobs.

Cloud Shell entry point. No keys/config are bundled and no paid generation runs.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
import uuid
import zipfile

HOST = 'opc@141.148.242.30'
ZIP_SHA256 = '087f5bc8337e554738a03a335c12ad17cbef05ac555748348a2cc68249187dca'
JOBS = {'Julia': '076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d',
        'Krolowa-Neptuna': '99397623-e45c-48dc-95ec-6f84446a54d5'}
FILES = ('model.glb', 'model.blend', 'model-master.glb', 'model-mm.stl',
         'scene.json', 'edits.py', 'result.json', 'visual-review.json', 'model-ready.json')
TERMINAL = {'succeeded', 'failed', 'cancelled'}
MAX_FILE = 1024 ** 3


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def ensure_plain(path, root):
    if path.is_symlink() or root.is_symlink():
        raise ValueError('Dowiazanie zamiast zwyklego pliku lub katalogu: ' + path.name)
    if root.resolve() not in path.resolve().parents:
        raise ValueError('Plik poza katalogiem zlecenia.')
    for parent in path.parents:
        if parent == root: break
        if parent.is_symlink(): raise ValueError('Dowiazanie w sciezce zlecenia.')
    if not path.is_file() or path.stat().st_size > MAX_FILE:
        raise ValueError('Brak zwyklego pliku lub przekroczony limit 1 GiB: ' + path.name)


def read_json(path, limit=2*1024**2):
    if path.stat().st_size > limit: raise ValueError('Zbyt duzy plik JSON.')
    return json.loads(path.read_text(encoding='utf-8'))


def installed_version(root):
    path = root / 'server.py'; ensure_plain(path, root)
    tree = ast.parse(path.read_text())
    for item in tree.body:
        if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CONNECTOR_VERSION' for t in item.targets):
            value = ast.literal_eval(item.value)
            if type(value) is int: return value
    raise ValueError('Nie mozna ustalic wersji; aktualizacja nie ruszy.')


def inventory(root):
    db = root / 'state' / 'jobs.sqlite'; ensure_plain(db, root)
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as conn:
        rows = dict(conn.execute('SELECT id,state FROM jobs'))
    return {'installed_version': installed_version(root),
            'active_jobs': sum(state not in TERMINAL for state in rows.values()),
            'jobs': {name: {'id': jid, 'state': rows.get(jid),
                            'glb_exists': (root/'state'/'jobs'/jid/'model.glb').is_file()}
                     for name, jid in JOBS.items()}}


def health(root):
    config = root / 'state' / 'config.json'; ensure_plain(config, root)
    token = read_json(config, 100000)['token']
    request = urllib.request.Request('http://127.0.0.1:8765/v1/health',
                                     headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read(100000))
    # Print only a fixed allow-list, never credentials or arbitrary worker text.
    return {key: data.get(key) for key in ('connectorVersion', 'workerRelease',
            'referenceAcceptanceRevision', 'executionEngine', 'ready')}


def plan_update(status):
    version = status['installed_version']
    if type(version) is not int: raise ValueError('Nieznana wersja.')
    if status['active_jobs']: raise ValueError('Trwa zlecenie. Poczekaj na jego zakonczenie; niczego nie anulowano.')
    if version > 34: return 'keep-newer'
    if version == 34: return 'keep-current'
    if version < 19: raise ValueError('Stara instalacja wymaga osobnego sprawdzenia zgodnosci.')
    return 'install-v34'


def export_models(root, destination):
    status = inventory(root)
    report = {'schema': 'forge-private-model-recovery-v1', 'jobs': {}, 'contains_credentials': False,
              'geometry_repaired': False, 'production_approved': False}
    selections = []
    for name, info in status['jobs'].items():
        entry = {**info, 'files': [], 'status': 'missing'}; report['jobs'][name] = entry
        if info['state'] is None: continue
        if info['state'] not in TERMINAL:
            entry['status'] = 'active-not-exported'; continue
        folder = root/'state'/'jobs'/info['id']
        if not folder.is_dir() or folder.is_symlink(): continue
        for filename in FILES:
            path = folder/filename
            if not path.exists() and not path.is_symlink(): continue
            ensure_plain(path, root)
            selections.append((name, info['id'], path))
        entry['status'] = 'awaiting-copy' if any(n == name for n, _, _ in selections) else 'missing'
    total = sum(p.stat().st_size for _, _, p in selections)
    if total > 3*1024**3 or shutil.disk_usage(destination.parent).free < total + 256*1024**2:
        raise ValueError('Brak miejsca na eksport (limit paczki: 3 GiB, zapas: 256 MiB).')
    pending = destination.with_suffix('.pending')
    if destination.exists() or pending.exists(): raise ValueError('Plik docelowy juz istnieje; nie nadpisano go.')
    try:
        with pending.open('xb') as output:
            os.chmod(pending, 0o600)
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED, allowZip64=True) as archive:
                for name, jid, path in selections:
                    before = path.stat(); sha = hashlib.sha256(); copied = 0
                    arcname = name + '/' + path.name
                    with path.open('rb') as source, archive.open(arcname, 'w', force_zip64=True) as target:
                        for block in iter(lambda: source.read(1024*1024), b''):
                            copied += len(block)
                            if copied > MAX_FILE: raise ValueError('Plik rosnie podczas eksportu.')
                            target.write(block); sha.update(block)
                    after = path.stat()
                    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or copied != before.st_size:
                        raise ValueError('Plik zmienil sie podczas odczytu; ponow po zakonczeniu zapisu.')
                    file_report = {'path': arcname, 'bytes': copied, 'sha256': sha.hexdigest()}
                    report['jobs'][name]['files'].append(file_report)
                    if path.name == 'model.glb':
                        checkpoint = path.parent/'model-ready.json'
                        if checkpoint.exists():
                            ensure_plain(checkpoint, root); cp = read_json(checkpoint)
                            if (cp.get('bytes'), cp.get('sha256')) != (copied, sha.hexdigest()):
                                raise ValueError('GLB nie odpowiada model-ready.json: ' + name)
                for entry in report['jobs'].values():
                    if entry['files']: entry['status'] = 'exported'
                archive.writestr('RECOVERY.json', json.dumps(report, ensure_ascii=False, indent=2))
        pending.replace(destination)
    except BaseException:
        pending.unlink(missing_ok=True); raise
    return {'filename': destination.name, 'bytes': destination.stat().st_size,
            'sha256': digest(destination), 'report': report}


def remote_call(args, key):
    options = ['-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=15', '-i', str(key)]
    # All arguments are internal constants or generated safe basenames.
    import shlex
    command = 'python3 - --remote ' + ' '.join(shlex.quote(a) for a in args)
    proc = subprocess.run(['ssh', '-T', *options, HOST, command],
        input=Path(__file__).read_text(), text=True, capture_output=True, timeout=900)
    if proc.returncode:
        raise RuntimeError(proc.stderr[-1200:] or 'Operacja Oracle nie powiodla sie.')
    return json.loads(proc.stdout), options


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', choices=('inventory', 'health', 'export'))
    parser.add_argument('--name')
    parser.add_argument('--export-only', action='store_true')
    args = parser.parse_args()
    if args.remote:
        root = Path.home()/'froge-connector'
        if args.remote == 'inventory': result = inventory(root)
        elif args.remote == 'health': result = health(root)
        else:
            if not args.name or not args.name.startswith('FORGE-modele-') or not args.name.endswith('.zip') or Path(args.name).name != args.name or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.' for c in args.name):
                raise ValueError('Nieprawidlowa nazwa eksportu.')
            result = export_models(root, Path.home()/args.name)
        print(json.dumps(result)); return
    key = Path.home()/'ssh-key-2026-09-06.key'
    if not key.is_file(): raise ValueError('Uruchom w swoim Oracle Cloud Shell z dotychczasowym kluczem SSH. Nie wysylaj klucza do czatu.')
    status, options = remote_call(['inventory'], key)
    print('Wersja Oracle:', status['installed_version'], '| Aktywne zadania:', status['active_jobs'], flush=True)
    if not args.export_only:
        action = plan_update(status)
        if action == 'install-v34':
            package = Path(__file__).parent/'froge-v34.zip'
            if digest(package) != ZIP_SHA256: raise ValueError('Uszkodzona paczka v34.')
            with tempfile.TemporaryDirectory(prefix='forge-v34-') as tmp:
                with zipfile.ZipFile(package) as archive:
                    installer = Path(tmp)/'froge-v34.py'; installer.write_bytes(archive.read('froge-v34.py'))
                subprocess.run([sys.executable, str(installer)], check=True)
        else: print('Zachowuje obecna wersje; nie cofam generatora.', flush=True)
        confirmed, _ = remote_call(['health'], key)
        if confirmed.get('connectorVersion') != max(34, status['installed_version']):
            raise ValueError('Brak potwierdzenia wersji uruchomionego workera. Nie ponawiaj instalacji w ciemno.')
        print('Wersja potwierdzona przez health:', confirmed['connectorVersion'], flush=True)
    name = 'FORGE-modele-julia-neptune-' + uuid.uuid4().hex[:12] + '.zip'
    exported, options = remote_call(['export', '--name', name], key)
    if exported.get('filename') != name: raise ValueError('Nieprawidlowa nazwa eksportu z serwera.')
    output = Path.home()/name
    if output.exists(): raise ValueError('Plik lokalny istnieje; nie nadpisano.')
    if shutil.disk_usage(output.parent).free < exported['bytes'] + 128*1024**2:
        raise ValueError('Brak miejsca w Cloud Shell. Eksport pozostaje w katalogu domowym opc: ' + name)
    pending = output.with_suffix('.pending')
    if pending.exists(): raise ValueError('Niedokonczony lokalny plik juz istnieje.')
    try:
        subprocess.run(['scp', *options, HOST+':'+name, str(pending)], check=True, timeout=900)
        if pending.stat().st_size != exported['bytes'] or digest(pending) != exported['sha256']:
            raise ValueError('Eksport po pobraniu ma niezgodna sume kontrolna.')
        os.chmod(pending, 0o600); pending.replace(output)
    finally: pending.unlink(missing_ok=True)
    print('FROGE_MODELS_EXPORTED:', output, flush=True)
    for model, entry in exported['report']['jobs'].items():
        print(model, entry['id'], entry['status'], 'plikow:', len(entry['files']))
    print('To kopia zapisanych plikow, nie nowa generacja ani naprawa geometrii. Oryginaly pozostaja na Oracle.')


if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: raise SystemExit('Przerwano. Sprawdz status Oracle przed ponowieniem.')
    except Exception as error: raise SystemExit('FORGE_ORACLE_ERROR: ' + str(error))
