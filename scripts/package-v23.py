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
template = (root / 'scripts/cloud-shell-v23.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v23.py', 'exec')
readme = '''FORGE v23 — geometria swobodna i tekstury ze zdjec

INSTALACJA — Oracle Cloud Shell > Menu > Upload: froge-v23.zip

python3 -m zipfile -e "$HOME/froge-v23.zip" "$HOME/froge-v23"
python3 "$HOME/froge-v23/froge-v23.py"

Po FROGE_V23_OK odswiez strone i sprawdz polaczenie z Oracle.
Aktualizacja korzysta z obecnej maszyny i zapisanego OpenAI. Zachowuje klucze,
polaczenie, modele i kopie programu. Nie wymaga Meshy ani nowego dostawcy.
Instalator wykonuje testy bez platnego API: import/eksport oraz swobodne
powierzchnie, dwie tekstury ze zdjec testowych i kontrola zaslaniania.

CO ZMIENIONO
- Astra moze opisywac swobodne powierzchnie i asymetryczne przekroje zamiast
  ograniczac sie do elipsoid oraz kilku gotowych strojow.
- Nowe zlecenia ze zdjec musza podac kamery i maski widocznych czesci.
- Blender naklada oryginalne piksele tylko na widoczne sciany w masce;
  inne ujecia moga dostarczyc kolor tylu i bokow. Ukryte sciany zachowuja material.
- Eksport FBX/OBJ konsoliduje UV kolorow osobno dla kazdej sciany i materialu.
- Planowanie AI ma do 600 s, dodatkowa ocena do 240 s, lacznie do 840 s.
  Rezerwa na ocene wynosi 240 s; calosc moze trwac dluzej i zuzyc wiecej API.
  Blender: do 600 s pierwszej budowy i 300 s rezerwy na przebudowe, 900 s lacznie.
- Prywatny endpoint /v1/jobs/{id}/quality zwraca rzeczywiste dane modelu,
  tekstur, projekcji i status kontroli. Sukces zapisu nie oznacza akceptacji wygladu.

SPRAWDZONO
Testy kodu, natywne powierzchnie w Blenderze 4.3, maski, zaslanianie, przypisanie
przodu/tylu, eksport i ponowny import FBX. Sa to kontrolowane dane testowe,
nie pomiar podobienstwa nowej generacji Astry ani dowod dzialania na kazdym zdjeciu.

OGRANICZENIA
Astra pozostaje modelem planujacym; to nie trening nowego silnika image-to-3D.
Dokladnosc kamer, masek i geometrii zalezy od planu i wymaga oceny renderow.
Z jednego zdjecia nie odzyskamy pewnego wygladu niewidocznego tylu. Tekstury
zachowuja sfotografowane oswietlenie; nie sa odzyskanym fizycznym albedo.
Nowe narzedzia rozszerzaja zakres ksztaltow, ale nie gwarantuja fotorealizmu
kazdego modelu ani zgodnosci 1:1. Detale nieobecne w zdjeciu pozostaja szacowane.
Rozdzielczosc jest raportowana z plikow; nie podnosimy jej sztucznie dla etykiety 4K.

Ta paczka aktualizuje Oracle. Nie publikuje nowego interfejsu strony.
Przygotowany kod i raport sa w PR #9: teslaeco/Froge-MPC-2-test.
'''

folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v23.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v23.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,11,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v23.py') != program.encode():
            raise RuntimeError('Incomplete v23 update archive')
    temporary.replace(folder / 'froge-v23.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v23:', (folder / 'froge-v23.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
