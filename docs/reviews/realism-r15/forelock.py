import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15'
rng=np.random.default_rng(916)
mats=[bpy.data.materials['R15 chestnut fibre %02d'%i] for i in range(12)]
def mesh(name,vs,fs,uvs,inds):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for m in mats:me.materials.append(m)
 layer=me.uv_layers.new(name='HairFlow')
 for p in me.polygons:
  p.use_smooth=True;p.material_index=inds[p.index]
  for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
 return o
# Tube frames follow the existing accepted wave guide; UVs run along each fibre.
def tube(vs,fs,uvs,inds,centres,radii,axis,other,mi):
 base=len(vs);n=len(centres);cols=4
 for i,(c,r) in enumerate(zip(centres,radii)):
  aa=axis[i]/max(1e-9,np.linalg.norm(axis[i]));bb=other[i]/max(1e-9,np.linalg.norm(other[i]));bb-=aa*np.dot(aa,bb);bb/=max(1e-9,np.linalg.norm(bb))
  for j in range(cols):
   t=math.tau*j/cols;vs.append(tuple(c+r*(math.cos(t)*aa+math.sin(t)*bb)));uvs.append((j/cols,i/(n-1)))
   if i:fs.append((base+(i-1)*cols+j,base+i*cols+j,base+i*cols+(j+1)%cols,base+(i-1)*cols+(j+1)%cols));inds.append(mi)
 fs.append(tuple(base+j for j in reversed(range(cols))));inds.append(mi);fs.append(tuple(base+(n-1)*cols+j for j in range(cols)));inds.append(mi)

head=bpy.data.objects['anatomical-head'];tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
count=0
for side in (-1,1):
 vs=[];fs=[];uvs=[];inds=[]
 for j in range(800):
  u=(j+.5)/800;centres=[];n=81
  for i in range(n):
   t=i/(n-1);x=.006+side*(.001+(.115+.018*u)*math.sin(t*math.pi/2));z=1.678+.002*math.sin(math.pi*u)-(.122+.056*u)*t**1.30;y=-.022+.04*u-.02*math.sin(math.pi*t)
   hit,no,_,_=tree.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)))
   if hit is not None:y=hit.y-.004-.012*u-.002*math.sin(11*t+15*u)
   centres.append((x,y,z))
  centres=np.array(centres);tangent=np.gradient(centres,axis=0);normal=np.tile([0,-1,0],(n,1));axis=np.cross(tangent,normal);t=np.linspace(0,1,n);radii=rng.uniform(.00013,.00021)*(.12+.88*(1-t)**.25)
  tube(vs,fs,uvs,inds,centres,radii,axis,normal,int(rng.integers(0,12)));count+=1
 mesh('R15 lifted forelock %s'%side,vs,fs,uvs,inds)
# Ease the prominent front neck join and define paired neck tendons below the jaw.
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith(('anatomical-head','R9_continuous')):continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;x,y,z=w
  if 1.255<z<1.395 and y<.05:
   f=math.exp(-((z-1.325)/.045)**2);w.y-=.0018*f*math.exp(-((abs(x)-.030)/.013)**2);w.x*=1-.025*f
   v.co=inv@w
 ob.data.update()
(OUT/'final-refinement-report.json').write_text(json.dumps({'removed_panel_scalp':True,'living_iris_scale':1.22,'eye_recess':.004,'skeletal_eye_material_darkened':True,'lifted_forelock_fibres':count,'neck_contour_refined':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stage-final.blend'),compress=True)
