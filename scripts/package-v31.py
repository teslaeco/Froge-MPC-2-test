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
base_assets = json.loads((root/'oracle_connector/runtime/assets/manifest.json').read_text())
base_names = {'runtime/assets/'+name: digest for name, digest in base_assets.items()}
data = {'files': {name: base64.b64encode((root / 'oracle_connector' / name).read_bytes()).decode() for name in names if name not in base_names}, 'base_assets': base_names}
for name,digest in base_names.items():
    if hashlib.sha256((root/'oracle_connector'/name).read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Existing asset manifest does not match source: '+name)

raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
template = (root / 'scripts/cloud-shell-v31.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v31.py', 'exec')
readme = """FORGE v31 — Astra + Codex + Blender MCP

Cloud Shell: Menu > Upload > froge-v31.zip
python3 -m zipfile -e "$HOME/froge-v31.zip" "$HOME/froge-v31"
python3 "$HOME/froge-v31/froge-v31.py"

Mala aktualizacja istniejacego generatora: ponownie wykorzystuje piec duzych
zasobow anatomii i tekstur TYLKO po potwierdzeniu ich SHA256. Gdy zasobow
brakuje lub sa uszkodzone, zatrzymuje sie przed zmiana kodu i wskazuje pelne v30.
Instalacja nie wywoluje platnego modelu; testuje rzeczywisty Codex,
MCP, Blender i eksport FBX z zaprogramowanymi odpowiedziami modelu.
Wymagane: CODEX_MCP_BLENDER_BUILD_OK i FROGE_V31_OK.

V31 dodatkowo usuwa wykryte przez Copilota bledy instalacji/rollback,
sprawdza pliki Codex i Code Mode przed przyjeciem platnego zlecenia oraz
atomowo zapisuje identyfikator proby. Powtarzanie duzych scen ma zgodny limit.
Zawiera wszystkie poprawki v30: odczyt po zakonczonym finish_model, konczy Codex po
zweryfikowanym finale, laczy wynik z biezacym wykonaniem i SHA256.
Blad edycji Python nie zabija MCP. Poprawione sa materialy korekt
(8 nowych przy legalnej palecie postaci), ellipsoid i koncowka bledu.
Strona odroznia szkic od ocenionej rewizji, pokazuje zrodlo podgladu
i odblokowuje nowe zlecenie po zakonczeniu/anulowaniu poprzedniego.
Astra pozostaje projektantem; Codex steruje Blenderem przez MCP.
Budzet pozostaje 32 zapytania, 96000 tokenow, 5 budow i 1800 sekund.

Opcjonalna RZECZYWISTA PLATNA PROBA przy instalacji:
python3 "$HOME/froge-v31/froge-v31.py" --test-job NUMER_ZAPISANEGO_ZLECENIA
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
(folder / 'froge-v31.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v31.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,12,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v31.py') != program.encode():
            raise RuntimeError('Incomplete v31 update archive')
    temporary.replace(folder / 'froge-v31.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v31:', (folder / 'froge-v31.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
