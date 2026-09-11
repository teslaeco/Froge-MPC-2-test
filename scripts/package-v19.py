"""Full v19 worker with deterministic payload and rollback-safe installation."""
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
      'fixture':json.loads((root/'oracle_connector/examples/couture-fan-v19.scene.json').read_text())}
raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
template=(root/'scripts/cloud-shell-portrait.template.py').read_text()
template=template.replace('v15','v19').replace('v14 lub v19','wczesniejszej wersji')
template=template.replace("health.get('connectorVersion') != 15", "health.get('connectorVersion') != 19")
template=template.replace("health.get('portraitRevision') != 1:","health.get('portraitRevision') != 1 or health.get('coutureRevision') != 1 or health.get('characterStandard') != 19:")
template=template.replace("compile(base64.b64decode(encoded, validate=True), name, 'exec')", "decoded = base64.b64decode(encoded, validate=True)\n        if name.endswith('.py'): compile(decoded, name, 'exec')")
template=template.replace('timeout=180','timeout=900').replace('timeout=360','timeout=1080')
template=template.replace('FROGE_PORTRAIT_OK','FROGE_V19_OK')
# Retain the actual verification model so it can be inspected after installation.
template=template.replace("with tempfile.TemporaryDirectory(prefix='portrait-export-check-', dir=target / 'state') as folder:",
    "with __import__('contextlib').nullcontext(target / 'state' / ('couture-review-v19-' + uuid.uuid4().hex)) as folder:")
template=template.replace('work = Path(folder)',"work = Path(folder)\n        work.mkdir(mode=0o700, parents=True)")
template=template.replace("print('FROGE_PORTRAIT_EXPORT_OK:","print('Model kontrolny: ' + str(work / 'model.glb'), flush=True)\n        if json.loads((work / 'result.json').read_text()).get('export_validation', {}).get('reimported') is not True:\n            raise RuntimeError('Ponowne otwarcie GLB nie zostalo potwierdzone.')\n        print('FROGE_PORTRAIT_EXPORT_OK:")
result=template.replace('__PAYLOAD_B64__',base64.b64encode(gzip.compress(raw,mtime=0)).decode()).replace('__PAYLOAD_SHA256__',hashlib.sha256(raw).hexdigest())
compile(result,'froge-v19.py','exec')
folder=root/'public/downloads';folder.mkdir(parents=True,exist_ok=True)
(folder/'froge-v19.py').write_text(result)
readme='''FORGE v19 — pełna aktualizacja generatora

Prześlij froge-v19.zip do Oracle Cloud Shell (Menu > Upload), potem:
python3 -m zipfile -e "$HOME/froge-v19.zip" "$HOME/froge-v19"
python3 "$HOME/froge-v19/froge-v19.py"

Instalator zachowuje istniejące połączenie, klucz OpenAI i modele. Przed zmianą
sprawdza aktywne zadania; tworzy kopię i cofa aktualizację, jeśli test nie przejdzie.
Uruchamia rzeczywisty model sukni i wachlarza bez płatnego zapytania do AI,
sprawdza portret, oczy, dłonie, paznokcie, tekstury i ponowne otwarcie GLB.
Model GLB oraz plik Blender zostają na Oracle; ścieżka jest wypisywana w terminalu.
FROGE_V19_OK oznacza udaną instalację i test struktury, nie zgodność twarzy ze zdjęciem.

Zmiany: osobna dopasowana suknia (bez bluzy), rzeczywista grubość, cienkie
zdobienia na powierzchni, wachlarz z powtarzanymi wirnikami, spięte włosy,
makijaż i nowsza baza anatomii v16. Do 5000 znaków, 600 s AI i 900 s Blender.
Zachowana obsługa grup i zdjęć. To nie trening wag modelu AI.

Ograniczenia tego wydania: autor zmian nie miał działającego Blendera ani SSH
do Oracle. Testy lokalne sprawdzają kod i geometrię numeryczną; przed publikacją
trzeba uruchomić powyższy test na Oracle i obejrzeć twarz oraz pełną sylwetkę.
Fotorealizm, dokładne podobieństwo, druk i rig do gry nie są potwierdzone.
'''
with zipfile.ZipFile(folder/'froge-v19.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name,content in [('froge-v19.py',result),('CZYTAJ.txt',readme)]:
        info=zipfile.ZipInfo(name,(2026,9,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,content.encode())
print('Full v19 package:',(folder/'froge-v19.zip').stat().st_size,'bytes')
