from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
p=Path('/workspace/scratch/584c9d97a5a1/reconstruction-r12');root=p.parent
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
def sheet(name,items):
 im=Image.new('RGB',(640*len(items),860),'#161d25');d=ImageDraw.Draw(im)
 for i,(path,title) in enumerate(items):
  with Image.open(path) as src:im.paste(src.convert('RGB'),(i*640,60))
  d.text((i*640+14,16),title,font=f,fill='white')
 im.save(p/name)
 with Image.open(p/name) as check:check.verify()
sheet('FORGE-r12-przed-po.png',[(root/'refinement-r11/FBX-face.png','PRZED — R11'),(p/'FBX-face.png','PO — R12, TEN SAM KADR')])
sheet('FORGE-r12-geometria.png',[(root/'refinement-r11/FBX-face-clay.png','PRZED — GEOMETRIA R11'),(p/'FBX-face-clay.png','PO — GEOMETRIA R12')])
sheet('FORGE-r12-trzy-widoki.png',[(p/'FBX-front.png','R12 — PRZÓD'),(p/'FBX-left.png','R12 — LEWY BOK'),(p/'FBX-back.png','R12 — TYŁ (INTERPRETACJA)')])
files=['FORGE-r12-przed-po.png','FORGE-r12-geometria.png','FORGE-r12-trzy-widoki.png','FORGE-model-r12.fbx','FORGE-model-r12.blend','FORGE-model-r12.glb','FORGE-analiza-r12.md']
(p/'upload-request.json').write_text(json.dumps({'uploads':[{'local_path':str(p/n),'purpose':'create_library_file'} for n in files]}))
(p/'hashes.json').write_text(json.dumps({n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in files},indent=2))
print('Review sheets and hashes complete')
