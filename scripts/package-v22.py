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
template = (root / 'scripts/cloud-shell-astra.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v22.py', 'exec')
readme = '''FORGE v22 — Astra Max + Blender, 2026-09-11

Ta aktualizacja wycofuje wymaganie dodatkowego silnika. Zdjecia i opis
trafiaja do Astry przez zapisany klucz OpenAI. Blender wykonuje sprawdzony
plan geometrii i materialow. Dla zdjec Astra uzywa reasoning.effort=max.
Ocena wizualna obejmuje rzeczywiste rendery przodu, profilu, tylu, twarzy
oraz ujecia trzy-czwarte. Zachowane sa eksporty FBX, OBJ, STL, BLEND i GLB.

INSTALACJA — Oracle Cloud Shell, Menu > Upload: froge-v22.zip

python3 -m zipfile -e "$HOME/froge-v22.zip" "$HOME/froge-v22"
python3 "$HOME/froge-v22/froge-v22.py"

Po FROGE_V22_OK odswiez strone i sprawdz polaczenie z Oracle.
Nie ma trzeciego polecenia ani dodatkowego klucza. Istniejace polaczenie
OpenAI, klucze, modele i kopie programu sa zachowane. Instalator nie wywoluje
platnego API. Podczas czekania pokazuje postep co 15 sekund.
Astra nadal korzysta z platnego OpenAI API podczas faktycznego generowania.

OGRANICZENIA I STAN
To przywrocenie Astry i rozszerzenie jej kontroli wizualnej. Nie jest nowym
wytrenowanym modelem image-to-3D ani dowodem fotograficznej zgodnosci 1:1.
Astra tworzy instrukcje, Blender oblicza geometrie, UV i tekstury z referencji
oraz procedur materialowych. Nie odzyskujemy ukrytych powierzchni ani detali
nieobecnych w zdjeciu. 4K/8K oznacza limit map, a nie wynik podobienstwa.
Instalator sprawdza pliki na szescianie, bez generowania postaci przez AI.

Zmiany strony zapisane w PR #9 repozytorium teslaeco/Froge-MPC-2-test.
Instalator aktualizuje Oracle; nie publikuje nowego interfejsu strony.
'''

folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v22.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v22.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,11,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v22.py') != program.encode():
            raise RuntimeError('Incomplete v22 update archive')
    temporary.replace(folder / 'froge-v22.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v22:', (folder / 'froge-v22.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
