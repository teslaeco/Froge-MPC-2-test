from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
p=Path('/workspace/scratch/584c9d97a5a1/refinement-r10');f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
def sheet(name,items):
 im=Image.new('RGB',(640*len(items),860),'#161d25');d=ImageDraw.Draw(im)
 for i,(path,title) in enumerate(items):
  with Image.open(path) as source:im.paste(source.convert('RGB'),(i*640,60))
  d.text((i*640+16,16),title,font=f,fill='white')
 im.save(p/name)
 with Image.open(p/name) as check:check.verify()
sheet('FORGE-r10-trzy-widoki.png',[(p/'FBX-front.png','R10 — PRZÓD'),(p/'FBX-left.png','R10 — LEWY BOK'),(p/'FBX-back.png','R10 — TYŁ (INTERPRETACJA)')])
sheet('FORGE-r10-twarz.png',[(p/'FBX-face.png','R10 — TWARZ'),(p/'FBX-face-clay.png','R10 — GEOMETRIA BEZ TEKSTUR')])
files=['FORGE-r10-trzy-widoki.png','FORGE-r10-twarz.png','FORGE-model-r10-1500k.fbx','FORGE-model-r10-1500k.blend','FORGE-model-r10-1500k.glb']
(p/'upload-request.json').write_text(json.dumps({'uploads':[{'local_path':str(p/n),'purpose':'create_library_file'} for n in files]}))
(p/'hashes.json').write_text(json.dumps({n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in files},indent=2))
print('Verified sheets and model hashes ready')
