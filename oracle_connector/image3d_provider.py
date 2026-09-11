"""Image-conditioned Meshy tasks. No scene templates and no automatic paid retries.

Credentials stay on the worker; Blender only receives downloaded assets.
API contract checked against docs.meshy.ai on 2026-09-11.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.meshy.ai/openapi/v1/'
MODEL = 'meshy-7'
MAX_ASSET_BYTES = 256 * 1024**2
MAX_TOTAL_BYTES = 768 * 1024**2
TASK_ID = re.compile(r'^[A-Za-z0-9_-]{1,128}$')
MISSING_CONNECTION = 'Podlacz Meshy w ustawieniach Zdjecia -> 3D. Sam klucz OpenAI nie uruchamia rekonstrukcji ze zdjecia.'


class Image3DError(ValueError):
    pass


class RequestError(Image3DError):
    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = retryable


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, api_key, payload=None):
    if not re.fullmatch(r'(image-to-3d|multi-image-to-3d)(/[A-Za-z0-9_-]+|\?page_size=1)?', path):
        raise Image3DError('Nieprawidlowa operacja generatora.')
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=45) as response:
            raw = response.read(4 * 1024**2 + 1)
            if len(raw) > 4 * 1024**2:
                raise Image3DError('Zbyt duza odpowiedz generatora.')
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        # Never echo provider responses: they may include images, keys or URLs.
        messages = {400: 'Meshy odrzucilo parametry zdjecia.',
                    401: 'Klucz Meshy jest nieprawidlowy.',
                    402: 'Na koncie Meshy brakuje kredytow API.',
                    403: 'Klucz Meshy nie ma dostepu do tej operacji.',
                    404: 'Meshy nie znalazlo zapisanego zadania.',
                    429: 'Limit zapytan Meshy; oczekiwanie na dostepnosc.'}
        raise RequestError(messages.get(error.code, 'Meshy jest chwilowo niedostepne.'),
                           retryable=error.code == 429 or error.code >= 500) from None
    except (OSError, ValueError) as error:
        if isinstance(error, Image3DError):
            raise
        raise RequestError('Nie otrzymano poprawnej odpowiedzi Meshy.', retryable=True) from None


def verify_key(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,512}', value.strip()):
        raise Image3DError('Wpisz pelny klucz API Meshy w bezpiecznym polu ustawien.')
    value = value.strip()
    request('GET', 'image-to-3d?page_size=1', value)
    return value


def settings(state):
    path = Path(state) / 'image-provider.json'
    if not path.is_file():
        return {'provider': 'meshy', 'texture_resolution': '8k'}
    return json.loads(path.read_text())


def capability(state):
    selected = settings(state)
    configured = selected.get('provider') == 'meshy' and bool(selected.get('api_key'))
    return {'image3dRevision': 1, 'image3dReady': configured, 'image3dProvider': 'meshy',
            'image3dModel': MODEL, 'image3dTextureResolution': selected.get('texture_resolution', '8k'),
            'image3dUltra': True, 'image3dDetail':
            'Meshy 7 Ultra: geometria i tekstury ze zdjec, eksport FBX.' if configured else MISSING_CONNECTION}


def make_payload(photos, selected):
    if not 1 <= len(photos) <= 4:
        raise Image3DError('Dodaj od jednego do czterech ujec tej samej postaci lub obiektu.')
    subjects = {p.get('subject', '').strip().casefold() for p in photos if p.get('subject', '').strip()}
    if len(subjects) > 1:
        raise Image3DError('Te zdjecia maja rozne oznaczenia postaci. Generuj kazda osobe w osobnym zleceniu; kilka ujec sluzy jednej postaci.')
    resolution = selected.get('texture_resolution', '8k')
    if resolution not in ('4k', '8k'):
        raise Image3DError('Wybierz tekstury 4K lub 8K.')
    # A labelled front takes precedence; preserve order otherwise. Never send
    # face landmarks, a composition signature or another person's reference.
    ordered = sorted(enumerate(photos), key=lambda p: (p[1]['view'] != 'front', p[0]))
    images = ['data:image/jpeg;base64,' + base64.b64encode(p['bytes']).decode('ascii') for _, p in ordered]
    payload = {'model_type': 'standard', 'ai_model': MODEL, 'ultra_mode': True,
               'should_remesh': False, 'should_texture': True, 'enable_pbr': True,
               'texture_resolution': resolution, 'image_enhancement': False,
               'pose_mode': '', 'auto_size': False, 'target_formats': ['glb']}
    if len(images) == 1:
        payload['image_url'] = images[0]
        payload['texture_image_url'] = images[0]
        endpoint = 'image-to-3d'
    else:
        payload['image_urls'] = images
        payload['texture_image_urls'] = images
        endpoint = 'multi-image-to-3d'
    return endpoint, payload


def file_record(path, folder):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'path': path.relative_to(folder).as_posix(), 'bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def asset_url(value):
    if not isinstance(value, str):
        raise Image3DError('Generator nie zwrocil pliku modelu.')
    url = urllib.parse.urlsplit(value)
    if url.scheme != 'https' or url.hostname != 'assets.meshy.ai' or url.port not in (None, 443) or url.username or url.password or url.fragment:
        raise Image3DError('Nieprawidlowy adres pliku generatora.')
    return value


def download(url, path, cancelled):
    url = asset_url(url)
    temporary = path.with_suffix('.part')
    try:
        # No API Authorization header on asset requests and no redirects.
        with urllib.request.build_opener(NoRedirect()).open(url, timeout=45) as response, temporary.open('wb') as output:
            os.chmod(temporary, 0o600)
            size = 0
            if int(response.headers.get('Content-Length', '0')) > MAX_ASSET_BYTES:
                raise Image3DError('Plik przekracza limit 256 MiB; oryginal pozostaje na koncie Meshy.')
            while True:
                if cancelled.is_set():
                    raise InterruptedError()
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ASSET_BYTES:
                    raise Image3DError('Plik przekracza limit 256 MiB.')
                output.write(chunk)
            if size < 20:
                raise Image3DError('Generator zwrocil pusty plik.')
        temporary.replace(path)
    except (OSError, ValueError) as error:
        if isinstance(error, (Image3DError, InterruptedError)):
            raise
        raise Image3DError('Pobieranie pliku zostalo przerwane. Wznow odbior zapisanego zadania, bez ponownego generowania.') from None
    finally:
        temporary.unlink(missing_ok=True)


def validate_glb(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise Image3DError('Niepelny plik GLB.')
        magic, version, length, json_size, kind = struct.unpack('<5I', header)
        if magic != 0x46546C67 or version != 2 or length != size or kind != 0x4E4F534A or not 2 <= json_size <= min(8 * 1024**2, size - 20):
            raise Image3DError('Nieprawidlowy plik GLB generatora.')
        try:
            data = json.loads(stream.read(json_size))
        except (ValueError, UnicodeError):
            raise Image3DError('Nieprawidlowy opis geometrii GLB.') from None
    if not isinstance(data, dict) or not data.get('meshes') or not data.get('images') or not data.get('textures'):
        raise Image3DError('Generator nie zwrocil geometrii z teksturami.')
    # A remote asset must not instruct Blender to open host paths or URLs.
    for entry in data.get('buffers', []) + data.get('images', []):
        uri = entry.get('uri')
        if uri and (not isinstance(uri, str) or not uri.startswith('data:')):
            raise Image3DError('Model odwoluje sie do zewnetrznego pliku. Wymagany samodzielny GLB.')
    return {'meshes': len(data['meshes']), 'embedded_images': len(data['images'])}


def image_size(path):
    raw = path.read_bytes()
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) >= 24:
        return list(struct.unpack('>II', raw[16:24]))
    if raw.startswith(b'\xff\xd8'):
        from photo_input import jpeg_dimensions
        return list(jpeg_dimensions(raw))
    raise Image3DError('Generator zwrocil nieprawidlowa teksture PNG/JPEG.')


def generate(photos, selected, folder, cancelled, progress, *, transport=request,
             download_asset=download, timeout=1200):
    """Submit once, resume GETs/downloads. Never fall back to procedural anatomy."""
    if selected.get('provider') != 'meshy' or not selected.get('api_key'):
        raise Image3DError(MISSING_CONNECTION)
    endpoint, payload = make_payload(photos, selected)
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    path = folder / 'image3d-task.json'
    task = json.loads(path.read_text()) if path.is_file() else None
    if task and task.get('fingerprint') != fingerprint:
        raise Image3DError('Zapisane zadanie dotyczy innych zdjec lub ustawien. Nie zamowiono nowego modelu.')
    if cancelled.is_set():
        raise InterruptedError()
    if task is None:
        task = {'provider': 'meshy', 'model': MODEL, 'endpoint': endpoint,
                'fingerprint': fingerprint, 'phase': 'submitting',
                'texture_resolution': payload['texture_resolution'],
                'reference_sha256': [hashlib.sha256(p['bytes']).hexdigest() for p in photos]}
        # Persist intent BEFORE the only paid POST. A crash or lost response must
        # not cause a second POST on restart or when retrying exports.
        write_json(path, task)
        progress('Meshy Ultra tworzy geometrie i tekstury z przeslanych zdjec…')
        try:
            response = transport('POST', endpoint, selected['api_key'], payload)
            remote_id = response.get('result') if isinstance(response, dict) else None
            if not isinstance(remote_id, str) or not TASK_ID.fullmatch(remote_id):
                raise Image3DError('Nie otrzymano identyfikatora zadania.')
        except RequestError as error:
            if not error.retryable:
                task.update(phase='rejected')
                write_json(path, task)
                raise Image3DError(str(error) + ' Nie uruchomiono kolejnej proby.') from None
            raise Image3DError('Nie potwierdzono utworzenia zadania Meshy. Nie ponawiam platnego zapytania. Sprawdz zadania na koncie Meshy przed nowa generacja.') from None
        except Exception:
            raise Image3DError('Nie potwierdzono utworzenia zadania Meshy. Nie ponawiam platnego zapytania. Sprawdz zadania na koncie Meshy przed nowa generacja.') from None
        task.update(id=remote_id, phase='submitted')
        write_json(path, task)
    if not isinstance(task.get('id'), str) or not TASK_ID.fullmatch(task['id']):
        raise Image3DError('Poprzednie wyslanie zadania nie zostalo potwierdzone. Sprawdz konto Meshy; ponowienie zostalo zablokowane, aby nie naliczyc drugiej oplaty.')
    deadline = time.monotonic() + timeout
    while True:
        if cancelled.is_set():
            raise InterruptedError()
        if time.monotonic() >= deadline:
            raise Image3DError('Meshy nadal przetwarza zapisane zadanie. Wznow odbior wyniku, bez kolejnej oplaty za generowanie.')
        try:
            result = transport('GET', endpoint + '/' + task['id'], selected['api_key'])
        except RequestError as error:
            if not error.retryable:
                raise
            progress('Oczekuje na odpowiedz Meshy dla tego samego zadania…')
            cancelled.wait(5)
            continue
        state = result.get('status') if isinstance(result, dict) else None
        if state not in ('PENDING', 'IN_PROGRESS', 'SUCCEEDED', 'FAILED', 'CANCELED'):
            raise Image3DError('Nieznany stan zadania Meshy. Nie utworzono kolejnego zadania.')
        task.update(phase=state)
        if isinstance(result.get('consumed_credits'), (int, float)):
            task['consumed_credits'] = result['consumed_credits']
        write_json(path, task)
        if state in ('FAILED', 'CANCELED'):
            raise Image3DError('Meshy nie ukonczylo zadania. Stan: ' + state + '. Nie uruchomiono szablonu ani kolejnej platnej proby.')
        if state == 'SUCCEEDED':
            break
        percent = result.get('progress', 0)
        percent = max(0, min(100, int(percent))) if isinstance(percent, (float, int)) else 0
        progress('Meshy Ultra: geometria i tekstury %d%%. To samo zadanie; oczekiwanie na wynik…' % percent)
        cancelled.wait(5)
    progress('Pobieram oryginalna geometrie i mapy materialow…')
    master = folder / 'model-master.glb'
    download_asset(asset_url(result.get('model_urls', {}).get('glb')), master, cancelled)
    geometry = validate_glb(master)
    records = [file_record(master, folder)]
    textures = []
    output = folder / 'provider-textures'
    output.mkdir(exist_ok=True, mode=0o700)
    maps = result.get('texture_urls') or []
    if not isinstance(maps, list) or len(maps) > 32:
        raise Image3DError('Nieprawidlowa lista tekstur generatora.')
    total = master.stat().st_size
    for index, entry in enumerate(maps):
        for channel in ('base_color', 'metallic', 'roughness', 'normal'):
            if not isinstance(entry, dict) or not entry.get(channel):
                continue
            url = asset_url(entry[channel])
            target = output / ('%02d-%s.image' % (index, channel))
            download_asset(url, target, cancelled)
            total += target.stat().st_size
            if total > MAX_TOTAL_BYTES:
                raise Image3DError('Pliki przekraczaja budzet pobierania. Oryginal pozostaje na koncie Meshy.')
            dimensions = image_size(target)
            with target.open('rb') as stream:
                suffix = '.png' if stream.read(8) == b'\x89PNG\r\n\x1a\n' else '.jpg'
            final = target.with_suffix(suffix)
            target.replace(final)
            textures.append({**file_record(final, folder), 'channel': channel,
                             'size': dimensions, 'pixels_resampled': False})
    manifest = {'revision': 1, 'provider': 'meshy', 'model': MODEL, 'task_id': task['id'],
                'ultra': True, 'image_enhancement': False, 'remeshed': False,
                'requested_texture_resolution': payload['texture_resolution'],
                'reference_sha256': task['reference_sha256'], 'files': records,
                'textures': textures, 'geometry': geometry,
                'consumed_credits': task.get('consumed_credits'),
                'likeness_verified': False, 'hidden_surfaces': 'inferred',
                'physical_dimensions_verified': False}
    write_json(folder / 'image3d-manifest.json', manifest)
    return manifest
