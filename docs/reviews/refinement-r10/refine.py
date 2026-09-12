"""R10: shaped shoulders/bust, sleeve anatomy, nose/smile and swept hairline; 1.5M budget."""
import bpy,bmesh,math,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r10'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors

def mesh(name,vs,fs,uvs,mats):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for m in mats:me.materials.append(m)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
 return o

def gaussian(v,c,w):return math.exp(-((v-c)/w)**2)
def long_hash():
 h=hashlib.sha256()
 for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  if o.type=='MESH' and o.name.startswith(('Reference_front_lock','Reference_back_lock')):
   h.update(o.name.encode());a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);h.update(a.tobytes())
 return h.hexdigest()
hair_before=long_hash()
# A paired, smoothly blended bust shape replaces the barrel-like chest profile.
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 if o.name.startswith(('R9_tailored','R9_bodice','R9_neckline','R9_continuous')):
  for v in o.data.vertices:
   x,y,z=v.co
   front=max(0,min(1,(.035-y)/.08))
   bust=gaussian(abs(x),.087,.055)*gaussian(z,1.197,.071)*front
   v.co.y-=.040*bust
   # lift lateral neckline over the breast while retaining central plunge
   v.co.z+=.011*bust
   # soften unnaturally angular trapezius and upper chest ring transitions
   if o.name.startswith('R9_continuous'):
    v.co.z-=.008*gaussian(abs(x),.15,.075)*gaussian(z,1.315,.035)
  o.data.update()
