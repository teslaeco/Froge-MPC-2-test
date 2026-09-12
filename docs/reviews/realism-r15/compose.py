from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path('/workspace/scratch/584c9d97a5a1');P=ROOT/'realism-r15'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
def sheet(name,panels):
 canvas=Image.new('RGB',(640*len(panels),850),(17,24,31));d=ImageDraw.Draw(canvas)
 for i,(path,label) in enumerate(panels):
  im=Image.open(path).convert('RGB');assert im.size==(640,800),im.size
  canvas.paste(im,(640*i,50));d.text((640*i+18,12),label,font=font,fill=(237,230,220))
 canvas.save(P/name)
sheet('FORGE-r15-twarz-porownanie.png',[(ROOT/'anatomy-r14/FBX-face.png','PRZED — R14'),(P/'FBX-face.png','PO — R15'),(P/'FBX-face-angle.png','R15 — UKOS')])
sheet('FORGE-r15-trzy-widoki.png',[(P/'FBX-front.png','PRZÓD'),(P/'FBX-left.png','LEWY BOK'),(P/'FBX-back.png','TYŁ')])
sheet('FORGE-r15-geometria.png',[(ROOT/'anatomy-r14/FBX-face-clay.png','PRZED — GEOMETRIA'),(P/'FBX-face-clay.png','PO — GEOMETRIA')])
report=json.loads((P/'fbx-reimport-report.json').read_text());hq=json.loads((P/'hq-render-report.json').read_text());assert report['fbx_sha256']==hq['source_fbx_sha256']
assert Image.open(P/'FORGE-r15-render-HQ.png').size==(2048,2560)
files=['FORGE-model-r15.blend','FORGE-model-r15.fbx','FORGE-model-r15.glb','FORGE-r15-twarz-porownanie.png','FORGE-r15-trzy-widoki.png','FORGE-r15-geometria.png','FORGE-r15-render-HQ.png']
manifest=[]
for f in files:
 q=P/f;assert q.stat().st_size>0
 manifest.append({'name':f,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(P/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
