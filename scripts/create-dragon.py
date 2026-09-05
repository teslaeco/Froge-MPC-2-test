"""Codex-authored editable oriental dragon. No external generation service."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'blender_addon'/'froge_studio'))
from geometry import compile_shapes
shapes=[]
def sphere(name,center,size,color,pattern='solid',metalness=0):shapes.append(dict(kind='sphere',name=name,center=center,size=size,color=color,pattern=pattern,metalness=metalness))
def tube(name,points,color,pattern='solid',metalness=0):shapes.append(dict(kind='tube',name=name,points=points,color=color,pattern=pattern,metalness=metalness))
green='#218a56';gold='#eac373';dark='#12563e';red='#b83927'
# A continuous rising serpentine body: two broad coils narrowing toward the tail.
body=[]
for i in range(90):
    t=i/89;a=t*math.pi*3.4
    radius=2.1*(1-.34*t)
    body.append([radius*math.cos(a),.8+6.4*t,radius*.58*math.sin(a),.10+.43*math.sin(math.pi*t*.73)])
tube('Wezowe cialo z luskami',body,green,'scales')
# Gold belly follows the forward face, a thinner continuous tube partially embedded.
belly=[[p[0],p[1]-.12,p[2]+p[3]*.7,p[3]*.62] for p in body[5:]]
tube('Jasny pancerz brzucha',belly,gold,'scales')
head=body[-1][:3];hx,hy,hz=head
sphere('Glowa',[hx,hy+.22,hz+.08],[1.5,1.0,1.2],green,'scales')
sphere('Dlugi pysk',[hx,hy+.03,hz+.76],[1.05,.6,1.3],green,'scales')
sphere('Otwarta paszcza',[hx,hy-.22,hz+.95],[.86,.23,.95],'#441e22')
sphere('Dolna szczeka',[hx,hy-.39,hz+.90],[.92,.21,1.04],gold)
for side in [-1,1]:
    sphere('Oko',[hx+side*.59,hy+.35,hz+.43],[.28,.25,.3],'#fbe38b')
    sphere('Zrenica',[hx+side*.68,hy+.35,hz+.52],[.10,.20,.13],'#121612')
    sphere('Blysk oka',[hx+side*.70,hy+.41,hz+.57],[.05,.06,.05],'#ffffff')
    sphere('Nozdrze',[hx+side*.28,hy+.12,hz+1.3],[.16,.11,.13],'#143626')
    tube('Brew',[[hx+side*.32,hy+.50,hz+.60,.10],[hx+side*.58,hy+.56,hz+.47,.13],[hx+side*.77,hy+.53,hz+.1,.035]],dark)
    tube('Rog glowny',[[hx+side*.44,hy+.56,hz-.12,.17],[hx+side*.59,hy+1.05,hz-.25,.11],[hx+side*.79,hy+1.53,hz-.48,.012]],gold,metalness=.15)
    tube('Odnog rogu',[[hx+side*.58,hy+1.02,hz-.24,.1],[hx+side*.92,hy+1.22,hz-.1,.045],[hx+side*1.06,hy+1.42,hz+.02,.01]],gold)
    tube('Was smoka',[[hx+side*.36,hy-.02,hz+1.2,.045],[hx+side*.85,hy+.04,hz+1.7,.036],[hx+side*1.3,hy+.45,hz+1.8,.025],[hx+side*1.6,hy+.9,hz+1.45,.009]],gold)
    for z in [.6,1.0]:tube('Zab',[[hx+side*.34,hy-.12,hz+z,.07],[hx+side*.33,hy-.32,hz+z+.03,.005]],'#fff0cf')
# Mane spines, each genuinely three-dimensional.
for i in range(12,85,4):
    x,y,z,r=body[i]
    tube('Grzebien grzbietu',[[x,y,z-r*.65,.11],[x,y+.22,z-r-.18,.1],[x,y+.5,z-r-.40,.006]],gold)
for side in [-1,1]:
    for row in range(5):
        tube('Grzywa glowy',[[hx+side*.48,hy+.4-row*.13,hz-.17,.13],[hx+side*(.86+row*.035),hy+.55-row*.17,hz-.45,.12],[hx+side*(1.12+row*.05),hy+.30-row*.21,hz-.75,.006]],red)
# Four articulated legs and twelve curved claws.
for bodyindex,side in [(70,-1),(70,1),(30,-1),(30,1)]:
    x,y,z,r=body[bodyindex]
    points=[[x+side*r*.5,y,z+.15,.21],[x+side*.8,y-.3,z+.42,.19],[x+side*1.06,y-.72,z+.76,.14],[x+side*.82,y-.98,z+1.02,.16]]
    tube('Lapa',points,green,'scales');end=points[-1]
    for toe in [-1,0,1]:
        xx=end[0]+toe*.17
        tube('Palec',[[xx,end[1],end[2],.095],[xx+side*.05,end[1]-.14,end[2]+.22,.075],[xx+side*.08,end[1]-.10,end[2]+.38,.045]],green)
        tube('Pazur',[[xx+side*.08,end[1]-.10,end[2]+.35,.06],[xx+side*.08,end[1]-.19,end[2]+.50,.008]],gold)
# Round display base and clouds, intentionally separate for later print preparation.
sphere('Podstawka',[0,.10,0],[5.7,.25,4.3],'#233a45')
for i in range(10):
    a=i/10*2*math.pi;sphere('Oblok',[2.0*math.cos(a),.39+.12*(i%3),1.3*math.sin(a)],[1.0,.5,.7],'#d6e9e4')
scene=compile_shapes({'version':1,'name':'Smok orientalny — projekt Codexa','description':'Wezowy zielony smok z rogami, wasami, czterema lapami i luskami. Autorski stylizowany szkic inspirowany smokami orientalnymi; nie jest wierna kopia konkretnej postaci. Oddzielne czesci wymagaja scalenia i kontroli przed drukiem.','shapes':shapes})
root=Path(__file__).resolve().parents[1]
(root/'public/models/codex-dragon.froge.json').write_text(json.dumps(scene,separators=(',',':'),ensure_ascii=False))
(root/'public/models/codex-dragon-design.json').write_text(json.dumps({'version':1,'name':scene['name'],'description':scene['description'],'shapes':shapes},ensure_ascii=False,indent=2))
print('Created',len(scene['parts']),'parts;',sum(len(p['triangles'])//3 for p in scene['parts']),'triangles')