# Relax ring transitions without flattening the designed body silhouette.
chest=bpy.data.objects['R9_continuous_shoulders_neck']
bm=bmesh.new();bm.from_mesh(chest.data);vs=[v for v in bm.verts if 1.27<v.co.z<1.395 and not v.is_boundary]
for _ in range(9):bmesh.ops.smooth_vert(bm,verts=vs,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(chest.data);bm.free()
# Anatomical upper arms create real rounded shoulders above off-shoulder sleeve rims.
for side,material in ((-1,chest.data.materials[0]),(1,chest.data.materials[1])):
 vs=[];fs=[];uvs=[];nr=70;nc=80
 for i in range(nr+1):
  s=i/nr;z=1.333-.365*s;cx=side*(.193+.071*s);cy=.025
  rad=np.interp(s,[0,.10,.25,.60,1],[.009,.048,.058,.046,.036]);depth=rad*1.18
  for j in range(nc):
   t=math.tau*j/nc;vs.append((cx+rad*math.sin(t),cy-depth*math.cos(t),z));uvs.append((j/nc,s))
   if i:fs.append(((i-1)*nc+j,(i-1)*nc+(j+1)%nc,i*nc+(j+1)%nc,i*nc+j))
 arm=mesh('R10_upper_arm_%s'%side,vs,fs,uvs,[material])
 # leave the cap buried within the shoulder; hide the lower arm inside its sleeve
 for name in ('R9_gathered_sleeve_%s'%side,'R9_sleeve_edge_%s'%side):
  o=bpy.data.objects[name]
  for v in o.data.vertices:
   x,y,z=v.co;s=max(0,min(1,(z-.69)/.57))
   v.co.z-=.023*s**6
   # gentle elbow bend; hands and cuff remain aligned
   bend=.010*math.sin(math.pi*s)**2
   v.co.y-=bend
   # break perfectly vertical corrugation with small localized fold depth
   v.co.y+=.0023*math.sin(z*97+side*x*23)*gaussian(z,1.015,.048)
  o.data.update()
# Smooth and reshape the nose; preserve UV registration of the living face.
head=bpy.data.objects['anatomical-head']
for v in head.data.vertices:
 x,y,z=v.co
 if x<.006 and y<.035:
  nose=gaussian(x,-.013,.017)*gaussian(z,1.534,.021)*max(0,min(1,(.035-y)/.035))
  v.co.y-=.004*nose
  v.co.x+=.0015*nose
  # lift the lip corner subtly rather than exposing a large black mouth opening
  smile=gaussian(x,-.039,.014)*gaussian(z,1.489,.010)
  v.co.z+=.0022*smile
# Shrink angular nasal boundary and smooth the surrounding nose opening.
bm=bmesh.new();bm.from_mesh(head.data)
bound=[v for v in bm.verts if v.is_boundary and -.005<v.co.x<.026 and 1.502<v.co.z<1.559 and v.co.y<.055]
for v in bound:
 v.co.x=.007+(v.co.x-.007)*.88;v.co.z=1.530+(v.co.z-1.530)*.90
for _ in range(12):bmesh.ops.smooth_vert(bm,verts=bound,factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(head.data);bm.free();head.data.update()
# Enamel crown variation and a slightly deeper dental arch.
for o in bpy.context.scene.objects:
 if o.name.startswith('Anatomical_upper_tooth_'):
  side,j=map(int,o.name.rsplit('_',2)[1:]);o.location.y+=.0013;o.location.z+=(.00045 if j==0 else -.0003 if j==1 else .0002)
  o.scale.x*=1.035 if j<2 else .96;o.rotation_euler.y+=side*(.025 if j==1 else -.02)
 if o.name.startswith('Anatomical_lower_tooth_'):o.location.y+=.001
# Replace the photographic cap patch with actual fine swept surface locks.
cap=bpy.data.objects['Reference_fitted_scalp'];hairmat=bpy.data.objects['Reference_front_lock_-1_00'].data.materials[0]
cap.data.materials.clear();cap.data.materials.append(hairmat)
for p in cap.data.polygons:p.material_index=0
capuv=cap.data.uv_layers[0]
for p in cap.data.polygons:
 for li in p.loop_indices:
  v=cap.data.vertices[cap.data.loops[li].vertex_index].co;capuv.data[li].uv=(abs(v.co.x) if hasattr(v,'co') else abs(v.x),v.z)
tree=BVHTree.FromPolygons([v.co for v in cap.data.vertices],[p.vertices[:] for p in cap.data.polygons])
for side in (-1,1):
 for j in range(38):
  centers=[];vs=[];fs=[];uvs=[];steps=62;sides=10
  for i in range(steps+1):
   t=i/steps;x=side*(.0012+.118*math.sin(t*math.pi/2));z=1.734-.00185*j-.049*t-.031*t*t
   hit,n,_,_=tree.ray_cast(Vector((x,-.8,z)),Vector((0,1,0)))
   if hit is None:hit,n,_,_=tree.find_nearest(Vector((x,-.04,z)))
   # frontward offset is deliberate: this cap's winding is not used for clearance
   centers.append(hit+Vector((0,-.0032,0)))
  for i,c in enumerate(centers):
   tangent=centers[min(i+1,steps)]-centers[max(0,i-1)];tangent.y=0
   if tangent.length<1e-7:tangent=Vector((side,0,-1))
   tangent.normalize();axis=Vector((-tangent.z,0,tangent.x));t=i/steps
   taper=.35+.65*math.sin(math.pi*t)**.35
   for k in range(sides):
    a=math.tau*k/sides;vs.append(tuple(c+axis*(.0023*taper*math.cos(a))+Vector((0,.0013*taper*math.sin(a),0))));uvs.append((k/sides,t))
    if i:fs.append(((i-1)*sides+k,(i-1)*sides+(k+1)%sides,i*sides+(k+1)%sides,i*sides+k))
  fs.extend([tuple(reversed(range(sides))),tuple(steps*sides+k for k in range(sides))])
  mesh('R10_swept_hairline_%s_%02d'%(side,j),vs,fs,uvs,[hairmat])
assert hair_before==long_hash()
# Densify the face and tune its triangle budget after all genuine shape changes.
def count(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();n=len(me.loop_triangles);ev.to_mesh_clear();return n
others=sum(count(o) for o in bpy.context.scene.objects if o.type=='MESH' and o!=head)
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
sub=head.modifiers.new('Fine facial density','SUBSURF');sub.levels=1;sub.render_levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
dense=count(head);target=1500000-others
mod=head.modifiers.new('Exact 1.5M scene budget','DECIMATE');mod.ratio=target/dense;mod.use_collapse_triangulate=True
# Adjust ratio against evaluated counts before applying, avoiding repeated destructive decimation.
for _ in range(8):
 actual=count(head)
 if actual==target:break
 mod.ratio+=(target-actual)/dense
bpy.ops.object.modifier_apply(modifier=mod.name)
triangles=others+count(head)
assert abs(triangles-1500000)<=2,(triangles,target)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.context.scene['repair_revision']='r10-1.5M';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r10-1500k.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r10-1500k.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r10-1500k.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=triangles,target_triangles=1500000,hair_preserved=True,long_lock_hash=hair_before,new_hairline_locks=76,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R10_SAVED',triangles,flush=True)
