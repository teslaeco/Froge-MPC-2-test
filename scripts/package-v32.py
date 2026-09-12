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
template = (root / 'scripts/cloud-shell-v32.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v32.py', 'exec')
readme = """FORGE v32 — Astra + Codex + Blender MCP

Cloud Shell: Menu > Upload > froge-v32.zip
python3 -m zipfile -e "$HOME/froge-v32.zip" "$HOME/froge-v32"
python3 "$HOME/froge-v32/froge-v32.py"

Mala aktualizacja istniejacego generatora: ponownie wykorzystuje piec duzych
zasobow anatomii i tekstur TYLKO po potwierdzeniu ich SHA256. Gdy zasobow
brakuje lub sa uszkodzone, zatrzymuje sie przed zmiana kodu i wskazuje pelne v30.
Instalacja nie wywoluje platnego modelu; testuje rzeczywisty Codex,
MCP, Blender i eksport FBX z zaprogramowanymi odpowiedziami modelu.
Wymagane: CODEX_MCP_BLENDER_BUILD_OK i FROGE_V32_OK.

V32 naprawia odczyt po finish_model, takze gdy ostatnie wywolanie trwa ponad
2 sekundy. Duze sceny i historie edycji odczytuje stronicami z kontrola
rewizji i SHA256, bez utraty konca modelu. Chroni osobne obiekty anatomii
i rzesy przed laczeniem tracacym znaczniki. Bledy anatomii zawieraja
konkretne brakujace elementy, zamiast samego script failed.
Zawiera poprawki instalacji i eksportow v30/v31.
Ta paczka aktualizuje Oracle; nie aktualizuje kodu strony Studio.
Astra pozostaje projektantem; Codex steruje Blenderem przez MCP.
Budzet pozostaje 32 zapytania, 96000 tokenow, 5 budow i 1800 sekund.

Opcjonalna RZECZYWISTA PLATNA PROBA przy instalacji:
python3 "$HOME/froge-v32/froge-v32.py" --test-job NUMER_ZAPISANEGO_ZLECENIA
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
(folder / 'froge-v32.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v32.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,12,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v32.py') != program.encode():
            raise RuntimeError('Incomplete v32 update archive')
    temporary.replace(folder / 'froge-v32.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v32:', (folder / 'froge-v32.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
