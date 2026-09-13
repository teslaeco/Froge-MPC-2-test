from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
p=Path('/workspace/scratch/584c9d97a5a1/materials-r13');root=p.parent;f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
def sheet(name,items):
 out=Image.new('RGB',(640*len(items),856),'#151e27');d=ImageDraw.Draw(out)
 for i,(path,label) in enumerate(items):
  with Image.open(path) as im:out.paste(im.convert('RGB'),(640*i,56))
  d.text((640*i+14,15),label,font=f,fill='white')
 out.save(p/name)
 with Image.open(p/name) as im:im.verify()
sheet('FORGE-r13-twarz-porownanie.png',[(root/'reconstruction-r12/FBX-face.png','PRZED — R12'),(p/'FBX-face.png','R13 — NOWE MATERIAŁY'),(p/'FBX-face-angle.png','R13 — WIDOK POD KĄTEM')])
sheet('FORGE-r13-stroj-porownanie.png',[(root/'reconstruction-r12/FBX-front.png','PRZED — R12'),(p/'FBX-front.png','R13 — NOWE MATERIAŁY'),(p/'FBX-fabric.png','R13 — ZBLIŻENIE TKANINY')])
sheet('FORGE-r13-trzy-widoki.png',[(p/'FBX-front.png','PRZÓD'),(p/'FBX-left.png','LEWY BOK'),(p/'FBX-back.png','TYŁ — INTERPRETACJA')])
names=['FORGE-r13-twarz-porownanie.png','FORGE-r13-stroj-porownanie.png','FORGE-r13-trzy-widoki.png','FORGE-model-r13.blend','FORGE-model-r13.fbx','FORGE-model-r13.glb','FORGE-kontrola-materialow-r13.md']
(p/'hashes.json').write_text(json.dumps({n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in names},indent=2))
(p/'upload-request.json').write_text(json.dumps({'uploads':[{'local_path':str(p/n),'purpose':'create_library_file'} for n in names]}))
print('R13 sheets verified')
