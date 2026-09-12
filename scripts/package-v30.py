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
template = (root / 'scripts/cloud-shell-v30.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v30.py', 'exec')
readme = """FORGE v30 — Astra + Codex + Blender MCP

Cloud Shell: Menu > Upload > froge-v30.zip
python3 -m zipfile -e "$HOME/froge-v30.zip" "$HOME/froge-v30"
python3 "$HOME/froge-v30/froge-v30.py"

Instalacja nie wywoluje platnego modelu; testuje rzeczywisty Codex,
MCP, Blender i eksport FBX z zaprogramowanymi odpowiedziami modelu.
Wymagane: CODEX_MCP_BLENDER_BUILD_OK i FROGE_V30_OK.

V30 naprawia odczyt po zakonczonym finish_model, konczy Codex po
zweryfikowanym finale, laczy wynik z biezacym wykonaniem i SHA256.
Blad edycji Python nie zabija MCP. Poprawione sa materialy korekt
(8 nowych przy legalnej palecie postaci), ellipsoid i koncowka bledu.
Strona odroznia szkic od ocenionej rewizji, pokazuje zrodlo podgladu
i odblokowuje nowe zlecenie po zakonczeniu/anulowaniu poprzedniego.
Astra pozostaje projektantem; Codex steruje Blenderem przez MCP.
Budzet pozostaje 32 zapytania, 96000 tokenow, 5 budow i 1800 sekund.

Opcjonalna RZECZYWISTA PLATNA PROBA przy instalacji:
python3 "$HOME/froge-v30/froge-v30.py" --test-job NUMER_ZAPISANEGO_ZLECENIA
Uzywa oryginalnego opisu i zdjec zapisanych na Oracle. Jeden trwaly
identyfikator zabezpiecza przed ponownym zamowieniem po zerwaniu SSH.
Powtorzenie polecenia odczytuje ten sam wynik. Pliki i raport proby sa
na Oracle; proba terminalowa nie dodaje sama rekordu do historii strony.
Terminal pokazuje FROGE_PAID_TRIAL_MODEL_CREATED tylko po powstaniu
rzeczywistego modelu. Jego podobienstwo nadal wymaga oceny renderow.

Nie obiecujemy braku bledow ani potwierdzonego podobienstwa bez wyniku.
Po instalacji odswiez Studio i sprawdz polaczenie.
"""


folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v30.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v30.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,12,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v30.py') != program.encode():
            raise RuntimeError('Incomplete v30 update archive')
    temporary.replace(folder / 'froge-v30.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v30:', (folder / 'froge-v30.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
