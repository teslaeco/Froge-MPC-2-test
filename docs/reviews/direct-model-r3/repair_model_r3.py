"""Direct repair of the downloaded 5280cdee draft. No generator update/API."""
import bpy,bmesh,math,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
OUT=Path('/workspace/scratch/584c9d97a5a1/model-repair')
original=Path('/workspace/scratch/model.blend')
# Opened by Blender with auto-execution disabled. Retain the original separately.
bpy.context.view_layer.update()
for obj in list(bpy.context.scene.objects):
 if obj.name.startswith(('Fitted_chestnut_scalp','Rooted_wave_','Inferred_back_lock_')):
  bpy.data.objects.remove(obj,do_unlink=True)
# Work in world coordinates so every anatomical and skeletal component follows
# the same proportions, including the actual eye, lashes, teeth and UV surface.
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 for v in obj.data.vertices:v.co=obj.matrix_world@v.co
 obj.matrix_world=Matrix.Identity(4)
 for v in obj.data.vertices:
  x,y,z=v.co
  if z>1.32:
   w=min(1,max(0,(z-1.40)/.10));w=w*w*(3-2*w)
   x*=1+.15*w
   z=1.32+(z-1.32)*(.12/.18) if z<1.50 else 1.44+(z-1.50)*1.16
  v.co=(x,y,z)
 obj.data.update()
# Align the separate neck with the actual cervical cross-section: its
# original upper ring was about 10 cm in front of the head's neck.
for name in ('Living_neck_chest','Skeletal_neck_chest'):
 ob=bpy.data.objects[name]
 for vv in ob.data.vertices:
  w=max(0,min(1,(vv.co.z-1.28)/.15));w=w*w*(3-2*w)
  vv.co.y+=.10*w
 ob.data.update()
