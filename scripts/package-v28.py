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
template = (root / 'scripts/cloud-shell-v28.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v28.py', 'exec')
readme = """FORGE v28 — wykonanie Codex + Astra + Blender MCP

Oracle Cloud Shell: Menu > Upload > froge-v28.zip
python3 -m zipfile -e "$HOME/froge-v28.zip" "$HOME/froge-v28"
python3 "$HOME/froge-v28/froge-v28.py"

Wymagane potwierdzenia:
CODEX_MCP_BLENDER_BUILD_OK
FROGE_V28_OK

Test instalacji przechodzi przez rzeczywisty Codex, Code Mode, MCP,
budowe w Blenderze, trzy rendery i eksport FBX. Decyzje modelu w tescie
sa zaprogramowane: nie kupuje generacji i nie sprawdza podobienstwa zdjec.
V28 zachowuje identyfikator i szczegol bledu wywolania MCP, naprawia
walidacje pustej listy issues podczas zakonczenia oraz zapisuje przebieg
narzedzi bez zdjec, rozumowania i kluczy. Lokalny limit 12 zapytan /
36000 tokenow nie udaje juz ograniczenia OpenAI 429; oba sa rozrozniane.
Instrukcja jasno wskazuje wywolania narzedzi przez Code Mode oraz
przekazywanie renderow jako obrazow. Brak modelu jest opisany w raporcie.
Poprzednie modele, klucz i połączenie pozostaja zachowane.
Niepowodzenie testu powoduje przywrocenie poprzedniego kodu.

Nie zwiekszono limitow kosztu ani nie uruchomiono nowej platnej generacji.
Oryginalne logi przyczyny braku budowy w zadaniu ce122db3 pozostaja
na Oracle; instalator drukuje dostepne bezpieczne dane diagnostyczne.
Po FROGE_V28_OK odswiez Studio i sprawdz polaczenie.
"""


folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v28.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v28.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,12,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v28.py') != program.encode():
            raise RuntimeError('Incomplete v28 update archive')
    temporary.replace(folder / 'froge-v28.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v28:', (folder / 'froge-v28.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
