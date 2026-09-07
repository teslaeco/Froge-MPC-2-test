"""Prepare bounded CC0 head/hand geometry from the documented MakeHuman sources.

Usage: python scripts/build-anatomy-assets.py SOURCE_DIRECTORY
Only data is reused; no MakeHuman executable source is incorporated.
"""
import gzip
import json
from pathlib import Path
import sys

source = Path(sys.argv[1])
output = Path(__file__).resolve().parents[1] / 'oracle_connector/runtime/assets'
output.mkdir(parents=True, exist_ok=True)
vertices, uvs, groups = [], [], {}
group = 'body'
for line in (source / 'base.obj').read_text().splitlines():
    p = line.split()
    if not p: continue
    if p[0] == 'v': vertices.append(list(map(float, p[1:4])))
    elif p[0] == 'vt': uvs.append(list(map(float, p[1:3])))
    elif p[0] == 'g': group = p[1]
    elif p[0] == 'f': groups.setdefault(group, []).append([tuple(int(a)-1 for a in s.split('/')[:2]) for s in p[1:]])
body_ids = {i for f in groups['body'] for i, _ in f}
shapes = {}
for name in ('male', 'female'):
    v = [p.copy() for p in vertices]
    for line in (source / (name+'.target')).read_text().splitlines():
        p = line.split()
        if p and not p[0].startswith('#'):
            for axis in range(3): v[int(p[0])][axis] += float(p[axis+1])
    low, high = min(v[i][1] for i in body_ids), max(v[i][1] for i in body_ids)
    scale = 1.8/(high-low)
    shapes[name] = [[p[0]*scale, -p[2]*scale, (p[1]-low)*scale] for p in v]

def joint(name, shape):
    ids = {i for f in groups[name] for i, _ in f}
    return [sum(shapes[shape][i][axis] for i in ids)/len(ids) for axis in range(3)]

selected = {}
for part in ('head', 'left', 'right', 'left-forearm', 'right-forearm'):
    def include(i):
        x,y,z = shapes['male'][i]
        if part.endswith('-forearm'):return (x>.30 if part.startswith('left') else x<-.30) and z<1.40
        return z>1.47 if part=='head' else (x> .455 if part=='left' else x<-.455) and z<1.27
    faces = [f for f in groups['body'] if all(include(i) for i, _ in f)]
    ids = sorted({i for f in faces for i, _ in f}); mapping = {k:i for i,k in enumerate(ids)}
    selected[part] = {'shapes': {s:[[round(c,7) for c in shapes[s][i]] for i in ids] for s in shapes},
                      'faces':[[mapping[i] for i,_ in f] for f in faces],
                      'uv':[[uvs[t] for _,t in f] for f in faces]}
landmarks = {s:{g[6:]:joint(g,s) for g in groups if g.startswith('joint-')} for s in shapes}
data = {'version':1,'parts':selected,'landmarks':landmarks}
with (output/'anatomy.json.gz').open('wb') as f:
    with gzip.GzipFile(fileobj=f, mode='wb', filename='', mtime=0) as gz:
        gz.write(json.dumps(data,separators=(',',':')).encode())
print('Anatomy bytes', (output/'anatomy.json.gz').stat().st_size)
print({part:len(p['faces']) for part,p in selected.items()})
