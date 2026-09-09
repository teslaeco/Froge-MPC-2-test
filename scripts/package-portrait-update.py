"""Reproducible one-file upgrade from the confirmed v14/r2 Oracle sources."""
import base64,gzip,hashlib,json,runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'oracle_connector'))
base=json.loads((root/'scripts/portrait-update-base.json').read_text())
updater=runpy.run_path(str(root/'oracle_connector/apply_update.py'))
data={'base_hashes':base,'staged_files':[*updater['FILES'],'apply_update.py'],
      'files':{name:base64.b64encode((root/'oracle_connector'/name).read_bytes()).decode() for name in [*base,'apply_update.py']},
      'fixture':json.loads((root/'oracle_connector/examples/portrait-floor-components.scene.json').read_text())}
raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
template=(root/'scripts/cloud-shell-portrait.template.py').read_text()
result=template.replace('__PAYLOAD_B64__',base64.b64encode(gzip.compress(raw,mtime=0)).decode()).replace('__PAYLOAD_SHA256__',hashlib.sha256(raw).hexdigest())
compile(result,'froge-standard-postaci.py','exec')
(root/'public/downloads/froge-standard-postaci.py').write_text(result)
print('Packaged verified-base portrait standard installer')
