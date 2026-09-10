"""Full v20 worker with deterministic payload and rollback-safe installation."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'oracle_connector'))
updater=runpy.run_path(str(root/'oracle_connector/apply_update.py'))
names=[*updater['FILES'],'apply_update.py']
data={'base_hashes':{},'staged_files':names,
      'files':{name:base64.b64encode((root/'oracle_connector'/name).read_bytes()).decode() for name in names},
      'fixture':json.loads((root/'oracle_connector/examples/couture-fan-v20.scene.json').read_text())}
raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
template=(root/'scripts/cloud-shell-portrait.template.py').read_text()
template=template.replace('v15','v20').replace('v14 lub v20','wczesniejszej wersji')
template=template.replace("health.get('connectorVersion') != 15", "health.get('connectorVersion') != 20")
template=template.replace("health.get('portraitRevision') != 1:","health.get('portraitRevision') != 2 or health.get('coutureRevision') != 2 or health.get('characterStandard') != 20 or health.get('referenceQualityRevision') != 1 or health.get('materialQualityRevision') != 2:")
template=template.replace("report.get('revision') != 1", "report.get('revision') != 2")
template=template.replace("compile(base64.b64decode(encoded, validate=True), name, 'exec')", "decoded = base64.b64decode(encoded, validate=True)\n        if name.endswith('.py'): compile(decoded, name, 'exec')")
template=template.replace('timeout=180','timeout=900').replace('timeout=360','timeout=1080')
template=template.replace('FROGE_PORTRAIT_OK','FROGE_V20_OK')
template=template.replace('Poprawiona figurka jest juz dostepna na stronie.', 'Model kontrolny zostal zapisany na Oracle. Sprawdz jego wyglad; nowe modele tworz w generatorze.')
# Retain the actual verification model so it can be inspected after installation.
template=template.replace("with tempfile.TemporaryDirectory(prefix='portrait-export-check-', dir=target / 'state') as folder:",
    "with __import__('contextlib').nullcontext(target / 'state' / ('couture-review-v20-' + uuid.uuid4().hex)) as folder:")
template=template.replace('work = Path(folder)',"work = Path(folder)\n        work.mkdir(mode=0o700, parents=True)")
template=template.replace("print('FROGE_PORTRAIT_EXPORT_OK:","print('Model kontrolny: ' + str(work / 'model.glb'), flush=True)\n        if json.loads((work / 'result.json').read_text()).get('export_validation', {}).get('reimported') is not True:\n            raise RuntimeError('Ponowne otwarcie GLB nie zostalo potwierdzone.')\n        print('FROGE_PORTRAIT_EXPORT_OK:")
result=template.replace('__PAYLOAD_B64__',base64.b64encode(gzip.compress(raw,mtime=0)).decode()).replace('__PAYLOAD_SHA256__',hashlib.sha256(raw).hexdigest())
compile(result,'froge-v20.py','exec')
folder=root/'public/downloads';folder.mkdir(parents=True,exist_ok=True)
(folder/'froge-v20.py').write_text(result)
readme='''FORGE v20 — pełna aktualizacja generatora, referencje 4K/8K

Prześlij froge-v20.zip do Oracle Cloud Shell (Menu > Upload), potem:
python3 -m zipfile -e "$HOME/froge-v20.zip" "$HOME/froge-v20"
python3 "$HOME/froge-v20/froge-v20.py"

Instalator zachowuje istniejące połączenie, klucz OpenAI i modele. Przed zmianą
sprawdza aktywne zadania; tworzy kopię i cofa aktualizację, jeśli test nie przejdzie.
Uruchamia rzeczywisty model sukni i wachlarza bez płatnego zapytania do AI,
sprawdza portret, oczy, dłonie, paznokcie, tekstury i ponowne otwarcie GLB.
Model GLB oraz plik Blender zostają na Oracle; ścieżka jest wypisywana w terminalu.
FROGE_V20_OK oznacza udaną instalację i test struktury, nie zgodność twarzy ze zdjęciem.

Jakość referencji: limity 2048/4096/8192 px, proporcje bez rozciągania, brak
sztucznego powiększania, raport rzeczywistych wymiarów. Ta sama kompozycja
po ponownym zapisie zachowuje mapowanie kreacji; inne kadry go nie dziedziczą.
Źródła 4K/8K wymagają aktualnej strony i pracownika referenceQualityRevision=1.

Zmiany: osobna dopasowana suknia (bez bluzy), rzeczywista grubość, cienkie
zdobienia na powierzchni, wachlarz z powtarzanymi wirnikami, spięte włosy,
makijaż i nowsza baza anatomii v16. Do 5000 znaków, 600 s AI i 900 s Blender.
Zachowana obsługa grup i zdjęć. To nie trening wag modelu AI.

W tej wersji poprawiono przenikanie ciała przez suknię, eksport kolorowego
połysku i makijażu, fryzurę oraz dodano ocenę renderów przez Astrę z jedną
korektą planu. Budżety 600 s AI i 900 s Blender są wspólne dla etapów.
Modele sprawdzono w rzeczywistym Blenderze 4.3.0. Dodatkowy przebieg Astry
wymaga sprawdzenia z aktywnym kluczem na Oracle po instalacji.
Fotorealizm, dokładne podobieństwo, druk i rig do gry nie są potwierdzone.

Moduł pomiarów twarzy: strona odczytuje lokalnie 478 punktów na przesyłanym
JPEG. Blender dopasowuje zamkniętą siatkę i związane z nią detale do 112
punktów sterujących; kolor jest próbkowany z rzeczywistego zdjęcia. Ta funkcja
wymaga również aktualnego kodu strony, który przesyła faceLandmarks. Sam Oracle
nie uruchamia detektora. Obecnie obsługiwana jest jedna postać kobieca; inne
sceny zachowują wcześniejsze działanie i informację o braku dopasowania.
Głębia i słabiej widoczna strona pozostają szacowane. Oświetlenie referencji
częściowo pozostaje w kolorze skóry. To dopasowanie do punktów, nie skan.

Korekta po przeglądzie porannym: przestrzenne zwężane rzęsy, matowe pełniejsze
brwi, wyraźniejszy szmaragdowy makijaż i terakotowe usta. Gęstsza siatka twarzy
utrzymuje granice makijażu; satyna ma delikatniejszy połysk. Suknia otrzymała
cienkie srebrne przeszycia, wachlarz obramowania rzeczywistych faset.
Eksport kontroluje zachowanie rzęs na obu oczach. To nadal proceduralne studium
postaci; instalacja nie potwierdza fotograficznego podobieństwa.
'''
with zipfile.ZipFile(folder/'froge-v20.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name,content in [('froge-v20.py',result),('CZYTAJ.txt',readme)]:
        info=zipfile.ZipInfo(name,(2026,9,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,content.encode())
print('Full v20 package:',(folder/'froge-v20.zip').stat().st_size,'bytes')
