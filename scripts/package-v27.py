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
template = (root / 'scripts/cloud-shell-v27.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v27.py', 'exec')
readme = """FORGE v27 — naprawa polaczenia Codex / Code Mode / Blender MCP

Oracle Cloud Shell: Menu > Upload > froge-v27.zip
python3 -m zipfile -e "$HOME/froge-v27.zip" "$HOME/froge-v27"
python3 "$HOME/froge-v27/froge-v27.py"

Wymagane potwierdzenia:
CODEX_MCP_REAL_CLI_ROUNDTRIP_OK
FROGE_V27_OK

Poprzedni test v26 oczekiwal bezposrednich funkcji. Astra w Codex
korzysta z Code Mode; v26 wylaczalo host i nie instalowalo jego pliku.
V27 pobiera osobno oficjalny codex-code-mode-host 0.154.0,
sprawdza SHA256, wlacza wlasciwy tryb i sprawdza rzeczywisty wynik MCP
oraz obecnosc wszystkich 6 narzedzi. Odpowiedzi modelu sa kontrolne.
Test nie wywoluje platnego API i nie generuje nowej postaci.
Brak narzedzia exec zatrzymuje zlecenie przed wyslaniem do OpenAI.
Bledy zachowuja szczegoly; nieudana aktualizacja przywraca poprzedni
kod i potwierdzenie weryfikacji, zachowujac modele, polaczenie i klucz.

Lokalne testy kodu nie potwierdzaja instalacji na Twojej maszynie.
W naszym zagniezdzonym srodowisku pelny Codex zatrzymuje sie podczas
startu, przed zapytaniem do modelu. Obowiazkowy test na Oracle pozostaje
bramka przyjecia aktualizacji. Nie omijaj go po bledzie.
Po FROGE_V27_OK odswiez strone i sprawdz polaczenie.
Zmiany nie sa nowym pomiarem szybkosci ani podobienstwa postaci.
"""


folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v27.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v27.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,12,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v27.py') != program.encode():
            raise RuntimeError('Incomplete v27 update archive')
    temporary.replace(folder / 'froge-v27.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v27:', (folder / 'froge-v27.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
