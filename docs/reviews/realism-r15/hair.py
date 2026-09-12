"""R15 thousands of tapered mesh fibres over reduced dark inner hair mass."""
import bpy,bmesh,math,json,sys,gc
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15';sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs
rng=np.random.default_rng(915)
def material(name,c,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.28;return m
core=material('R15 dark hair interior',(.0045,.002,.0008),.72)
mats=[material('R15 chestnut fibre %02d'%i,tuple(np.array([.022,.009,.0032])*(.65+i*.08)),.37+(i%3)*.035) for i in range(12)]
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
locks=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('R11_Reference_')];filaments=0
for k,ob in enumerate(locks):
 raw=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',raw);a=raw.reshape(-1,8,3).astype(float);c=a.mean(1);axis=a[:,0]-c;other=a[:,2]-c;rad=np.linalg.norm(axis,axis=1);t=np.linspace(0,1,len(c));vs=[];fs=[];uvs=[];inds=[]
 for j in range(16):
  phase=math.tau*(j/16)+rng.uniform(-.12,.12);rho=rng.uniform(.65,1.03);wiggle=.10*np.sin(t*math.tau*rng.uniform(1.3,2.8)+phase)
  centres=c+rho*(np.cos(phase+wiggle)[:,None]*axis+np.sin(phase+wiggle)[:,None]*other)
  radii=np.minimum(.00038,rad*rng.uniform(.065,.095))*(.10+.90*(1-t)**.30);tube(vs,fs,uvs,inds,centres,radii,axis,other,int(rng.integers(0,12)));filaments+=1
 mesh('R15 fine wave %03d'%k,vs,fs,uvs,inds)
 # Non-glossy inner mass supplies opacity; fine outer fibres define visible highlights.
 inside=c[:,None,:]+.43*(a-c[:,None,:]);ob.data.vertices.foreach_set('co',inside.astype(np.float32).ravel());ob.data.materials.clear();ob.data.materials.append(core)
 for p in ob.data.polygons:p.material_index=0
 if k%60==0:print('FINE_HAIR_GUIDES',k,flush=True)
for ob in list(bpy.context.scene.objects):
 if ob.name.startswith('R12_root_'):bpy.data.objects.remove(ob,do_unlink=True)
cap=bpy.data.objects.get('R12_asymmetric_scalp')
if cap:
 cap.name='R15 scalp undercoat';cap.data.materials.clear();cap.data.materials.append(core)
 for p in cap.data.polygons:p.material_index=0
head=bpy.data.objects['anatomical-head'];tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons]);root_count=0
for side in (-1,1):
 for batch in range(3):
  vs=[];fs=[];uvs=[];inds=[]
  for local in range(200):
   j=batch*200+local;u=(j+.5)/600;start_y=-.016+.178*u;start_x=.009+side*rng.uniform(.00065,.0017)
   start,_,_,_=tree.ray_cast(Vector((start_x,start_y,1.9)),Vector((0,0,-1)))
   if start is None:continue
   endz=1.505+.066*u;end_y=.009+.13*u;centres=[];normals=[];n=73
   for i in range(n):
    t=i/(n-1);x=.009+side*(.001+.119*math.sin(t*math.pi/2));y=start_y+(end_y-start_y)*t**1.3;z=start.z-(start.z-endz)*t**1.45+.009*math.sin(math.pi*t)
    p,no,_,_=tree.find_nearest(Vector((x,y,z)));outward=p-Vector((.009,.07,1.535))
    if no.dot(outward)<0:no=-no
    p+=no*(.0007+.00015*(j%5));centres.append(np.array(p));normals.append(np.array(no))
   centres=np.array(centres);normals=np.array(normals);tangents=np.gradient(centres,axis=0);axis=np.cross(tangents,normals);other=normals;t=np.linspace(0,1,n);radii=rng.uniform(.00014,.00023)*(.30+.70*np.sin(math.pi*np.minimum(.98,t+.015))**.35)
   tube(vs,fs,uvs,inds,centres,radii,axis,other,int(rng.integers(0,12)));root_count+=1
  mesh('R15 swept roots %s %s'%(side,batch),vs,fs,uvs,inds)
print('HAIR_FIBRES_READY',filaments,root_count,flush=True)
# Prune disconnected shader nodes and orphan data from earlier versions in this copy.
used={m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m}
for m in used:
 if not m.use_nodes:continue
 nt=m.node_tree;keep=set()
 def walk(n):
  if n in keep:return
  keep.add(n)
  for inp in n.inputs:
   for link in inp.links:walk(link.from_node)
 for n in nt.nodes:
  if n.type=='OUTPUT_MATERIAL' and n.is_active_output:walk(n)
 for n in list(nt.nodes):
  if n not in keep:nt.nodes.remove(n)
bpy.data.orphans_purge(do_recursive=True)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
bpy.context.scene['repair_revision']='r15-realism';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r15.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r15.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r15.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=tri,long_fibres=filaments,root_fibres=root_count,inner_hair_volume_radius_factor=.43,wave_guides_retained=True,anatomy=json.loads((OUT/'anatomy-report.json').read_text()),likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R15_SAVED',tri,filaments,root_count,flush=True)
