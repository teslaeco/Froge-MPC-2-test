"""R12 targeted shape reconstruction. No global density subdivision."""
import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'reconstruction-r12'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
head=bpy.data.objects['anatomical-head'];before=[tuple(v.co) for v in head.data.vertices]
bm=bmesh.new();bm.from_mesh(head.data)
# Reconstruct the nasal aperture boundary as a smaller, smooth pear-shaped contour.
nasal=[v for v in bm.verts if v.is_boundary and -.006<v.co.x<.030 and 1.50<v.co.z<1.562 and v.co.y<.060]
nose_changes=[]
for v in nasal:
 p=v.co.copy();angle=math.atan2((p.z-1.532)/.026,(p.x-.008)/.015)
 radius=.0070*(.78+.22*(1-math.sin(angle))*.5)
 v.co.x=.0075+radius*math.cos(angle);v.co.z=1.533+.019*math.sin(angle)
 nose_changes.append((p.copy(),v.co.copy()))
# Relax adjacent vertices so the new contour is not a folded rim.
near=[v for v in bm.verts if not v.is_boundary and -.009<v.co.x<.032 and 1.495<v.co.z<1.568 and v.co.y<.05]
for _ in range(7):bmesh.ops.smooth_vert(bm,verts=near,factor=.20,use_axis_x=True,use_axis_y=True,use_axis_z=True)
# Remove obsolete head neck stub that overlapped the independently built chest.
neck_faces=[f for f in bm.faces if all(v.co.z<1.424 for v in f.verts)]
bmesh.ops.delete(bm,geom=neck_faces,context='FACES');bm.to_mesh(head.data);bm.free();head.data.update()
for name in ('Half_mandible','Sculpted_orbital_margin'):
 ob=bpy.data.objects.get(name)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
# Existing head provides the jaw surface. Removing the loose overlay removes the crescent seam.
tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
chest=bpy.data.objects['R9_continuous_shoulders_neck']
for v in chest.data.vertices:
 if v.co.z>1.399:
  f=min(1,max(0,(v.co.z-1.399)/.042));f=f*f*(3-2*f)
  hit,n,_,_=tree.find_nearest(Vector((v.co.x,v.co.y,1.439)))
  if hit is not None:v.co=v.co*(1-f)+hit*f
chest.data.update()
# Natural upper incisors/canine lengths and a less exposed lower arch.
for ob in bpy.context.scene.objects:
 if ob.name.startswith('Anatomical_upper_tooth_'):
  side,j=map(int,ob.name.rsplit('_',2)[1:]);ob.scale.z*=1.30 if j==0 else 1.17 if j==1 else 1.32 if j==2 else .93
  ob.scale.x*=1.05 if j<2 else .90;ob.location.y+=.0025;ob.location.z-=.001
  for mod in ob.modifiers:
   if mod.type=='BEVEL':mod.width*=1.45;mod.segments=5
 if ob.name.startswith('Anatomical_lower_tooth_'):ob.location.y+=.003;ob.scale.z*=.82
# Dispose of the visibly artificial triangular cap and transverse comb rails.
for ob in list(bpy.context.scene.objects):
 if ob.name=='Reference_fitted_scalp' or ob.name.startswith('R10_swept_hairline_'):bpy.data.objects.remove(ob,do_unlink=True)
hairmat=bpy.data.materials['R11 chestnut fine hair']
# Asymmetric frontal hairline fitted from source image landmarks in scene coordinates.
def hairline(x):
 if x<0:return float(np.interp(-x,[0,.045,.088,.112],[1.690,1.679,1.626,1.575]))
 return float(np.interp(x,[0,.050,.090,.115],[1.690,1.695,1.655,1.61]))
