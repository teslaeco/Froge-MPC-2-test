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
from code_policy import CodePolicyError, StreamPolicyGuard, extract_code, prepare_code, repair_instruction, validate_code
from ai_stream import stream_chat
import openai_provider
from ai_stream import OpenAIServiceError
from runtime_check import IMAGE, sandbox_options, verify_runtime
from runtime.scene_contract import SCHEMA, PROMPT, parse_scene

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
JOBS = STATE / 'jobs'
CONFIG = STATE / 'config.json'
MODEL = os.environ.get('FROGE_AI_MODEL', 'qwen2.5-coder:7b')
CONNECTOR_VERSION = 7
AI_TIME_LIMIT = 180
OLLAMA = 'http://127.0.0.1:11434'
UUID = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
LOCK = threading.RLock()
WAKE = threading.Event()
CANCEL = {}
RUNNING = set()
PAIR_ATTEMPTS = []
SYSTEM = PROMPT

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
    selected = ai_settings()
    if selected.get('provider') == 'openai':
        ready = bool(selected.get('api_key'))
        return {'ready': ready, 'provider': 'openai', 'model': openai_provider.MODEL,
                'detail': 'OpenAI Astra jest polaczone. Blender wykona sprawdzony plan sceny.' if ready else 'Podlacz klucz OpenAI API w ustawieniach.',
                'connectorVersion': CONNECTOR_VERSION}
    try:
        tags = ollama_json('/api/tags').get('models', [])
        ready = any(m.get('name') == MODEL or m.get('model') == MODEL for m in tags)
        detail = 'Lokalny Qwen na CPU. Ten tryb moze byc wolny; Astra wymaga podlaczenia OpenAI API.' if ready else 'Pobieranie lub przygotowanie lokalnego modelu AI. Pierwsze uruchomienie trwa dluzej.'
        pull = STATE / 'pull-status.json'
        if not ready and pull.exists():
            detail = json.loads(pull.read_text()).get('detail', detail)
        return {'ready': ready, 'provider': 'ollama', 'model': MODEL, 'detail': detail, 'connectorVersion': CONNECTOR_VERSION}
    except Exception:
        return {'ready': False, 'provider': 'ollama', 'model': MODEL, 'detail': 'Lokalne AI jeszcze sie uruchamia. Sprawdz ponownie za chwile.', 'connectorVersion': CONNECTOR_VERSION}

def ai_settings():
    path = STATE / 'ai-provider.json'
    return json.loads(path.read_text()) if path.exists() else {'provider': 'ollama'}

