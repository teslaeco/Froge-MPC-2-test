"""E16 targeted seam/neck/nasal reconstruction from user's E15, preserving upper face."""
import bpy,bmesh,math,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');P=ROOT/'correction-e16';sys.path.insert(0,str(P/'runtime'))
from scene_exports import _portable_images,_portable_uvs
report={'base':'uploaded E15; no R15 deformation','changes':[],'likeness_accepted':False}
head=bpy.data.objects['anatomical-head']
# Recover original, higher-resolution artwork already packed in this source.
ref=bpy.data.images.get('R13 latest supplied reference')
if ref and ref.packed_file:(P/'reference-original.png').write_bytes(ref.packed_file.data)
# Match neck's upper envelope to the actual head at the same heights.
tree=BVHTree.FromPolygons([head.matrix_world@v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
chest=bpy.data.objects['R9_continuous_shoulders_neck'];inv=chest.matrix_world.inverted();neck_changes=0
for v in chest.data.vertices:
 w=chest.matrix_world@v.co
 if w.z>1.348 and abs(w.x)<.085:
  q=max(0,min(1,(w.z-1.348)/.047));f=q*q*(3-2*q);center=Vector((0,.075,w.z));direction=w-center
  if direction.length<1e-7:continue
  direction.normalize();hit,normal,_,_=tree.ray_cast(center+direction*.3,-direction,.35)
  if hit is not None:
   target=hit-direction*.0006;v.co=inv@w.lerp(target,f);neck_changes+=1
chest.data.update();report['neck_vertices_aligned']=neck_changes
# Local relief for collarbones and neck tendons, retaining neutral centered posture.
for v in chest.data.vertices:
 x,y,z=v.co
 if y<.055:
  front=max(0,min(1,(.055-y)/.08));collar_z=1.300-.17*abs(x);collar=math.exp(-((z-collar_z)/.008)**2)*math.exp(-((abs(x)-.065)/.075)**2)
  tendon=math.exp(-((abs(x)-(.022+.09*(1.38-z)))/.011)**2)*math.exp(-((z-1.34)/.043)**2)
  v.co.y-=front*(.0018*collar+.0015*tendon)
chest.data.update()
# Preserve E15 outer nasal boundary topology; use homothetic correspondence, never angle-sorted rings.
bm=bmesh.new();bm.from_mesh(head.data);edges=set(e for e in bm.edges if e.is_boundary);target=None
while edges:
 e=edges.pop();group={e};todo=[e]
 while todo:
  e=todo.pop()
  for v in e.verts:
   for n in v.link_edges:
    if n in edges:edges.remove(n);group.add(n);todo.append(n)
 vs={v for e in group for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs)
 if len(vs)>300 and .002<c.x<.018 and 1.49<c.z<1.52 and c.y<-.01:target=(group,vs)
assert target is not None
es,vs=target;assert all(sum(e in es for e in v.link_edges)==2 for v in vs)
start=min(vs,key=lambda v:v.co.z);ordered=[start];prev=None;cur=start
while True:
 ns=[e.other_vert(cur) for e in cur.link_edges if e in es and e.other_vert(cur)!=prev];nxt=ns[0]
 if nxt==start:break
 ordered.append(nxt);prev,cur=cur,nxt
assert len(ordered)==len(vs)
a=np.array([v.co for v in ordered]);smooth=a.copy()
for _ in range(24):smooth=.5*smooth+.25*np.roll(smooth,1,axis=0)+.25*np.roll(smooth,-1,axis=0)
for v,c in zip(ordered,smooth):v.co=c
mi=next(i for i,m in enumerate(head.data.materials) if m and m.name=='R13 observed skeletal face');ci=next(i for i,m in enumerate(head.data.materials) if m and m.name=='Cavity')
uvlayers=list(bm.loops.layers.uv.values());added=[];center=np.array([.0102,-.0244,1.5018]);inner=smooth.copy();inner[:,0]=center[0]+.58*(smooth[:,0]-center[0]);inner[:,2]=center[2]+.63*(smooth[:,2]-center[2]);inner[:,1]=-.003+.08*(smooth[:,1]-center[1])
def uv(q):
 py=(1.8856-(q.z+.032))/.0006;seam=490-(py-240)*28/520;px=seam+q.x/.00064
 return ((px*1.3399541385579454-163.50778090604848)/899,1-(py*1.3399541385579454-140.0901660043437)/2048)
old=ordered
for k in range(1,9):
 t=k/8;t=t*t*(3-2*t);ring=[bm.verts.new(Vector(tuple(a*(1-t)+b*t))) for a,b in zip(smooth,inner)]
 for j in range(len(ring)):
  n=(j+1)%len(ring);f=bm.faces.new((old[j],old[n],ring[n],ring[j]));f.material_index=mi;f.smooth=True;added.append(f)
  for l in f.loops:
   for layer in uvlayers:l[layer].uv=uv(l.vert.co)
 old=ring
for k in range(1,9):
 t=k/8;ring=[]
 for c in inner:
  q=c.copy();q[0]=center[0]+(c[0]-center[0])*(1-.95*t);q[2]=center[2]+(c[2]-center[2])*(1-.95*t);q[1]+=.044*t;ring.append(bm.verts.new(q))
 for j in range(len(ring)):
  n=(j+1)%len(ring);f=bm.faces.new((old[j],old[n],ring[n],ring[j]));f.material_index=ci;f.smooth=True;added.append(f)
 old=ring
f=bm.faces.new(tuple(reversed(old)));f.material_index=ci;added.append(f);bmesh.ops.recalc_face_normals(bm,faces=added)
patch={v for f in added for v in f.verts}
for _ in range(4):patch |= {e.other_vert(v) for v in list(patch) for e in v.link_edges}
for _ in range(65):bmesh.ops.smooth_vert(bm,verts=list(patch),factor=.55,use_axis_x=True,use_axis_y=True,use_axis_z=True)
report['nasal_patch_relaxation_steps']=65
report['nasal_boundary_vertices']=len(ordered);report['nasal_new_faces']=len(added)
bm.to_mesh(head.data);bm.free();head.data.update()
old=bpy.data.objects.get('Nasal_opening')
if old:bpy.data.objects.remove(old,do_unlink=True)
# Refine skeletal mouth corner with a compact-support field; leave living side unchanged.
changed=0
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not (ob.name=='anatomical-head' or ob.name.startswith('Anatomical_') or ob.name=='Recessed oral cavity'):continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;x,y,z=w
  if x>.020 and y<.045 and 1.425<z<1.487:
   f=math.exp(-((z-1.455)/.018)**2)*max(0,min(1,(x-.020)/.040));w.x-=.010*f;w.y+=.002*f;v.co=inv@w;changed+=1
 ob.data.update()
report['skeletal_mouth_vertices_refined']=changed
# Gown neckline: lift central dip, shape underbust/waist, carry seams along with cloth.
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith(('R9_tailored','R9_bodice','R9_neckline','R9_continuous')):continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;x,y,z=w;front=max(0,min(1,(.04-y)/.10))
  lift=.020*math.exp(-(x/.060)**2-((z-1.170)/.045)**2)*front;w.z+=lift
  # V-shaped fitted waist, localized rather than distorting the whole torso.
  w.x*=1-.035*math.exp(-((z-.985)/.055)**2)
  v.co=inv@w
 ob.data.update()
# Fit raised seam geometry to garment surface; eliminate floating thick cords.
gown=bpy.data.objects['R9_tailored_split_gown'];gown_tree=BVHTree.FromPolygons([gown.matrix_world@v.co for v in gown.data.vertices],[p.vertices[:] for p in gown.data.polygons]);snapped=0
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith('R9_bodice_seam'):continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;p,no,_,d=gown_tree.find_nearest(w)
  if p is not None:
   if no.dot(p-Vector((0,.025,p.z)))<0:no=-no
   v.co=inv@(p+no*.0005);snapped+=1
 ob.data.update()
report['bodice_seam_vertices_fitted']=snapped
# Portable PBR texture data: reduce oversized cloth blotches and add subtle woven relief.
# This modifies material data, not reference photos or review renders.
texture_changes=[]
for label in ['R13 ivory linen silk colour','R13 black fine twill colour']:
 im=bpy.data.images.get(label)
 if not im:continue
 n=len(im.pixels)
 if n==0:continue
 raw=np.empty(n,np.float32);im.pixels.foreach_get(raw);a=raw.reshape(im.size[1],im.size[0],4);rgb=a[:,:,:3];mean=np.mean(rgb,axis=(0,1));rgb[:]=mean+(rgb-mean)*.35
 h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];weave=(np.sin(xx*math.tau/5)*np.sin(yy*math.tau/7))*.008
 rgb[:]*=(1+weave[:,:,None]);rgb[:]=np.clip(rgb,0,1)
 out=bpy.data.images.new('E16 '+label,width=w,height=h,alpha=True);out.pixels.foreach_set(a.ravel());out.update();out.pack()
 for m in bpy.data.materials:
  if m.use_nodes:
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image==im:node.image=out
 texture_changes.append(out.name)
report['new_cloth_colour_maps']=texture_changes
for m in bpy.data.materials:
 if m.use_nodes and m.name.startswith('R11 warm skin'):
  bs=m.node_tree.nodes.get('Principled BSDF')
  if bs:bs.inputs['Base Color'].default_value=(.31,.179,.086,1);bs.inputs['Roughness'].default_value=.47;bs.inputs['Subsurface Weight'].default_value=.055
# Original skull dimensions and living-eye objects retained.
report['head_global_scale_unchanged']=True;report['living_eye_geometry_unchanged']=True
tri=0
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report['triangles']=tri
bpy.context.scene['repair_revision']='E16-local-reconstruction'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'FORGE-model-E16.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(P/'FORGE-model-E16.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
portable={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,portable),_portable_images(bpy,P,portable):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(P/'FORGE-model-E16.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report['portable']=portable;(P/'build-report.json').write_text(json.dumps(report,indent=2));print('E16_EXPORTED',tri,texture_changes,flush=True)
