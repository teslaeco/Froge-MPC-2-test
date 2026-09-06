"""Private Froge model worker. Python standard library; binds to localhost only."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import struct
import subprocess
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from code_policy import extract_code, validate_code

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
JOBS = STATE / 'jobs'
CONFIG = STATE / 'config.json'
MODEL = os.environ.get('FROGE_AI_MODEL', 'qwen2.5-coder:7b')
OLLAMA = 'http://127.0.0.1:11434'
IMAGE = 'localhost/froge-blender:local'
UUID = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
LOCK = threading.RLock()
WAKE = threading.Event()
CANCEL = {}
PAIR_ATTEMPTS = []
SYSTEM = '''You are a Blender 4.3 procedural 3D artist. Return ONLY one complete Python script.
Create a NEW detailed mesh that matches the user's exact description, not a generic example.
The scene starts EMPTY. Use metres and Z up. Make a complete three-dimensional asset with
recognizable silhouette, meaningful details, smooth organic forms or precise mechanical parts,
and suitable colours. For a tree distinguish trunk, tapered curved branches, crown and leaves.
For other objects design their own shapes; there is no fixed list of allowed objects.
Allowed imports: bpy, math, random, mathutils. Never access files, OS, network, wm, render,
handlers, drivers or other applications. Do not export or save; the host does that afterward.
Available helpers already in scope (do NOT import them):
make_material(name, rgb, pattern='plain', roughness=0.7, metallic=0.0) -> material.
  rgb is a 3-number tuple from 0 to 1. Patterns: plain, bark, wood, leaf, stone, fabric, metal.
  The helper creates a real packed 512px UV texture, which is included in the GLB.
mesh_object(name, vertices, faces, material) -> mesh object. vertices=[(x,y,z),...], faces=index tuples.
tube(name, points, radii, material, sides=12) -> capped curved tapered tube. len(radii)=len(points).
ellipsoid(name, center, scale, material, subdivisions=2) -> smooth mesh object.
join_meshes(objects, name) -> combine mesh objects. Use it for many small leaves or details.
You may also use ordinary bpy mesh operators. Reuse materials. Use custom meshes for shapes
that cannot be represented well by spheres or cubes. Organic foliage should have distinct
leaf-shaped surfaces and branching, not just a single green sphere. Use loops and functions
to construct detail efficiently. Never define classes or use introspection.
Limits: 256 objects (join small repeated parts), 200000 vertices, 400000 triangles,
at most 8 materials/images, 60KB Python source. Keep every axis of the whole asset nonzero.
Do not use subdivision modifiers with levels greater than 2. Deterministic random seed allowed.
Do not call make_material with a hexadecimal colour string; use an RGB tuple.
Return code only, without explanations or markdown prose.'''

def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.chmod(temporary, 0o600)
    temporary.replace(path)

def initialize():
    STATE.mkdir(mode=0o700, exist_ok=True)
    JOBS.mkdir(mode=0o700, exist_ok=True)
    if not CONFIG.exists():
        write_json(CONFIG, {'token': secrets.token_urlsafe(48), 'code': secrets.token_hex(16), 'expires': time.time() + 3600, 'client': None})
    with database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, prompt TEXT NOT NULL, state TEXT NOT NULL, detail TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL)')

def database():
    db = sqlite3.connect(STATE / 'jobs.sqlite', timeout=15)
    db.row_factory = sqlite3.Row
    return db

def status(job_id, state, detail):
    with LOCK, database() as db:
        db.execute('UPDATE jobs SET state=?,detail=?,updated=? WHERE id=? AND state!=?', (state, detail[:600], time.time(), job_id, 'cancelled'))

def ollama_json(path, payload=None, timeout=10):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(OLLAMA + path, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read(2 * 1024 * 1024))

def health():
    try:
        tags = ollama_json('/api/tags').get('models', [])
        ready = any(m.get('name') == MODEL or m.get('model') == MODEL for m in tags)
        detail = 'AI i Blender sa gotowe.' if ready else 'Pobieranie lub przygotowanie lokalnego modelu AI. Pierwsze uruchomienie trwa dluzej.'
        pull = STATE / 'pull-status.json'
        if not ready and pull.exists():
            detail = json.loads(pull.read_text()).get('detail', detail)
        return {'ready': ready, 'model': MODEL, 'detail': detail}
    except Exception:
        return {'ready': False, 'model': MODEL, 'detail': 'Lokalne AI jeszcze sie uruchamia. Sprawdz ponownie za chwile.'}

def generate_code(messages, job_id, cancelled):
    payload = {'model': MODEL, 'messages': messages, 'stream': True, 'keep_alive': 0,
               'options': {'temperature': 0.35, 'num_ctx': 8192, 'num_predict': 5000, 'num_thread': 2}}
    req = urllib.request.Request(OLLAMA + '/api/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    text = ''
    started = time.monotonic()
    last_update = 0
    with urllib.request.urlopen(req, timeout=180) as response:
        for raw in response:
            if cancelled.is_set():
                raise InterruptedError('Zlecenie anulowane.')
            if time.monotonic() - started > 1800:
                raise TimeoutError('AI przekroczylo limit 30 minut. Uprosc opis i sprobuj ponownie.')
            if len(raw) > 200000:
                raise ValueError('Nieprawidlowa odpowiedz AI.')
            item = json.loads(raw)
            if item.get('error'):
                raise ValueError(str(item['error'])[:500])
            text += item.get('message', {}).get('content', '')
            if len(text.encode()) > 80000:
                raise ValueError('AI zwrocilo zbyt dlugi skrypt.')
            if time.monotonic() - last_update > 8:
                status(job_id, 'generating', 'AI uklada geometrie i materialy: odebrano %d znakow instrukcji.' % len(text))
                last_update = time.monotonic()
            if item.get('done'):
                if item.get('done_reason') == 'length':
                    raise ValueError('Skrypt AI zostal uciety. Uprosc model i uzyj petli zamiast dlugich list.')
                break
    return extract_code(text)

def blender_command(job_id, folder):
    return ['podman', 'run', '--rm', '--pull=never', '--name', 'froge-job-' + job_id,
            '--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--userns=keep-id', '--memory=4g', '--memory-swap=4g', '--cpus=2', '--pids-limit=256',
            '--tmpfs', '/tmp:rw,size=256m', '--shm-size=128m', '-e', 'HOME=/tmp',
            '-v', str(ROOT / 'runtime') + ':/runner:ro,Z', '-v', str(folder) + ':/work:rw,Z',
            IMAGE, '--background', '--factory-startup', '--threads', '2', '--python-exit-code', '1',
            '--python', '/runner/run.py']

def run_blender(job_id, folder, cancelled):
    log_path = folder / 'blender.log'
    with log_path.open('wb') as log:
        process = subprocess.Popen(blender_command(job_id, folder), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        while process.poll() is None:
            if cancelled.wait(1) or time.monotonic() - started > 600:
                subprocess.run(['podman', 'kill', 'froge-job-' + job_id], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                process.wait(timeout=20)
                if cancelled.is_set():
                    raise InterruptedError('Zlecenie anulowane.')
                raise TimeoutError('Blender przekroczyl limit 10 minut. Uprosc opis.')
        if process.returncode:
            tail = log_path.read_bytes()[-3500:].decode('utf-8', errors='replace')
            raise ValueError('Blender nie skonczyl modelu: ' + tail)
    model = folder / 'model.glb'
    if not model.exists() or not 20 <= model.stat().st_size <= 12 * 1024 * 1024:
        raise ValueError('Model jest pusty albo przekracza limit 12 MB.')
    with model.open('rb') as file:
        magic, version, length = struct.unpack('<III', file.read(12))
    if magic != 0x46546C67 or version != 2 or length != model.stat().st_size:
        raise ValueError('Blender nie zapisal prawidlowego GLB.')

def worker():
    while True:
        WAKE.wait(2)
        WAKE.clear()
        with LOCK, database() as db:
            row = db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if not row:
                continue
            job = dict(row)
            cancelled = CANCEL.setdefault(job['id'], threading.Event())
            db.execute("UPDATE jobs SET state='generating',detail='AI analizuje opis…' WHERE id=?", (job['id'],))
        folder = JOBS / job['id']
        folder.mkdir(mode=0o700, exist_ok=True)
        messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': job['prompt']}]
        code = ''
        try:
            for attempt in range(2):
                try:
                    code = generate_code(messages, job['id'], cancelled)
                    validate_code(code)
                    (folder / 'generate.py').write_text(code, encoding='utf-8')
                    if cancelled.is_set():
                        raise InterruptedError('Zlecenie anulowane.')
                    status(job['id'], 'building', 'Blender tworzy siatke, tekstury UV i plik GLB…')
                    run_blender(job['id'], folder, cancelled)
                    status(job['id'], 'succeeded', 'Nowy model gotowy. Zapisano geometrie i materialy w GLB.')
                    break
                except (ValueError, SyntaxError) as error:
                    if attempt:
                        raise
                    status(job['id'], 'retrying', 'Pierwsza proba nie przeszla kontroli. AI poprawia instrukcje…')
                    if code:
                        messages.append({'role': 'assistant', 'content': code[-20000:]})
                    messages.append({'role': 'user', 'content': 'Fix this error. Return a COMPLETE corrected script, not a patch. Keep the original requested object. Error: ' + str(error)[-2500:]})
        except InterruptedError:
            status(job['id'], 'cancelled', 'Zlecenie anulowane.')
        except Exception as error:
            detail = str(error)
            if isinstance(error, urllib.error.URLError):
                detail = 'Brak odpowiedzi lokalnego AI. Sprawdz usluge Ollama i sprobuj ponownie.'
            status(job['id'], 'failed', detail[-600:])
        finally:
            CANCEL.pop(job['id'], None)

class Handler(BaseHTTPRequestHandler):
    server_version = 'Froge/1'
    def log_message(self, *_):
        pass  # Tokens, prompts and pairing codes must not enter access logs.

    def send_json(self, value, status_code=200):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def input(self):
        if not self.headers.get('Content-Type', '').startswith('application/json'):
            raise ValueError('Wymagany format JSON.')
        size = int(self.headers.get('Content-Length', '0'))
        if size < 0 or size > 12000:
            raise ValueError('Zbyt duze zadanie.')
        self.connection.settimeout(15)
        data = json.loads(self.rfile.read(size))
        if not isinstance(data, dict):
            raise ValueError('Nieprawidlowy format zadania.')
        return data

    def authorized(self, token):
        expected = ('Bearer ' + token).encode()
        return hmac.compare_digest(self.headers.get('Authorization', '').encode(), expected)

    def do_GET(self):
        self.handle_request(False)

    def do_POST(self):
        self.handle_request(True)

    def handle_request(self, write):
        try:
            config = json.loads(CONFIG.read_text())
            if write and self.path == '/v1/pair':
                with LOCK:
                    now = time.time()
                    PAIR_ATTEMPTS[:] = [t for t in PAIR_ATTEMPTS if t > now - 60]
                    if len(PAIR_ATTEMPTS) >= 10:
                        return self.send_json({'error': 'Za duzo prob polaczenia. Odczekaj minute.'}, 429)
                    PAIR_ATTEMPTS.append(now)
                    config = json.loads(CONFIG.read_text())
                    if now > config['expires'] or not self.authorized(config['code']):
                        return self.send_json({'error': 'Kod wygasl lub jest nieprawidlowy. Uruchom polecenie pokazujace nowy kod.'}, 401)
                    data = self.input()
                    client = data.get('client')
                    if not isinstance(client, str) or not 1 <= len(client) <= 256:
                        raise ValueError('Nieprawidlowy identyfikator klienta.')
                    if config.get('client') not in (None, client):
                        return self.send_json({'error': 'Ten kod przypisano juz do innego konta.'}, 409)
                    config['client'] = client
                    config['expires'] = min(config['expires'], now + 600)
                    write_json(CONFIG, config)
                    return self.send_json({'token': config['token']})
            if not self.authorized(config['token']):
                return self.send_json({'error': 'Wymagane polaczenie z kontem Froge.'}, 401)
            if not write and self.path == '/v1/health':
                return self.send_json(health())
            if write and self.path == '/v1/jobs':
                data = self.input()
                job_id, prompt = data.get('id'), data.get('prompt')
                if not isinstance(job_id, str) or not UUID.fullmatch(job_id) or not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
                    raise ValueError('Nieprawidlowy opis lub identyfikator zlecenia.')
                with LOCK, database() as db:
                    prior = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
                    if prior:
                        if prior['prompt'] != prompt.strip():
                            return self.send_json({'error': 'Identyfikator dotyczy innego opisu.'}, 409)
                        return self.send_json(dict(prior))
                    if db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]:
                        return self.send_json({'error': 'Serwer wykonuje poprzedni model. Poczekaj na wynik lub anuluj tamto zlecenie.'}, 409)
                    if not health()['ready']:
                        return self.send_json({'error': 'Lokalne AI nie jest jeszcze gotowe. Poczekaj na zakonczenie pobierania modelu.'}, 409)
                    if shutil.disk_usage(STATE).free < 2 * 1024**3:
                        return self.send_json({'error': 'Na serwerze zostalo mniej niz 2 GB wolnego miejsca.'}, 409)
                    if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] >= 300:
                        return self.send_json({'error': 'Osiagnieto limit 300 zlecen. Zarchiwizuj modele na serwerze przed dalsza praca.'}, 409)
                    now = time.time()
                    db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?)', (job_id, prompt.strip(), 'queued', 'Opis przyjety.', now, now))
                WAKE.set()
                return self.send_json({'id': job_id, 'state': 'queued'}, 202)
            match = re.fullmatch(r'/v1/jobs/([a-f0-9-]{36})(?:/(model|cancel))?', self.path)
            if not match or not UUID.fullmatch(match[1]):
                return self.send_json({'error': 'Nie znaleziono funkcji.'}, 404)
            job_id, action = match.groups()
            with database() as db:
                row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                return self.send_json({'error': 'Serwer nie ma tego zlecenia. Wyslij opis ponownie.'}, 404)
            if write and action == 'cancel':
                with LOCK, database() as db:
                    db.execute("UPDATE jobs SET state='cancelled',detail='Zlecenie anulowane.',updated=? WHERE id=? AND state NOT IN ('succeeded','failed','cancelled')", (time.time(), job_id))
                    CANCEL.setdefault(job_id, threading.Event()).set()
                return self.send_json({'cancelled': True})
            if write:
                return self.send_json({'error': 'Niedozwolona metoda.'}, 405)
            if action == 'model':
                path = JOBS / job_id / 'model.glb'
                if row['state'] != 'succeeded' or not path.is_file() or path.is_symlink():
                    return self.send_json({'error': 'Model nie jest jeszcze gotowy.'}, 409)
                size = path.stat().st_size
                if not 20 <= size <= 12 * 1024**2:
                    return self.send_json({'error': 'Plik modelu przekracza limit 12 MB.'}, 413)
                self.send_response(200)
                self.send_header('Content-Type', 'model/gltf-binary')
                self.send_header('Content-Length', str(size))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                with path.open('rb') as file:
                    shutil.copyfileobj(file, self.wfile, 65536)
                return
            if action:
                return self.send_json({'error': 'Nie znaleziono funkcji.'}, 404)
            return self.send_json(dict(row))
        except (ValueError, TypeError, KeyError):
            self.send_json({'error': 'Nieprawidlowe dane zadania.'}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.send_json({'error': 'Blad serwera. Sprawdz dziennik uslugi Froge.'}, 500)

def pair_info():
    with LOCK:
        config = json.loads(CONFIG.read_text())
        config.update(code=secrets.token_hex(16), expires=time.time() + 3600, client=None)
        write_json(CONFIG, config)
    log = STATE / 'tunnel.log'
    urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log.read_text(errors='replace') if log.exists() else '')
    print('\nADRES SERWERA: ' + (urls[-1] if urls else 'Tunel jeszcze sie uruchamia; wywolaj polecenie ponownie.'))
    print('KOD POLACZENIA: ' + config['code'])
    print('Wklej adres i kod w ustawieniach Blendera na swojej stronie Froge. Kod jest wazny przez godzine.\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pair-info', action='store_true')
    args = parser.parse_args()
    initialize()
    if args.pair_info:
        pair_info()
    else:
        with database() as db:
            db.execute("UPDATE jobs SET state='failed',detail='Serwer uruchomil sie ponownie. Wyslij opis jeszcze raz.' WHERE state NOT IN ('succeeded','failed','cancelled')")
        threading.Thread(target=worker, daemon=True).start()
        ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
