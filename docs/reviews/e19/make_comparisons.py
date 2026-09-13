from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,hashlib,shutil
R=Path('/workspace/scratch/584c9d97a5a1');D=R/'e19/final';A=R/'public-resume/dist/assets'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(n):return ImageFont.truetype(font,n)
def board(items,labels,name,w=600,h=750,note='Rzeczywiste rendery ponownie importowanych GLB. Ta sama kamera i światło dla przed/po.'):
 im=Image.new('RGB',(w*len(items),h+118),'#111c25');dr=ImageDraw.Draw(im)
 for i,(src,label) in enumerate(zip(items,labels)):
  p=Image.open(src).convert('RGB') if not isinstance(src,Image.Image) else src.convert('RGB')
  p=ImageOps.contain(p,(w-16,h));im.paste(p,(i*w+(w-p.width)//2,58+(h-p.height)//2));dr.text((i*w+18,14),label,font=f(24),fill='#f2f5f7')
 dr.text((18,h+77),note,font=f(18),fill='#b6c5cc');im.save(D/(name+'.png'));im.save(A/(name+'.webp'),quality=91,method=6)
board([D/'before-face.png',D/'after-face.png'],['PRZED · E18R','PO · E19'],'E19-PRZED-PO',800,1000)
board([D/'before-front.png',D/'after-front.png'],['TORS · E18R','TORS · E19'],'E19-TORSO',640,800)
if all((D/f'after-{v}.png').exists() for v in ['front','left','right','back']):
 board([D/f'after-{v}.png' for v in ['front','left','right','back']],['PRZÓD','LEWY BOK','PRAWY BOK','TYŁ'],'E19-WIDOKI',480,600,note='E19 · rzeczywiste rendery modelu. Widoki niewidoczne w referencji są interpretacją.')
for v in ['front','left','right','back','face','underside']:
 p=D/f'after-{v}.png'
 if p.exists():Image.open(p).save(A/f'model-{v}.webp',quality=92,method=6)
ref=Image.open(R/'upload/Screenshot_20260912-170529(3).png').crop((70,230,730,1170))
meshy=Image.open(A/'comparison.webp').crop((145,233,477,642))
after=Image.open(D/'after-face.png').crop((40,80,760,920))
board([ref,meshy,after],['REFERENCJA','MESHY · screen użytkownika','FORGE E19 · render GLB'],'E19-MESHY',540,720,note='Różne kamery, skala i światło. Meshy oceniony ze screenu; nie badaliśmy jego pliku 3D.')
a=Image.open(D/'before-face.png').crop((230,515,585,760));b=Image.open(D/'after-face.png').crop((230,515,585,760))
board([a,b],['UZĘBIENIE · E18R','UZĘBIENIE · E19'],'E19-TEETH',710,490,note='Zmiana geometrii koron, łuków, osadzenia i wnętrza ust. Uśmiech nadal wymaga oceny podobieństwa.')
manifest={'method':'mechanical crops/layout of actual renders and supplied screenshot, no generated replacements','meshy_source':'previous published comparison.webp top-left user screenshot panel','reference':'Screenshot_20260912-170529(3).png','model_sha256':json.loads((D/'build-report.json').read_text())['versions']['web']['sha256'],'boards':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('E19-*.png')}}
(D/'comparison-manifest.json').write_text(json.dumps(manifest,indent=2))
print(list(manifest['boards']))