# Selected scalp surface follows actual head, with density reduced on covered rear areas.
selected=[p for p in head.data.polygons if p.center.z>(hairline(p.center.x) if p.center.y<.065 else 1.595)]
used=sorted({i for p in selected for i in p.vertices});mapping={i:j for j,i in enumerate(used)}
verts=[tuple(head.data.vertices[i].co+head.data.vertices[i].normal*.0012) for i in used]
faces=[tuple(mapping[i] for i in p.vertices) for p in selected]
me=bpy.data.meshes.new('R12 fitted asymmetric scalp');me.from_pydata(verts,[],faces);me.update();cap=bpy.data.objects.new('R12_asymmetric_scalp',me);bpy.context.collection.objects.link(cap);me.materials.append(hairmat)
uv=me.uv_layers.new(name='HairFlow')
for p in me.polygons:
 p.use_smooth=True
 for li in p.loop_indices:
  q=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(abs(q.x)*8,(q.z-1.55)*6)
bpy.ops.object.select_all(action='DESELECT');cap.select_set(True);bpy.context.view_layer.objects.active=cap
mod=cap.modifiers.new('Scalp support density','DECIMATE');mod.ratio=.055;bpy.ops.object.modifier_apply(modifier=mod.name)
# Reproject the newly exposed upper forehead to the same source photograph.
observed=bpy.data.materials['Reference_observed_face'];mi=list(head.data.materials).index(observed);uv=head.data.uv_layers[0]
for p in head.data.polygons:
 c=p.center
 if c.y<.04 and c.z>1.637 and c.z<hairline(c.x)+.002 and p.normal.y<-.15:
  p.material_index=mi
  for li in p.loop_indices:
   q=head.data.vertices[head.data.loops[li].vertex_index].co
   py=(1.8856-q.z)/.0006;seam=490-(py-240)*28/520
   target=Vector(((seam+q.x/.00064)/899,1-py/2048));weight=min(1,max(0,(q.z-1.637)/.032));uv.data[li].uv=uv.data[li].uv.lerp(target,weight)
# Sweep roots from the central part towards the asymmetric temple contour.
# Surface is ray sampled in front view; curve direction replaces old horizontal rails.
for side in (-1,1):
 for j in range(26):
  vs=[];fs=[];uvs=[];steps=64;nr=8
  for i in range(steps+1):
   t=i/steps;x=side*(.0015+.112*t)
   low=hairline(x);z=low+(.034*(1-j/28))*(1-.15*t)
   hit,n,_,_=tree.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)))
   if hit is None:hit,n,_,_=tree.find_nearest(Vector((x,-.035,z)))
   c=hit+Vector((0,-.0022,0));width=.0014*(.35+.65*math.sin(math.pi*t)**.5)
   for k in range(nr):
    a=math.tau*k/nr;vs.append(tuple(c+Vector((0,width*.65*math.sin(a),width*math.cos(a)))));uvs.append((k/nr,t))
    if i:fs.append(((i-1)*nr+k,(i-1)*nr+(k+1)%nr,i*nr+(k+1)%nr,i*nr+k))
  me=bpy.data.meshes.new('R12 swept roots');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('R12_root_%s_%02d'%(side,j),me);bpy.context.collection.objects.link(ob);me.materials.append(hairmat);layer=me.uv_layers.new(name='HairFlow')
  for p in me.polygons:
   p.use_smooth=True
   for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
# Genuine geometric additions at neckline: strengthen corset cup curvature locally.
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob.name.startswith(('R9_tailored','R9_bodice','R9_neckline')):
  for v in ob.data.vertices:
   x,y,z=v.co;front=max(0,min(1,(.02-y)/.08));cup=math.exp(-((abs(x)-.085)/.049)**2-((z-1.188)/.060)**2)*front
   v.co.y-=.009*cup
  ob.data.update()
# Count the resulting scene honestly; do not fill a global triangle target with flat splits.
triangles=0
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();triangles+=len(m.loop_triangles);ev.to_mesh_clear()
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.context.scene['repair_revision']='r12-targeted-reconstruction';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r12.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r12.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r12.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=triangles,wave_guides_retained=True,nasal_boundary_vertices_rebuilt=len(nasal),head_neck_faces_removed=len(neck_faces),removed_overlay_objects=['Half_mandible','Sculpted_orbital_margin'],old_scalp_and_76_rails_removed=True,new_local_roots=52,global_density_subdivision=False,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R12_SAVED',triangles,flush=True)
