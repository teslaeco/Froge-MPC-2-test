"""Deterministic full worker update, restoring Astra photo generation."""
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'oracle_connector'))
names = [*runpy.run_path(str(root / 'oracle_connector/apply_update.py'))['FILES'], 'apply_update.py']
data = {'files': {name: base64.b64encode((root / 'oracle_connector' / name).read_bytes()).decode() for name in names}}
raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
template = (root / 'scripts/cloud-shell-v24.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v24.py', 'exec')
readme = 'FORGE v24 — naprawa timeoutu\n\nOracle Cloud Shell: Menu > Upload > froge-v24.zip\n\npython3 -m zipfile -e "$HOME/froge-v24.zip" "$HOME/froge-v24"\npython3 "$HOME/froge-v24/froge-v24.py"\n\nPoczekaj na FROGE_V24_OK, odswiez strone i sprawdz polaczenie z Oracle.\nInstalator zachowuje zapisane klucze, polaczenie, modele i kopie kodu.\nTesty instalacji sa bez platnego API. Wersja 24 zawiera cala aktualizacje 23.\n\nNAPRAWA\n- Odbior Astry konczy sie na response.completed, nawet gdy polaczenie HTTP\n  pozostaje otwarte. Nie czekamy na zamkniecie poprawnie zakonczonego strumienia.\n- Planowanie ze zdjec: do 900 s; tekst: do 600 s. Ocena zdjec ma nadal osobne\n  240 s. Nie zmieniono limitow tokenow ani liczby prob po timeoutcie.\n- Gotowy, sprawdzony GLB jest zachowany, gdy limit przerwie dodatkowy eksport\n  albo rendery. Kontrola sumy i nowy znacznik dla kazdej budowy odrzucaja\n  pliki niekompletne i pozostalosci starszej proby.\n- Timeout wskazuje etap: plan Astry, lokalne AI lub Blender. Zapisuje czasy\n  i dostepny szkic odpowiedzi. Szkic nie jest uznawany za gotowy model.\n- Ponowienie IDENTYCZNEGO opisu i zdjec po timeoutcie korzysta z poprawnego\n  zapisanego planu, jezeli istnieje, bez kolejnego zapytania AI.\n\nPO AKTUALIZACJI\nKliknij Ponow z tymi zdjeciami przy nieudanym zadaniu. Jezeli plan zdazyl sie\npoprawnie zapisac, Blender wykona go bez AI. Gdy plan nie istnieje, ponowne\ngenerowanie wymaga nowego zapytania do API i moze kosztowac.\n\nSprawdzono transport SSE, zachowanie pliku po przerwaniu, odrzucenie starego\nznacznika oraz kod i natywny Blender. Nie uruchomiono nowej platnej generacji\ni nie potwierdzono jakosci na kazdym zdjeciu. Ze starego ogolnego komunikatu\nnie mozna ustalic, ktory etap przekroczyl czas. Nie twierdzimy, ze nowy limit\ngwarantuje sukces kazdego zlecenia.\n'

folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v24.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v24.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,11,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v24.py') != program.encode():
            raise RuntimeError('Incomplete v24 update archive')
    temporary.replace(folder / 'froge-v24.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v24:', (folder / 'froge-v24.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
