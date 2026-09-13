"""Prepare the GitHub source mirror using published, hash-pinned assets.
Run from repository root after publication. No keys or private APIs are used.
"""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'asset-manifest.json').read_text())
for item in manifest['files']:
    relative=Path(item['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('unsafe asset path')
    path=root/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']:
        continue
    with urllib.request.urlopen(manifest['origin']+'/'+relative.as_posix(),timeout=180) as response:
        data=response.read(item['bytes']+1)
    if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
        raise ValueError('published asset differs: '+str(relative))
    path.write_bytes(data)
print('Published assets verified')