def ai_busy():
    with database() as db:
        return bool(RUNNING or db.execute("SELECT COUNT(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0])

def configure_ai(data):
    provider = data.get('provider')
    if provider not in ('openai', 'ollama'):
        raise ValueError('Nieprawidlowy dostawca AI.')
    with LOCK:
        if ai_busy():
            return False
        selected = ai_settings()
    if provider == 'openai':
        # Model access is checked without sending a paid generation request.
        supplied = data.get('apiKey') or selected.get('api_key')
        selected['api_key'] = openai_provider.verify_key(supplied)
    selected['provider'] = provider
    with LOCK:
        if ai_busy():
            return False
        write_json(STATE / 'ai-provider.json', selected)
    return True

def generate_code(messages, job_id, cancelled, deadline=None, attempt=1, selected=None):
    selected = selected or ai_settings()
    is_openai = selected.get('provider') == 'openai'
    payload = {'model': MODEL, 'messages': messages, 'stream': True, 'keep_alive': '5m', 'format': SCHEMA,
               'options': {'temperature': 0.2 if attempt == 1 else 0.1, 'num_ctx': 8192, 'num_predict': 3000, 'num_thread': 2}}
    def progress(characters, elapsed, silent):
        clock = '%d:%02d' % (int(elapsed) // 60, int(elapsed) % 60)
        prefix = 'Proba %d/2. Czas tej proby: %s. ' % (attempt, clock)
        if characters:
            detail = 'AI projektuje scene: %d znakow. Ostatnie dane %d s temu.' % (characters, silent)
        else:
            detail = 'OpenAI Astra analizuje opis; oczekiwanie na instrukcje.' if is_openai else 'AI laduje model lub analizuje opis; oczekiwanie na pierwsze instrukcje.'
        status(job_id, 'generating', prefix + detail)
    remaining = AI_TIME_LIMIT if deadline is None else deadline - time.monotonic()
    if is_openai:
        def usage(record):
            write_json(JOBS / job_id / ('ai-attempt-%d-usage.json' % attempt), {'model': openai_provider.MODEL, **record})
        return openai_provider.generate(messages, selected['api_key'], cancelled, progress,
                                        remaining, None, usage, schema=SCHEMA)
    return stream_chat(OLLAMA + '/api/chat', payload, cancelled, progress, timeout=remaining)

def blender_command(job_id, folder):
    return ['podman', 'run', '--rm', '--pull=never', '--name', 'froge-job-' + job_id] + sandbox_options() + [
            '-v', str(ROOT / 'runtime') + ':/runner:ro,Z', '-v', str(folder) + ':/work:rw,Z',
            IMAGE, '--background', '--factory-startup', '--threads', '2', '--python-exit-code', '1',
            '--python', '/runner/run.py']

def run_blender(job_id, folder, cancelled, timeout=600):
    log_path = folder / 'blender.log'
    with log_path.open('wb') as log:
        process = subprocess.Popen(blender_command(job_id, folder), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        while process.poll() is None:
            if cancelled.wait(1) or time.monotonic() - started > timeout:
                subprocess.run(['podman', 'kill', 'froge-job-' + job_id], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                process.wait(timeout=20)
                if cancelled.is_set():
                    raise InterruptedError('Zlecenie anulowane.')
                raise TimeoutError('Blender przekroczyl limit %d minut. Uprosc opis.' % (timeout // 60))
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
            RUNNING.add(job['id'])
            cancelled = CANCEL.setdefault(job['id'], threading.Event())
            db.execute("UPDATE jobs SET state='generating',detail='AI analizuje opis…' WHERE id=?", (job['id'],))
        folder = JOBS / job['id']
        folder.mkdir(mode=0o700, exist_ok=True)
        messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': job['prompt']}]
        code = ''
        started = time.monotonic()
        ai_seconds = blender_seconds = 0
        try:
            status(job['id'], 'generating', 'Sprawdzam, czy Blender moze uruchomic model…')
            verify_runtime()
            selected = ai_settings()
            is_openai = selected.get('provider') == 'openai'
            saved_script = folder / 'saved-script.py'
            reuse = saved_script.is_file()
            deadline = started + AI_TIME_LIMIT
            write_json(folder / 'provider.json', {'provider': 'saved-script' if reuse else selected.get('provider'), 'model': None if reuse else openai_provider.MODEL if is_openai else MODEL})
            for attempt in range(1 if reuse else 2):
                try:
                    if reuse:
                        code = saved_script.read_text(encoding='utf-8')
                    else:
                        phase_started = time.monotonic()
                        try:
                            code = generate_code(messages, job['id'], cancelled, deadline, attempt + 1, selected)
                        finally:
                            ai_seconds += time.monotonic() - phase_started
                    draft = folder / ('attempt-%d.%s' % (attempt + 1, 'py' if reuse else 'json'))
                    draft.write_text(code, encoding='utf-8')
                    os.chmod(draft, 0o600)
                    if reuse:
                        code, replaced = prepare_code(code)
                        write_json(folder / ('attempt-%d-helpers.json' % (attempt + 1)), {'restored_helpers': replaced})
                        (folder / 'generate.py').write_text(code, encoding='utf-8')
                    else:
                        scene = parse_scene(code)
                        write_json(folder / 'scene.json', scene)
                    if cancelled.is_set():
                        raise InterruptedError('Zlecenie anulowane.')
                    status(job['id'], 'building', 'Plan sprawdzony. Blender buduje geometrie i zapisuje GLB…')
                    phase_started = time.monotonic()
                    try:
                        run_blender(job['id'], folder, cancelled, timeout=180)
                    finally:
                        blender_seconds += time.monotonic() - phase_started
                    elapsed = time.monotonic() - started
                    write_json(folder / 'timing.json', {'total_seconds': round(elapsed, 2), 'ai_seconds': round(ai_seconds, 2), 'blender_seconds': round(blender_seconds, 2)})
                    detail = ('Model gotowy w %.1f s. Wykorzystano zapisany skrypt, bez nowego zapytania do AI.' % elapsed if reuse else 'Model gotowy w %.1f s. Instrukcje AI: %.1f s; Blender: %.1f s. Zapisano GLB z materialami.' % (elapsed, ai_seconds, blender_seconds))
                    status(job['id'], 'succeeded', detail)
                    break
                except (ValueError, SyntaxError) as error:
                    if isinstance(error, CodePolicyError) and error.partial_code:
                        draft = folder / ('attempt-%d.rejected.py' % (attempt + 1))
                        draft.write_text(error.partial_code, encoding='utf-8')
                        os.chmod(draft, 0o600)
                    write_json(folder / ('attempt-%d-error.json' % (attempt + 1)), {'error': str(error)[-2500:]})
                    if attempt or reuse:
                        raise
                    status(job['id'], 'retrying', 'Pierwsza proba nie przeszla kontroli. AI poprawia instrukcje…')
                    if code:
                        messages.append({'role': 'assistant', 'content': code[-20000:]})
                    messages.append({'role': 'user', 'content': 'Return a complete corrected scene JSON for the ORIGINAL request. Preserve its requested features. Fix this validation/build error: ' + str(error)[-1800:]})
        except InterruptedError:
            status(job['id'], 'cancelled', 'Zlecenie anulowane.')
        except TimeoutError:
            status(job['id'], 'failed', 'Przekroczono limit czasu. Nie uruchamiam kolejnej dlugiej proby. Jesli wybrano Qwen, podlacz OpenAI Astra w ustawieniach.')
        except Exception as error:
            detail = str(error)
            if isinstance(error, urllib.error.URLError):
                detail = 'Brak odpowiedzi lokalnego AI. Sprawdz usluge Ollama i sprobuj ponownie.'
            status(job['id'], 'failed', detail[-600:])
        finally:
            with LOCK:
                CANCEL.pop(job['id'], None)
                RUNNING.discard(job['id'])

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
            if write and self.path == '/v1/ai':
                if not configure_ai(self.input()):
                    return self.send_json({'error': 'Anuluj aktywne zlecenie i poczekaj na zatrzymanie, zanim zmienisz AI.'}, 409)
                return self.send_json({'saved': True})
            if write and self.path == '/v1/jobs':
                data = self.input()
                job_id, prompt = data.get('id'), data.get('prompt')
                source_id = data.get('sourceJobId')
                if source_id is not None and (not isinstance(source_id, str) or not UUID.fullmatch(source_id) or source_id == job_id):
                    raise ValueError('Nieprawidlowe zlecenie zrodlowe.')
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
                    if source_id is None and not health()['ready']:
                        return self.send_json({'error': 'Wybrane AI nie jest jeszcze gotowe. Sprawdz ustawienia.'}, 409)
                    if shutil.disk_usage(STATE).free < 2 * 1024**3:
                        return self.send_json({'error': 'Na serwerze zostalo mniej niz 2 GB wolnego miejsca.'}, 409)
                    if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] >= 300:
                        return self.send_json({'error': 'Osiagnieto limit 300 zlecen. Zarchiwizuj modele na serwerze przed dalsza praca.'}, 409)
                    if (JOBS / job_id).exists():
                        return self.send_json({'error': 'Identyfikator zlecenia jest juz zajety. Sprobuj ponownie.'}, 409)
                    if source_id is not None:
                        source = db.execute('SELECT * FROM jobs WHERE id=?', (source_id,)).fetchone()
                        source_path = JOBS / source_id / 'generate.py'
                        if not source or source['state'] != 'failed' or source['prompt'] != prompt.strip() or not source_path.is_file():
                            return self.send_json({'error': 'Brak zapisanego skryptu dla tego nieudanego zlecenia.'}, 409)
                        if source_path.stat().st_size > 60000:
                            return self.send_json({'error': 'Zapisany skrypt przekracza limit rozmiaru.'}, 409)
                        saved_code = source_path.read_text(encoding='utf-8')
                        try:
                            prepare_code(saved_code)
                        except (ValueError, SyntaxError):
                            return self.send_json({'error': 'Zapisany skrypt wymaga nowych instrukcji AI; nie zostal uruchomiony.'}, 409)
                        destination = JOBS / job_id
                        destination.mkdir(mode=0o700)
                        (destination / 'saved-script.py').write_text(saved_code, encoding='utf-8')
                        os.chmod(destination / 'saved-script.py', 0o600)
                        write_json(destination / 'source-job.json', {'id': source_id})
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
        except OpenAIServiceError as error:
            self.send_json({'error': str(error)}, 422)
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
