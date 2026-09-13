"""E19 reusable, deterministic dental/orbital correction. Call apply() on E18R.
Only changes dental/orbit objects and a small orbital-rim area; preserves head extent.
Not a clinical model or proof of manufacturing suitability.
"""
import bpy, bmesh, math, json
import numpy as np
from mathutils import Vector
from pathlib import Path

def mat(name,col,rough=.4):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough
 p.inputs['IOR'].default_value=1.46
 return m

def mesh(name,vs,fs,material):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(material)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 return o

def ellipsoid(name,center,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=center);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def arc(x):return -.023 + .043*(abs(x)/.044)**1.9

def rise(x):return .0080*(abs(x)/.044)**1.6

def crown(name,x,width,height,upper,kind,material):
 # Smooth cross-sections give crowns, not bevelled boxes. Cervical root is seated in gum.
 y=arc(x)+(0 if upper else .0024)
 tip=1.4495+rise(x) if upper else 1.4481+rise(x)
 sign=1 if upper else -1
 slope=1.9*.043/.044*(abs(x)/.044)**.9*(1 if x>0 else -1)
 tangent=Vector((1,slope,0)).normalized();normal=Vector((slope,-1,0)).normalized()
 vs=[];fs=[];rings=19;around=40;depth=.0039 if kind in ['central','lateral'] else .0057
 for j in range(rings):
  t=j/(rings-1)
  # tip t=0, cervical t=1. A small closed cap avoids exposed bottoms.
  taper=.72+.29*math.sin(math.pi*t*.88)
  if j==0:taper=.65
  if j==rings-1:taper=.60
  for k in range(around):
   a=2*math.pi*k/around;cs=math.cos(a);sn=math.sin(a)
   localx=math.copysign(abs(cs)**.68,cs)*width*.5*taper
   localy=math.copysign(abs(sn)**.83,sn)*depth*.5*(.68+.35*math.sin(math.pi*t))
   # central cutting edge rounded at corners; canine tip carries one gentle cusp.
   dz=.00045*(abs(cs)**3)*(1-t)**3
   if kind=='canine':dz += .00125*(abs(cs)**1.2)*(1-t)**3
   if kind=='premolar':dz += .00050*(1-abs(sn))*(1-t)**3
   pos=Vector((x,y,tip+sign*(height*t+dz+(.0050*t**4 if upper else 0))))+tangent*localx+normal*localy
   vs.append(tuple(pos))
 for j in range(rings-1):
  for k in range(around):
   a=j*around+k;b=j*around+(k+1)%around;fs.append((a,b,b+around,a+around) if upper else (a,a+around,b+around,b))
 fs.append(tuple(range(around-1,-1,-1)) if upper else tuple(range(around)))
 fs.append(tuple((rings-1)*around+k for k in range(around)) if upper else tuple((rings-1)*around+k for k in range(around-1,-1,-1)))
 o=mesh(name,vs,fs,material);o['anatomical_role']='upper_tooth' if upper else 'lower_tooth';o['tooth_type']=kind
 return o

def gum_arc(name,side,upper,material):
 vs=[];fs=[];steps=76;n=28
 for j in range(steps):
  u=j/(steps-1)
  x=side*(.043*min(1,u/.78)-.027*max(0,(u-.78)/.22));y=arc(side*.043*min(1,u/.78))+.0030+max(0,(u-.78)/.22)*.062
  # root bed closes the gaps behind each crown and runs into jaw/maxilla.
  z=(1.4650 if upper else 1.4397)+rise(x)+(1 if upper else -1)*.018*max(0,(u-.78)/.22)
  slope=1.9*.043/.044*(abs(x)/.044)**.9*side
  norm=Vector((slope,-1,0)).normalized()
  for k in range(n):
   a=2*math.pi*k/n
   p=Vector((x,y,z))+norm*(math.cos(a)*.0045)+Vector((0,0,math.sin(a)*.0038))
   vs.append(tuple(p))
 for j in range(steps-1):
  for k in range(n):a=j*n+k;b=j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(range(n-1,-1,-1)));fs.append(tuple((steps-1)*n+k for k in range(n)))
 return mesh(name,vs,fs,material)