# Seat the existing teeth farther inside the mouth; reduce the bead-like scale.
for obj in bpy.context.scene.objects:
 if obj.name.startswith(('Upper_tooth_','Lower_tooth_','Living_smile_tooth_')):
  c=sum((v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
  for v in obj.data.vertices:
   q=v.co-c;q.x*=.94;q.z*=.82;v.co=c+q+Vector((0,.003,0))
  if obj.name.startswith('Living_smile'):
   for v in obj.data.vertices:v.co.y+=.008
# Keep the original packed 2K skin atlas on the face and warm the neck colour.
skin=bpy.data.materials.get('Living_skin_clean')
if skin and skin.use_nodes:
 shader=skin.node_tree.nodes.get('Principled BSDF')
 if shader:shader.inputs['Roughness'].default_value=.65
for name in ('Half_mandible','Zygomatic_arch'):
 obj=bpy.data.objects.get(name)
 if obj:
  mod=obj.modifiers.new('Gentle bone continuity','SUBSURF');mod.levels=1;mod.render_levels=1
  for p in obj.data.polygons:p.use_smooth=True
head=bpy.data.objects['anatomical-head']
bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
# A portable image texture with fine longitudinal strands, not a glossy solid
# black material. The file contains this actual packed texture for GLB export.
n=1024
u=np.arange(n)[None,:]/n;v=np.arange(n)[:,None]/n
rng=np.random.default_rng(20260912)
f=.72+.14*np.sin(2*math.pi*(u*131+.12*np.sin(v*17)))+.08*np.sin(u*math.pi*503)+rng.random((n,n))*.09
pixels=np.ones((n,n,4),dtype=np.float32)
base=np.array([.16,.065,.023]);pixels[:,:,:3]=np.clip(f[:,:,None]*base[None,None,:],0,1)
im=bpy.data.images.new('Chestnut_fine_strands_1024',width=n,height=n,alpha=False)
im.pixels.foreach_set(pixels.ravel());im.update();im.pack()
hair=bpy.data.materials.new('Repair_chestnut_hair');hair.use_nodes=True
bs=hair.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.07,.025,.009,1);bs.inputs['Roughness'].default_value=.64
bs.inputs['Specular IOR Level'].default_value=.23
tex=hair.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
hair.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
def mesh(name,verts,faces,uv=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);me.materials.append(hair)
 if uv:
  layer=me.uv_layers.new(name='HairUV')
  for loop in me.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
 for p in me.polygons:p.use_smooth=True
 return ob
# Scalp follows the real head rather than a floating hemisphere above it.
verts=[];faces=[];uv=[];index={}
for p in head.data.polygons:
 c=p.center
 hairline=1.688-.07*min(1,abs(c.x)/.12)
 if not (c.z>1.575 and (c.y>.048 or c.z>hairline)):continue
 face=[]
 for vi in p.vertices:
  if vi not in index:
   vv=head.data.vertices[vi];point=vv.co+vv.normal*.004
   index[vi]=len(verts);verts.append(tuple(point));uv.append((math.atan2(point.x,point.y-.06)/math.tau+.5,(point.z-1.40)/.36))
  face.append(index[vi])
 faces.append(face)
cap=mesh('Repair_fitted_scalp',verts,faces,uv)
# Dense continuous rear hair volume closes the exposed nape/back scalp.
verts=[];faces=[];uv=[];rows=85;cols=121
for i in range(rows):
 t=i/(rows-1);z=1.730-.67*t
 r=.006+.145*math.sin(min(1,t/.22)*math.pi/2)
 for j in range(cols):
  a=-1.77+3.54*j/(cols-1)
  wave=(.007*math.sin(19*t+2*a)+.004*math.sin(34*t+a))*math.sin(math.pi*t)
  radius=r+wave+.0015*math.sin(90*a+7*t)**2
  x=radius*math.sin(a);y=.064+radius*.85*math.cos(a)
  zt=z+.045*math.sin(3*a)*t**3+.03*math.sin(7*a)*t**6-.06*math.cos(2*a)*t**3
  if t<.30:
   direction=Vector((math.sin(a),math.cos(a),0))
   hit,normal,_,_=bvh.ray_cast(Vector((0,.064,zt))+direction*.5,-direction)
   if hit is not None:
    blend=max(0,min(1,(.30-t)/.10))
    fitted=hit+normal*.009
    x=x*(1-blend)+fitted.x*blend;y=y*(1-blend)+fitted.y*blend
  verts.append((x,y,zt));uv.append((j/(cols-1),t))
  if i and j:
   k=i*cols+j;faces.append((k-cols-1,k-cols,k,k-1))
back=mesh('Repair_continuous_back_hair',verts,faces,uv)
solid=back.modifiers.new('Hair volume','SOLIDIFY');solid.thickness=.013;solid.offset=-1
# Asymmetric broad waves, with narrow roots fitted onto the actual head.
for side in (-1,1):
 for j in range(11):
  phase=j*.71+(0 if side<0 else .6)
  end=(.93 if side<0 else 1.06)+.026*math.sin(j*1.7)
  top=1.729-.005*j
  root=.004+.006*j
  edge=.112+.006*j
  samples=120;sides=24
  start=Vector((side*(.003+.006*j),-.2,1.724-.003*j))
  hit,normal,_,_=bvh.ray_cast(start,Vector((0,1,0)))
  if hit is None:hit,normal,_,_=bvh.find_nearest(Vector((start.x,.065,start.z)))
  p0=hit+normal*.009
  points=[p0,Vector((side*(.057+.005*j),.022+.003*j,1.683-.003*j)),
          Vector((side*(.11+.004*j),-.005+.004*j,1.59-.004*j)),
          Vector((side*(.13+.005*j),-.035+.004*j,1.46)),
          Vector((side*(.135+.004*j),-.105+.003*j,1.30)),
          Vector((side*(.13+.004*j),-.115+.002*j,1.14)),
          Vector((side*(.15+.003*j),-.11,end))]
  centers=[]
  for i in range(samples):
   t=i/(samples-1);q=t*(len(points)-1);k=min(len(points)-2,int(q));u=q-k
   a0=points[max(0,k-1)];a1=points[k];a2=points[k+1];a3=points[min(len(points)-1,k+2)]
   c=.5*((2*a1)+(-a0+a2)*u+(2*a0-5*a1+4*a2-a3)*u*u+(-a0+3*a1-3*a2+a3)*u*u*u)
   wave=math.sin(math.pi*max(0,(t-.25)/.75))
   c.x+=side*.018*math.sin(16*t+phase*.4)*wave
   c.y+=.007*math.sin(15*t+phase*.4)*wave
   centers.append(c)
  verts=[];faces=[];uv=[]
  for i,c in enumerate(centers):
   t=i/(samples-1)
   tangent=(centers[min(i+1,samples-1)]-centers[max(i-1,0)]).normalized()
   across=tangent.cross(Vector((0,1,0))).normalized();depth=tangent.cross(across).normalized()
   width=(.006+.010*math.sin(math.pi*t)**.45)*max(.025,(1-t)**.42)
   thick=width*.52
   for k in range(sides):
    a=math.tau*k/sides;ridge=1+.025*math.cos(9*a+2*t)
    point=c+across*(math.cos(a)*width*ridge)+depth*(math.sin(a)*thick)
    verts.append(tuple(point));uv.append((k/sides+j*.087,t))
    if i:
     b=i*sides+k;faces.append((b-sides,(i-1)*sides+(k+1)%sides,i*sides+(k+1)%sides,b))
  faces.append(tuple(reversed(range(sides))));faces.append(tuple((samples-1)*sides+k for k in range(sides)))
  mesh('Repair_wave_%s_%02d'%(side,j),verts,faces,uv)
# Save an editable revision; acceptance remains with Sebastian.
bpy.context.scene['repair_revision']='direct-model-r3'
bpy.context.scene['reference_likeness_accepted']=False
bpy.context.scene['source_model_sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
for im in bpy.data.images:
 if not im.packed_file and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-poprawka-r3.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-poprawka-r3.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
(OUT/'repair-report.json').write_text(json.dumps({'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'revision':'r3','changes':['shared head/neck proportion correction','fitted scalp replacing floating cap','continuous rear hair','asymmetric chestnut waves','teeth inset and reduced height','gentle bone subdivision'],'likeness_accepted':False,'remaining':['facial likeness and smile','central facial seam and dental anatomy','garment folds and sleeves','unseen back is inferred']},indent=2))
print('REPAIR_R3_SAVED',flush=True)
