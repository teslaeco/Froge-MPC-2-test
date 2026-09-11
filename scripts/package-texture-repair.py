"""Build the self-contained texture repair from reviewed canonical sources."""
import base64, gzip, hashlib, json, runpy, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'oracle_connector'))
BASE_HASHES = {'server.py': '2370fe50046e4001d390b05956ccce5360e43d4bb3594693d4a5202d6e402143', 'runtime/run.py': '242c7333fec0a0cdf2413deabd1aff46396bea1168f12efed32a6a4d8ca15ad5', 'runtime/textiles.py': '8dd7bd8a546d94001c7cef850dbf616ba2c9ecef442e4cb79cdfbcaaa706ce73'}
changed = [*BASE_HASHES, 'apply_update.py']
updater = runpy.run_path(str(root / 'oracle_connector/apply_update.py'))
data = {'base_hashes': BASE_HASHES, 'staged_files': [*updater['FILES'], 'apply_update.py'],
        'files': {name: base64.b64encode((root / 'oracle_connector' / name).read_bytes()).decode() for name in changed},
        'fixture': json.loads((root / 'oracle_connector/examples/textures-eight.scene.json').read_text())}
raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
template = (root / 'scripts/cloud-shell-texture.template.py').read_text()
result = template.replace('__PAYLOAD_B64__', base64.b64encode(gzip.compress(raw, mtime=0)).decode()).replace('__PAYLOAD_SHA256__', hashlib.sha256(raw).hexdigest())
compile(result, 'froge-napraw-tekstury.py', 'exec')
(root / 'public/downloads/froge-napraw-tekstury.py').write_text(result)
print('Packaged standalone texture repair')
