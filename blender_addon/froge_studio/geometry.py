"""Bounded, data-only modeling. Centimetres, Y up. No eval/exec or cloud API."""
import math
import re

VEC = {'type':'array','items':{'type':'number','minimum':-10000,'maximum':10000},'minItems':3,'maxItems':3}
SHAPE_SCHEMA = {'type':'object','additionalProperties':False,'properties':{
 'version':{'const':1},'name':{'type':'string','minLength':1,'maxLength':160},'description':{'type':'string','maxLength':2000},
 'shapes':{'type':'array','minItems':1,'maxItems':128,'items':{'type':'object','additionalProperties':False,'properties':{
  'kind':{'enum':['sphere','box','tube','mesh']},'name':{'type':'string','maxLength':100},'center':VEC,'size':VEC,
  'points':{'type':'array','minItems':2,'maxItems':128,'items':{'type':'array','items':{'type':'number'},'minItems':4,'maxItems':4}},
  'vertices':{'type':'array','items':{'type':'number'},'maxItems':15000},'triangles':{'type':'array','items':{'type':'integer','minimum':0},'maxItems':30000},
  'color':{'type':'string','pattern':'^#[0-9a-fA-F]{6}$'},'roughness':{'type':'number','minimum':0,'maximum':1},'metalness':{'type':'number','minimum':0,'maximum':1},'pattern':{'enum':['solid','scales','bark']}},'required':['kind','name','color']}}},'required':['version','name','description','shapes']}

def number(v, limit=10000):
    if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or abs(v)>limit:
        raise ValueError('Wspolrzedne musza byc skonczonymi liczbami w dozwolonym zakresie.')
    return float(v)

def vec(v, length=3):
    if not isinstance(v,list) or len(v)!=length: raise ValueError('Nieprawidlowy wektor.')
    return [number(x) for x in v]

def unit(v):
    length=math.sqrt(sum(x*x for x in v))
    if length<1e-9: raise ValueError('Punkty osi rury nie moga sie powtarzac.')
    return [x/length for x in v]