def apply():
 if bpy.context.scene.get('E19_dental_applied'):raise RuntimeError('E19 dental patch already applied; reload source before applying twice')
 old=[]
 for o in list(bpy.context.scene.objects):
  if o.name.startswith(('Anatomical_upper_tooth','Anatomical_lower_tooth','R14 recessed')) or o.name in ['anatomical-eye-l','Recessed oral cavity']:
   old.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 enamel=mat('E19 warm ivory enamel',(.58,.515,.392),.32)
 aged=mat('E19 aged enamel',(.43,.37,.26),.45)
 living_gum=mat('E19 recessed living gingiva',(.16,.043,.033),.59)
 bone_gum=mat('E19 alveolar bone shade',(.145,.13,.087),.68)
 interior=mat('E19 closed oral interior',(.008,.002,.002),.9)
 enamel.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.06
 ellipsoid('E19 closed oral backing',(0,.064,1.453),(.050,.038,.020),interior)
 # The lower/upper arches meet closed root beds, instead of isolated floating teeth.
 specs=[(.0047,.0091,.0130,'central'),(.0130,.0074,.0105,'lateral'),(.0203,.0070,.0118,'canine'),(.0271,.0064,.0091,'premolar'),(.0335,.0065,.0086,'premolar'),(.0395,.0070,.0082,'molar')]
 for side in [-1,1]:
  for i,(x,w,h,k) in enumerate(specs):
   crown('E19 upper %s %s'%(side,i),side*x,w,h,True,k,enamel if side<0 else aged)
   crown('E19 lower %s %s'%(side,i),side*(x*.93),w*.88,h*.57,False,k,enamel if side<0 else aged)
  gum_arc('E19 upper root bed %s'%side,side,True,living_gum if side<0 else bone_gum)
  gum_arc('E19 lower root bed %s'%side,side,False,living_gum if side<0 else bone_gum)
 # Local rim correction reduces the oversized vertical opening without changing the head envelope.
 head=bpy.data.objects.get('anatomical-head')
 rim_vertices=0
 if head:
  co=np.empty(len(head.data.vertices)*3,dtype=np.float32);head.data.vertices.foreach_get('co',co);co=co.reshape(-1,3)
  dx=co[:,0]-.0423;dz=co[:,2]-1.552
  radial=np.sqrt((dx/.039)**2+(dz/.033)**2)
  w=np.exp(-((radial-1)/.42)**2)*np.clip((.058-co[:,1])/.05,0,1)*np.clip(co[:,0]/.012,0,1)
  rim_vertices=int(np.count_nonzero(w>.05));co[:,0]-=dx*.045*w;co[:,2]-=dz*.105*w
  head.data.vertices.foreach_set('co',co.ravel());head.data.update()
 # Retain a present eye as the reference requires, smaller and dark with no protruding white sclera.
 sclera=mat('E19 orbital deep charcoal',(.006,.006,.0045),.35)
 iris=mat('E19 recessed umber iris',(.013,.009,.005),.27)
 pupil=mat('E19 recessed pupil',(.001,.001,.0008),.20)
 eye=ellipsoid('anatomical-eye-l',(.0423,.048,1.5515),(.0120,.0120,.0120),sclera);eye['anatomical_role']='eye';eye['eye_state']='recessed_present'
 ellipsoid('E19 recessed iris',(.0423,.0363,1.5515),(.0060,.00075,.0060),iris)
 ellipsoid('E19 recessed pupil',(.0423,.0357,1.5515),(.0031,.00044,.0031),pupil)
 # Remove grey-faceted cup appearance: existing hollow cup gets smooth normals and black depth.
 cup=bpy.data.objects.get('Recessed_empty_orbit')
 if cup:
  cup.data.materials.clear();cup.data.materials.append(mat('E19 orbital cavity',(.004,.0042,.0035),.95))
  for p in cup.data.polygons:p.use_smooth=True
  cup['eye_state']='recessed_present'
 bpy.context.scene['E19_dental_applied']=True
 report={'removed':old,'new_upper_teeth':12,'new_lower_teeth':12,'root_beds':4,'orbital_eye_diameter_m':.024,'global_head_scale_changed':False,'local_orbital_rim_vertices':rim_vertices,'orbital_rim_vertical_inset_fraction':.105,'oral_backing':'closed recessed mesh','limitations':['Root beds overlap jaw; no boolean union or manufacturing certification.','Skull and living face shape remain approximate; single front reference cannot establish side anatomy.','E19 changes no global head size.']}
 return report

if __name__=='__main__':
 report=apply();out=Path('/workspace/scratch/584c9d97a5a1/e19/dental');out.mkdir(parents=True,exist_ok=True)
 (out/'dental-report.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'dental-test.blend'))
 print('E19_DENTAL_DONE')
