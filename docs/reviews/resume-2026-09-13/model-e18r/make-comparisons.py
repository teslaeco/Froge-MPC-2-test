from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(s):return ImageFont.truetype(F,s)
bg='#111d26'; fg='#e9f3f7';muted='#b4c6cf'
a=Image.new('RGB',(1280,915),bg);d=ImageDraw.Draw(a)
d.text((18,15),'PRZED — E18, ODZYSKANY GLB',font=font(24),fill=fg)
d.text((655,15),'PO — E18R, KOREKTA NASADY',font=font(24),fill=fg)
for i,n in enumerate(('before-face.png','after-face.png')):a.paste(Image.open(P/n).convert('RGB'),(640*i,58))
d.text((18,875),'Rzeczywiste eksporty GLB. Ta sama kamera i światła. Model sukni, nie nowa Julia w bluzie.',font=font(21),fill=muted)
a.save(P/'E18R-PRZED-PO.png');a.save(P/'E18R-PRZED-PO.webp',quality=93)
b=Image.new('RGB',(1920,915),bg);d=ImageDraw.Draw(b)
for i,(v,l) in enumerate((('front','PRZÓD'),('left','LEWY BOK'),('back','TYŁ'))):
 d.text((i*640+18,15),'E18R — '+l,font=font(26),fill=fg);b.paste(Image.open(P/f'after-{v}.png').convert('RGB'),(640*i,58))
d.text((18,875),'Widoki tego samego poprawionego GLB. Odtworzenie z wersji web: oryginalne tekstury master nie zostały odzyskane.',font=font(22),fill=muted)
b.save(P/'E18R-TRZY-STRONY.png');b.save(P/'E18R-TRZY-STRONY.webp',quality=91)
c=Image.new('RGB',(1200,430),bg);d=ImageDraw.Draw(c)
for i,n in enumerate(('before-face.png','after-face.png')):
 im=Image.open(P/n).convert('RGB').crop((145,88,495,305));im=im.resize((600,372),Image.Resampling.LANCZOS);c.paste(im,(i*600,58))
 d.text((i*600+18,15),'PRZED' if i==0 else 'PO',font=font(26),fill=fg)
c.save(P/'E18R-NASADA-DETAL.png');c.save(P/'E18R-NASADA-DETAL.webp',quality=94)
for v in ('face','front','left','back'):
 Image.open(P/f'after-{v}.png').save(P/f'after-{v}.webp',quality=91)
cloth=Image.new('RGB',(1280,915),bg);d=ImageDraw.Draw(cloth)
for i,n in enumerate(('before-front.png','after-front.png')):
 d.text((640*i+18,15),'ŹRÓDŁO GLB' if i==0 else 'PO — KOREKTA NASADY + SHEEN',font=font(24),fill=fg)
 cloth.paste(Image.open(P/n).convert('RGB'),(640*i,58))
d.text((18,875),'Ta sama ciemna mapa koloru, poprawiona warstwa sheen. Ta sama kamera i oświetlenie.',font=font(21),fill=muted)
cloth.save(P/'E18R-MATERIAL-PRZED-PO.webp',quality=92)
files=['FORGE-E18R.glb','FORGE-E18R-recovered-checkpoint.blend','E18R-PRZED-PO.webp','E18R-TRZY-STRONY.webp','E18R-NASADA-DETAL.webp','E18R-MATERIAL-PRZED-PO.webp','correct.py','render-exports.py','correction-report.json','render-verification.json']
(P/'delivery-manifest.json').write_text(json.dumps({'files':[{'path':n,'bytes':(P/n).stat().st_size,'sha256':hashlib.sha256((P/n).read_bytes()).hexdigest()} for n in files]},indent=2))