def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def validate_scene(scene):
    if not isinstance(scene,dict) or set(scene)!={'version','name','description','parts'} or scene['version']!=1: raise ValueError('Nieprawidlowy format sceny Froge.')
    if not isinstance(scene['name'],str) or not 1<=len(scene['name'])<=160 or not isinstance(scene['description'],str) or len(scene['description'])>2000: raise ValueError('Nieprawidlowa nazwa/opis.')
    parts=scene['parts']
    if not isinstance(parts,list) or not 1<=len(parts)<=256: raise ValueError('Scena wymaga 1-256 czesci.')
    total=0
    for p in parts:
        if not isinstance(p,dict) or set(p)!={'name','vertices','triangles','uv','color','roughness','metalness','pattern'}: raise ValueError('Nieprawidlowe pola czesci.')
        if not isinstance(p['name'],str) or not 1<=len(p['name'])<=100: raise ValueError('Nieprawidlowa nazwa czesci.')
        v,t,uv=p['vertices'],p['triangles'],p['uv']
        if not all(isinstance(x,list) for x in (v,t,uv)): raise ValueError('Oczekiwano tablic siatki.')
        if not 9<=len(v)<=150000 or len(v)%3 or not 3<=len(t)<=300000 or len(t)%3 or len(uv)!=len(v)//3*2: raise ValueError('Nieprawidlowy rozmiar siatki.')
        for x in v: number(x)
        for x in uv: number(x,1000)
        if any(type(i)!=int or i<0 or i>=len(v)//3 for i in t): raise ValueError('Indeks poza siatka.')
        if not isinstance(p['color'],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',p['color']): raise ValueError('Kolor wymaga #RRGGBB.')
        for k in ('roughness','metalness'):
            if not 0<=number(p[k],1)<=1: raise ValueError('Material wymaga zakresu 0-1.')
        if p['pattern'] not in ('solid','scales','bark'): raise ValueError('Nieznana tekstura.')
        total+=len(v)
    if total>600000: raise ValueError('Limit 200000 wierzcholkow.')
    return scene

def compile_shapes(data):
    if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('shapes'),list) or not 1<=len(data['shapes'])<=128: raise ValueError('Nieprawidlowy projekt AI.')
    result={'version':1,'name':data.get('name','Model'),'description':data.get('description',''),'parts':[]}
    for shape in data['shapes']:
        v,t,uv=[],[],[]
        def vertex(p,u=0,w=0):
            v.extend(p);uv.extend([u,w]);return len(v)//3-1
        kind=shape.get('kind')
        if kind in ('sphere','box'):
            c=vec(shape.get('center',[0,0,0]));s=vec(shape.get('size',[1,1,1]))
            if any(x<=0 for x in s): raise ValueError('Wielkosc musi byc dodatnia.')
        if kind=='sphere':
            rings,sides=16,32
            for j in range(rings+1):
                a=math.pi*j/rings
                for i in range(sides+1):
                    b=2*math.pi*i/sides
                    vertex([c[0]+s[0]/2*math.sin(a)*math.cos(b),c[1]+s[1]/2*math.cos(a),c[2]+s[2]/2*math.sin(a)*math.sin(b)],i/sides,j/rings)
            for j in range(rings):
                for i in range(sides):
                    a=j*(sides+1)+i;b=a+sides+1
                    if j>0:t.extend([a,a+1,b])
                    if j<rings-1:t.extend([a+1,b+1,b])
        elif kind=='box':
            for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:vertex([c[0]+x*s[0]/2,c[1]+y*s[1]/2,c[2]+z*s[2]/2],(x+1)/2,(y+1)/2)
            t=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,3,7,6,3,6,2,0,4,7,0,7,3,1,2,6,1,6,5]
        elif kind=='tube':
            points=shape.get('points',[])
            if not isinstance(points,list) or not 2<=len(points)<=128: raise ValueError('Rura wymaga 2-128 punktow [x,y,z,promien].')
            points=[vec(p,4) for p in points];sides=20;previous=None
            for j,p in enumerate(points):
                if not 0<p[3]<=1000:raise ValueError('Promien musi byc dodatni.')
                before=points[max(0,j-1)];after=points[min(len(points)-1,j+1)]
                tangent=unit([after[k]-before[k] for k in range(3)])
                if previous:
                    dot=sum(previous[k]*tangent[k] for k in range(3));normal=[previous[k]-dot*tangent[k] for k in range(3)]
                    if sum(x*x for x in normal)<1e-8:normal=cross(tangent,[1,0,0] if abs(tangent[0])<.8 else [0,1,0])
                    normal=unit(normal)
                else:normal=unit(cross(tangent,[1,0,0] if abs(tangent[0])<.8 else [0,1,0]))
                binormal=cross(tangent,normal);previous=normal
                for i in range(sides+1):
                    a=2*math.pi*i/sides;vertex([p[k]+p[3]*(normal[k]*math.cos(a)+binormal[k]*math.sin(a)) for k in range(3)],i/sides,j/(len(points)-1))
            for j in range(len(points)-1):
                for i in range(sides):
                    a=j*(sides+1)+i;b=a+sides+1;t.extend([a,a+1,b,a+1,b+1,b])
            start=vertex(points[0][:3],.5,.5);end=vertex(points[-1][:3],.5,.5);base=(len(points)-1)*(sides+1)
            for i in range(sides):t.extend([start,i+1,i,end,base+i,base+i+1])
        elif kind=='mesh':
            v=list(shape.get('vertices',[]));t=list(shape.get('triangles',[]))
            uv=[0.]*(len(v)//3*2)
        else: raise ValueError('Nieznany typ geometrii.')
        result['parts'].append({'name':shape.get('name','Czesc'),'vertices':[round(x,6) for x in v],'triangles':t,'uv':[round(x,6) for x in uv],'color':shape.get('color','#999999'),'roughness':shape.get('roughness',.6),'metalness':shape.get('metalness',0.),'pattern':shape.get('pattern','solid')})
    return validate_scene(result)

def texture_pixels(color,pattern,size=128):
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)];pixels=[]
    for y in range(size):
        for x in range(size):
            f=1
            if pattern=='scales':
                xx=((x+(y//16%2)*8)%16-8)/8;yy=(y%16)/16;f=.55 if xx*xx+yy*yy>.86 else .92+.08*(1-yy)
            if pattern=='bark':f=.58+.42*(.5+.5*math.sin(x*.65+math.sin(y*.15)*2))
            pixels.extend([*(c*f for c in rgb),1])
    return pixels
