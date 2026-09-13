from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
P=Path(__file__).parent
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
def sheet(items,name,note):
 w,h=640,800; out=Image.new('RGB',(w*len(items),h+90),'#111923');d=ImageDraw.Draw(out)
 for j,(file,label) in enumerate(items):
  out.paste(Image.open(P/file).convert('RGB'),(j*w,38));d.text((j*w+16,8),label,font=font,fill='#eeeeee')
 d.text((16,h+52),note,font=font,fill='#b5c2cf');out.save(P/name)
sheet([('before-face.png','E15 — PRZED'),('after-face.png','E16 — PO'),('after-angle.png','E16 — UKOS')],'POROWNANIE-E16.png','Ta sama kamera i światło dla E15/E16. Rendery ponownie wczytanych plików FBX.')
sheet([('after-front.png','E16 — PRZÓD'),('after-left.png','E16 — LEWY BOK'),('after-back.png','E16 — TYŁ')],'WIDOKI-E16.png','Widoki tego samego modelu E16. Tył jest interpretacją: brak referencji tylnej.')
sheet([('before-clay.png','E15 — GEOMETRIA'),('after-clay.png','E16 — GEOMETRIA')],'GEOMETRIA-E16.png','Bez tekstur; identyczna kamera i oświetlenie.')
