from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json
ROOT=Path('/workspace/scratch/584c9d97a5a1');P=ROOT/'correction-e15'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
def sheet(name,items,note=''):
 im=Image.new('RGB',(640*len(items),884),(17,24,31));d=ImageDraw.Draw(im)
 for i,(path,label) in enumerate(items):
  q=Image.open(path).convert('RGB');assert q.size==(640,800);im.paste(q,(i*640,50));d.text((i*640+16,12),label,font=font,fill='white')
 d.text((16,858),note,font=small,fill=(187,203,214));im.save(P/name)
sheet('FORGE-R14-R15-E15.png',[(ROOT/'anatomy-r14/FBX-face.png','R14 — WYBRANA BAZA'),(ROOT/'realism-r15/FBX-face.png','R15 — ODRZUCONY'),(P/'FBX-face.png','E15 — TWARZ R14, WĘŻSZE WŁOSY')],'Identyczna kamera i oświetlenie. Geometria twarzy E15 pochodzi bez zmian z R14.')
sheet('FORGE-E15-trzy-widoki.png',[(P/'FBX-front.png','E15 — PRZÓD'),(P/'FBX-left.png','E15 — LEWY BOK'),(P/'FBX-back.png','E15 — TYŁ')],'Rendery ponownie zaimportowanego FBX.')
# Evidence crops, preserving aspect ratio. Screenshots do not permit controlled camera/light matching.
items=[('Screenshot_20260912-190442.png',(375,920,707,1335),'MESHY — SCREEN UŻYTKOWNIKA'),(None,None,'ASTRA + BLENDER — E15'),('Screenshot_20260912-190054.png',(373,538,708,957),'MESHY — BEZ TEKSTUR'),(None,None,'E15 — BEZ TEKSTUR')]
canvas=Image.new('RGB',(1600,655),(17,24,31));d=ImageDraw.Draw(canvas)
for i,(src,box,label) in enumerate(items):
 if src:im=Image.open(ROOT/'upload'/src).convert('RGB').crop(box)
 else:im=Image.open(P/('FBX-face.png' if i==1 else 'FBX-face-clay.png')).convert('RGB').crop((70,90,570,790))
 im=ImageOps.contain(im,(390,570),Image.Resampling.LANCZOS);canvas.paste(im,(i*400+(400-im.width)//2,55+(570-im.height)//2));d.text((i*400+9,12),label,font=small,fill='white')
d.text((12,631),'Porównanie wizualne: różne kamery, światło i skala. Meshy ocenione ze screenów; nie badano jego pliku 3D.',font=small,fill=(190,206,218));canvas.save(P/'FORGE-E15-vs-Meshy.png')
print('Comparison sheets ready')
