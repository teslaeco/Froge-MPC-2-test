"""Mechanical evidence layout: crops/scales unchanged source pixels; no new 3D renders.

This script preserves uploaded originals. All crops, timestamps and SHA256s are
recorded in evidence-manifest.json so the board can be independently rebuilt.
"""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'resume-review'
SRC = ROOT / 'upload'
BG = '#101923'
FG = '#edf3f7'
MUTED = '#a5bac7'
ACCENT = '#82e0cf'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def font(n):
    return ImageFont.truetype(FONT, n)

def wrap(draw, text, x, y, width, size=22, fill=FG):
    line = ''
    for word in text.split():
        test = f'{line} {word}'.strip()
        if draw.textlength(test, font=font(size)) > width and line:
            draw.text((x,y),line,font=font(size),fill=fill)
            y += int(size*1.4)
            line = word
        else:
            line = test
    if line:
        draw.text((x,y),line,font=font(size),fill=fill)
        y += int(size*1.4)
    return y

def place(canvas, name, box, crop=None):
    im = Image.open(SRC/name).convert('RGB')
    if crop:
        im = im.crop(crop)
    view = ImageOps.contain(im,(box[2]-box[0],box[3]-box[1]))
    canvas.paste(view, (box[0]+(box[2]-box[0]-view.width)//2,box[1]))

ref = 'ChatGPT Image 13 wrz 2026, 02_19_48.png'
failed = 'Screenshot_20260913-025146.png'
atlas = 'Screenshot_20260913-021422.png'
board = Image.new('RGB',(1600,1170),BG)
d=ImageDraw.Draw(board)
d.text((28,20),'JULIA | REFERENCJA A WYNIK ZGŁOSZONY 13.09.2026',font=font(31),fill=FG)
d.text((28,65),'Dokumentacja błędu. Te obrazy nie przedstawiają nowej poprawki modelu.',font=font(22),fill=MUTED)
for x,label in [(28,'REFERENCJA — CAŁA POSTAĆ'),(565,'REFERENCJA — DETAL'),(1080,'WYNIK — SCREEN UŻYTKOWNIKA')]:
    d.text((x,115),label,font=font(20),fill=ACCENT)
place(board,ref,(28,156,532,1035))
place(board,ref,(565,156,1050,800),(333,0,659,420))
place(board,failed,(1080,156,1572,800),(37,632,550,1075))
y=820
for line in ['Oko osadzone we wnęce, nierówny kostny brzeg oczodołu.','Drobne pasma, asymetryczne fale i miękka linia nasady.','Uśmiech, koszulka z okrągłym dekoltem, rozpięta bluza.']:
    y=wrap(d,line,565,y,480,size=22)+15
y=610
for line in ['Okrągły oczodół i czarna kulka oka.','Grube, odcięte pasma włosów.','Zbyt prosta szyja; brak uśmiechu referencji.','Kadr ucina czubek głowy. Pełnej sylwetki Julii nie ma w tym screenie.']:
    y=wrap(d,line,1080,y,490,size=22)+14
d.line((28,1055,1572,1055),fill='#344b5c',width=2)
wrap(d,'Zlecenie Julia: 076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d. Różne kamery, kadry i oświetlenie. Bez pomiaru głębokości i bez oceny pliku 3D.',28,1075,1540,size=21,fill=MUTED)
board.save(OUT/'JULIA-reference-vs-reported-failure.png')
board.save(OUT/'JULIA-reference-vs-reported-failure.webp',quality=92)

atlas_board=Image.new('RGB',(1140,790),BG)
d=ImageDraw.Draw(atlas_board)
d.text((28,20),'ATLAS | ODDZIELNY PRZYPADEK — FIGURKA Z OPISU',font=font(28),fill=FG)
place(atlas_board,atlas,(28,100,425,725),(408,889,578,1310))
y=105
for line in ['To jest screen wyniku, nie zdjęcie referencyjne.','Widoczne uproszczenia: sztywna poza, pudełkowe kieszenie, gładka twarz i niewiele dużych fałd ubrania.','Nie można ocenić zgodności z pełnym promptem: załącznik pokazuje tylko jego początek.','Do oceny po poprawce potrzebne są: ten sam prompt, eksport GLB/FBX, przód/bok/tył, twarz, ubranie i buty.','Zlecenie: b653826a-1b24-44f5-a881-c0e0c2492a18.']:
    y=wrap(d,line,465,y,640,size=23)+20
d.text((28,747),'Nie porównujemy Atlasa do Julii ani do modelu kobiety w sukni.',font=font(21),fill=MUTED)
atlas_board.save(OUT/'ATLAS-reported-failure.png')
atlas_board.save(OUT/'ATLAS-reported-failure.webp',quality=92)

contact=Image.new('RGB',(1140,1410),BG)
d=ImageDraw.Draw(contact)
d.text((18,15),'WIDEO UŻYTKOWNIKA — KLATKI KONTROLNE',font=font(26),fill=FG)
for idx,t in enumerate((0,5,10,15,20,25)):
    x=18+(idx%3)*375;y=65+(idx//3)*667
    d.text((x,y),f'{t:.1f} s',font=font(20),fill=ACCENT)
    im=Image.open(OUT/'frames'/f't-{t:02d}.jpg')
    contact.paste(im,(x,y+28))
contact.save(OUT/'video-contact.jpg',quality=87)

names=[ref,failed,atlas,'Screenshot_20260913-025123.png','Screenshot_20260913-025017.png','Screenshot_20260912-230917.png','886d2ed4263a4f285877eb1b43de90a2.mp4']
manifest={
    'status':'input_evidence_only_not_corrected_model',
    'method':'Mechanical crop, uniform resize and annotation; original pixels preserved without generative editing.',
    'sources':[{ 'path':'upload/'+n, 'bytes':(SRC/n).stat().st_size, 'sha256':hashlib.sha256((SRC/n).read_bytes()).hexdigest(), 'size_px':list(Image.open(SRC/n).size) if n.endswith('.png') else None } for n in names],
    'julia_job_id':'076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d',
    'atlas_job_id':'b653826a-1b24-44f5-a881-c0e0c2492a18',
    'crops_xyxy':{'julia_reference_face':[333,0,659,420],'julia_failed_viewport':[37,632,550,1075],'atlas_model':[408,889,578,1310]},
    'video':{'duration_seconds':29.833333,'width':1080,'height':1920,'frame_timestamps_seconds':[0,5,10,15,20,25],'classification':'Social screenshot montage; prior Meshy/FORGE comparisons. Not a clean model orbit and not capsule animation.'},
}
(OUT/'evidence-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
