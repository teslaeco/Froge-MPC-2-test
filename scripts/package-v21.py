"""Deterministic full worker update, with secure optional Meshy configuration."""
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
template = (root / 'scripts/cloud-shell-image3d.template.py').read_text()
program = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(program, 'froge-v21.py', 'exec')
readme = '''FORGE v21 — geometria i tekstury ze zdjec, 2026-09-11

Nowa sciezka: Meshy 7 Ultra generuje model bezposrednio z przeslanych zdjec.
Nie buduje postaci ze starej anatomii, zarejestrowanego zdjecia ani opisu Astry.
Kazda modelka/obiekt ma osobne zlecenie. Do czterech zdjec to ujecia tej samej
postaci. Silnik zachowuje poze, nie przerabia stylu zdjecia, generuje PBR.
Brak polaczenia Meshy blokuje nowe zlecenie ze zdjecia przed generowaniem.

INSTALACJA W TWOIM ORACLE CLOUD SHELL
Przeslij froge-v21.zip przez Menu > Upload, a nastepnie wykonaj:

python3 -m zipfile -e "$HOME/froge-v21.zip" "$HOME/froge-v21"
python3 "$HOME/froge-v21/froge-v21.py"

Po FROGE_V21_OK podlacz Meshy (klucz wpiszesz w ukrytym polu terminala):

python3 "$HOME/froge-v21/froge-v21.py" --connect-meshy

Nie wklejaj klucza do czatu ani do polecenia. Polaczenie wymaga osobnego
konta/klucza API Meshy i kredytow. Klucz OpenAI i dotychczasowe modele zostaja.
Po MESHY_CONNECTION_OK odswiez strone, sprawdz polaczenie z Oracle, dodaj
zdjecie i kliknij Generuj. Sam instalator i podlaczenie klucza nie kupuja modelu.
Domyslnie wybrane sa tekstury koloru 8K i Ultra. Pelny eksport 8K wymaga co
najmniej 10 GiB dostepnej pamieci na VM; test zasobow poprzedza platne zlecenie.
W nowym panelu strony mozna wybrac 4K. Bez niego mozna skonfigurowac worker
bezposrednio na VM: python3 ~/froge-connector/server.py --configure-image3d
--texture-resolution 4k (oba argumenty w jednej linii).

Model-master.glb zachowuje dokladne bajty oryginalu z silnika. FBX, OBJ+MTL,
STL i BLEND pochodza z tej samej zaimportowanej geometrii.
Oryginalne mapy koloru, normalnych, metalicznosci i szorstkosci otrzymane od
silnika sa dostepne takze jako osobny ZIP z teksturami PBR.
Podglad do 48 MiB moze miec mniejsze tekstury; master i eksporty ich nie traca. Rzeczywiste
rozmiary map sa w result.json; samo zadanie 8K nie jest dowodem ich rozmiaru.
FBX/OBJ maja ograniczenia przenoszenia shaderow PBR. STL nie zawiera tekstur.
Skala generatora jest zachowana; rzeczywiste wymiary fizyczne sa nieznane.

Nie ponawiamy automatycznie niepotwierdzonego platnego POST. Zapisany task ID
pozwala wznowic pobieranie/eksport. Zerwanie lacznosci z nieznanym task ID
wymaga sprawdzenia konta Meshy przed nowym zleceniem. Zatrzymanie oczekiwania
nie gwarantuje przerwania pracy ani zwrotu kredytow u dostawcy.

ZAKRES WERYFIKACJI
Wykonano testy protokolu offline i prawdziwy import/eksport w Blenderze.
Instalator testuje teksturowany szescian. To test plikow, nie model postaci.
Nie wykonano platnej generacji Meshy: w sesji nie bylo polaczenia Meshy.
Podobienstwo do zdjecia oraz niewidoczny tyl wymagaja oceny rzeczywistego
wyniku; nie obiecujemy skanu 1:1 z pojedynczej grafiki ani jakosci lepszej od
Meshy. Zmiana silnika usuwa ograniczenie starego szablonu, nie niepewnosc 3D.

KOD STRONY
Ustawienia Meshy, pobieranie FBX/oryginalu i bezplatne wznowienie przygotowano
w PR #9 repozytorium teslaeco/Froge-MPC-2-test. Instalator aktualizuje Oracle,
nie kod strony. Nowy panel strony wymaga osobnego wdrozenia jej kodu.
W sesji wgranie strony blokowal HTTP 500 jej repozytorium zrodlowego.
Na starszej stronie z polaczona Astra nowe zdjecia moga juz korzystac z
nowego silnika po aktualizacji Oracle, ale opisy i przyciski pozostaja stare.

Dokumentacja API: https://docs.meshy.ai/en/api/image-to-3d
Cennik: https://docs.meshy.ai/en/api/pricing
'''
folder = root / 'public/downloads'; folder.mkdir(parents=True, exist_ok=True)
(folder / 'froge-v21.py').write_text(program)
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in [('froge-v21.py', program), ('CZYTAJ.txt', readme)]:
        info = zipfile.ZipInfo(name, (2026,9,11,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, value.encode())
with tempfile.NamedTemporaryFile(dir=folder, delete=False) as pending:
    temporary = Path(pending.name)
    pending.write(buffer.getvalue()); pending.flush(); os.fsync(pending.fileno())
try:
    with zipfile.ZipFile(temporary) as verified:
        if verified.testzip() is not None or verified.read('froge-v21.py') != program.encode():
            raise RuntimeError('Incomplete v21 update archive')
    temporary.replace(folder / 'froge-v21.zip')
finally:
    temporary.unlink(missing_ok=True)
print('FORGE v21:', (folder / 'froge-v21.zip').stat().st_size, 'bytes;', len(names), 'files; payload', hashlib.sha256(raw).hexdigest())
