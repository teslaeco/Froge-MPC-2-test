"""Apply the worker-only update on the existing Oracle VM without resetting pairing."""
import json
import hashlib
import os
from pathlib import Path
import pwd
import sqlite3
import subprocess
import sys
import time
import urllib.request
from runtime_check import RuntimeUnavailable, setup_runtime

ASSETS = ('anatomy.json.gz', 'male-skin.png', 'female-skin.png','cotton-jersey-albedo.png','indigo-denim-albedo.png', 'LICENSE.CC0.md', 'SOURCES.md', 'manifest.json')
FILES = ('code_policy.py', 'ai_stream.py', 'openai_provider.py', 'photo_input.py', 'runtime_check.py', 'server.py', 'runtime/run.py', 'runtime/scene_contract.py', 'runtime/build_scene.py', 'runtime/detailed_geometry.py', 'runtime/anatomy.py', 'runtime/wardrobe.py', 'runtime/textiles.py') + tuple('runtime/assets/'+name for name in ASSETS)
FILES += ('visual_review.py',)
FILES += ('runtime/reference_surfaces.py','runtime/reference_quality.py','runtime/reference_match.py','runtime/assets/emerald-reference-signature.json')
FILES += ('face_measurement.py','runtime/photo_face.py','runtime/photo_face_color.py','runtime/assets/face-template-feminine.json')
FILES += ('runtime/assets/emerald-reference-landmarks.json',)
FILES += tuple('runtime/'+name for name in ('portrait.py','portrait_eyes.py','portrait_shape.py','portrait_orbits.py','portrait_hands.py','portrait_hair.py','portrait_hair_surface.py','portrait_locks.py','fashion.py','couture.py','couture_geometry.py','couture_qa.py','review_views.py','scene_exports.py'))
FILES += ('image3d_fixture.py', 'runtime/imported_asset.py')
FILES += ('generation_budget.py','quality_report.py','v23_fixture.py',
          'runtime/freeform_geometry.py','runtime/projection_math.py','runtime/photo_projection.py')
FILES += ('runtime/model_checkpoint.py','scene_repair.py',)
FILES += ('agent_limits.py','paid_trial.py','blender_mcp.py','codex_runner.py','install_codex.py','codex_smoke.py','runtime/finalize.py',)
EXPECTED_VERSION = 29
EXPECTED_RENDERER_REVISION = 3


def replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.update-tmp')
    temporary.write_bytes(data)
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def update(source, target, verify=None):
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
    original = {name: (target / name).read_bytes() if (target / name).exists() else None for name in (*FILES,'tools/codex/verified.json')}
    command = ['systemctl', '--user']
    # Check before downloads, then recheck under the write lock immediately
    # before stopping the worker. A download must not block job polling.
    with sqlite3.connect(db_path, timeout=15) as db:
        if db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]:
            raise RuntimeError('Zlecenie jest jeszcze aktywne. Poczekaj na wynik lub anuluj je na stronie, potem ponow aktualizacje.')
    from install_codex import install as install_codex
    install_codex(target/'tools'/'codex')
    try:
        setup_runtime()
    except RuntimeUnavailable as error:
        raise RuntimeError('Kontener Blendera nadal nie startuje. Nie zmieniono programu. Pokaz ten komunikat: ' + error.detail) from None
    # Hold the queue lock until the HTTP worker stops.
    with sqlite3.connect(db_path, timeout=15) as db:
        db.execute('BEGIN IMMEDIATE')
        busy = db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]
        if busy:
            raise RuntimeError('Zlecenie jest jeszcze aktywne. Poczekaj na wynik lub anuluj je na stronie, potem ponow aktualizacje.')
        subprocess.run(command + ['stop', 'froge-worker.service'], check=True, timeout=30)
    try:
        backup = state / 'code-backups' / str(time.time_ns())
        backup.mkdir(parents=True, mode=0o700)
        for name, data in original.items():
            if data is not None:
                replace(backup / name, data)
        for name, data in incoming.items():
            replace(target / name, data)
        print('Sprawdzam Codex i Blender MCP przed przyjeciem aktualizacji. Bez platnego API.',flush=True)
        subprocess.run([sys.executable,str(target/'codex_smoke.py'),'--build'],check=True,timeout=240)
        if verify is not None:
            verify(target)
        subprocess.run(command + ['start', 'froge-worker.service'], check=True, timeout=30)
        # Use the existing credential locally; it is never printed or changed.
        token = json.loads(config_path.read_text())['token']
        request = urllib.request.Request('http://127.0.0.1:8765/v1/health', headers={'Authorization': 'Bearer ' + token})
        for _ in range(20):
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    health = json.loads(response.read(10000))
                    if health.get('connectorVersion') == EXPECTED_VERSION and health.get('executionEngine') == 'codex-mcp' and health.get('freeformGeometryRevision') == 1 and health.get('photoProjectionRevision') == 1 and health.get('instructionsRevision') == 1 and health.get('astraPhotoRevision') == 1 and health.get('rendererRevision') == EXPECTED_RENDERER_REVISION and health.get('portraitRevision') == 2 and health.get('characterStandard') == 20 and health.get('coutureRevision') == 2 and health.get('referenceQualityRevision') == 1 and health.get('materialQualityRevision') == 2 and health.get('interchangeRevision') == 2 and health.get('portraitGeometryRevision') == 2 and health.get('registeredReferenceRevision') == 1:
                        print('FROGE_UPDATE_OK')
                        print('Froge v29: sprawdzono Codex, argumenty MCP, rzeczywista budowe i eksport. Rozroznione limity zlecenia i OpenAI. Modele i klucz zachowane.')
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
        print('FROGE_ROLLBACK_CODE_RESTORED: przywrocono poprzedni kod i zapis weryfikacji; pliki modeli i polaczenie zachowane.',flush=True)
        raise


if __name__ == '__main__':
    try:
        if pwd.getpwuid(os.getuid()).pw_name != 'opc':
            raise RuntimeError('Uruchom aktualizacje na serwerze Oracle jako opc.')
        update(Path(__file__).resolve().parent, Path.home() / 'froge-connector')
    except Exception as error:
        print('FROGE_UPDATE_ERROR: ' + str(error))
        raise SystemExit(1)
