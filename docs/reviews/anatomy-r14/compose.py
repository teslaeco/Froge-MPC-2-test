from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
p=Path('/workspace/scratch/584c9d97a5a1/anatomy-r14');root=p.parent;f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
def sheet(name,items):
 out=Image.new('RGB',(640*len(items),856),'#151e27');d=ImageDraw.Draw(out)
 for i,(path,label) in enumerate(items):
  with Image.open(path) as im:out.paste(im.convert('RGB'),(640*i,56))
  d.text((640*i+14,15),label,font=f,fill='white')
 out.save(p/name)
 with Image.open(p/name) as im:im.verify()
sheet('FORGE-r14-twarz-porownanie.png',[(root/'materials-r13/FBX-face.png','PRZED — R13'),(p/'FBX-face.png','R14 — ZĘBY, OKO, SZYJA'),(p/'FBX-face-angle.png','R14 — POD KĄTEM')])
sheet('FORGE-r14-trzy-widoki.png',[(p/'FBX-front.png','PRZÓD'),(p/'FBX-left.png','LEWY BOK'),(p/'FBX-back.png','TYŁ — INTERPRETACJA')])
sheet('FORGE-r14-kontrola-geometrii.png',[(root/'reconstruction-r12/FBX-face-clay.png','GEOMETRIA PRZED — R12/R13'),(p/'FBX-face-clay.png','GEOMETRIA R14')])
names=['FORGE-r14-twarz-porownanie.png','FORGE-r14-trzy-widoki.png','FORGE-r14-kontrola-geometrii.png','FORGE-model-r14.blend','FORGE-model-r14.fbx','FORGE-model-r14.glb','FORGE-kontrola-r14.md']
(p/'hashes.json').write_text(json.dumps({n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in names},indent=2))
(p/'upload-request.json').write_text(json.dumps({'uploads':[{'local_path':str(p/n),'purpose':'create_library_file'} for n in names]}))
print('R14 sheets verified')
