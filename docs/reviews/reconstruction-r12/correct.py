"""Replace failed nasal warp with a local annular patch; coherent front UVs; revert neck regression."""
import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'reconstruction-r12'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
head=bpy.data.objects['anatomical-head'];chest=bpy.data.objects['R9_continuous_shoulders_neck']
with bpy.data.libraries.load(str(ROOT/'refinement-r11/FORGE-model-r11-2000k.blend'),link=False) as (src,dst):dst.objects=['anatomical-head','R9_continuous_shoulders_neck']
for old,current in zip(dst.objects,[head,chest]):current.data=old.data.copy();bpy.data.objects.remove(old,do_unlink=True)
# Normalize duplicate imported material names, preserving the existing appearance.
for i,m in enumerate(head.data.materials):
 if m and m.name.startswith('Reference_observed_face'):head.data.materials[i]=bpy.data.materials['Reference_observed_face']
observed=bpy.data.materials['Reference_observed_face'];tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
# Remove the defective local nose patch. The replacement overlaps its edge by 1.5mm.
bm=bmesh.new();bm.from_mesh(head.data)
remove=[f for f in bm.faces if -.005<f.calc_center_median().x<.029 and 1.498<f.calc_center_median().z<1.566 and f.calc_center_median().y<.050]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(head.data);bm.free();head.data.update()
old=bpy.data.objects.get('Nasal_opening')
if old:bpy.data.objects.remove(old,do_unlink=True)
vs=[];fs=[];uvs=[];steps=128;rings=18;cx=.008;cz=1.532
for i in range(rings+1):
 t=i/rings
 for j in range(steps):
  a=math.tau*j/steps;dx=math.cos(a);dz=math.sin(a)
  rx=.0065*(.8+.2*(1-dz)*.5);inner=Vector((cx+rx*dx,0,cz+.0175*dz))
  scales=[]
  if dx>1e-8:scales.append((.0305-cx)/dx)
  elif dx< -1e-8:scales.append((-.0065-cx)/dx)
  if dz>1e-8:scales.append((1.5675-cz)/dz)
  elif dz< -1e-8:scales.append((1.4965-cz)/dz)
  r=min(scales);outer=Vector((cx+r*dx,0,cz+r*dz))
  hit,n,_,_=tree.ray_cast(Vector((outer.x,-.7,outer.z)),Vector((0,1,0)))
  oy=max(-.052,min(.006,hit.y if hit is not None else -.017))-.0008
  y=.008*(1-t)+oy*t
  p=inner*(1-t)+outer*t;p.y=y;vs.append(tuple(p))
  py=(1.8856-p.z)/.0006;seam=490-(py-240)*28/520;uvs.append(((seam+p.x/.00064)/899,1-py/2048))
  if i:fs.append(((i-1)*steps+j,(i-1)*steps+(j+1)%steps,i*steps+(j+1)%steps,i*steps+j))
me=bpy.data.meshes.new('R12 nasal annular topology');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('R12_reconstructed_nasal_rim',me);bpy.context.collection.objects.link(o);me.materials.append(observed);uv=me.uv_layers.new(name='UVMap')
for p in me.polygons:
 p.use_smooth=True
 for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
# A recessed cavity bowl, not a flat black decal.
vs=[];fs=[];uvs=[];nr=12
for i in range(nr+1):
 t=i/nr
 for j in range(steps):
  a=math.tau*j/steps;rx=.0065*(.8+.2*(1-math.sin(a))*.5);vs.append((cx+rx*math.cos(a)*(1-t*.96),.008+.032*math.sin(t*math.pi/2),cz+.0175*math.sin(a)*(1-t*.96)));uvs.append((j/steps,t))
  if i:fs.append(((i-1)*steps+j,(i-1)*steps+(j+1)%steps,i*steps+(j+1)%steps,i*steps+j))
me=bpy.data.meshes.new('R12 nasal cavity depth');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('R12_nasal_cavity',me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials['Cavity']);uv=me.uv_layers.new(name='UVMap')
for p in me.polygons:
 p.use_smooth=True
 for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
# Coherent projection over the observed front replaces the mixed old atlas/photo band.
mi=list(head.data.materials).index(observed);uv=head.data.uv_layers[0]
for p in head.data.polygons:
 if p.center.y<.04 and p.center.z>1.43 and p.normal.y<-.10:
  p.material_index=mi
  for li in p.loop_indices:
   q=head.data.vertices[head.data.loops[li].vertex_index].co;py=(1.8856-q.z)/.0006;seam=490-(py-240)*28/520
   uv.data[li].uv=((seam+q.x/.00064)/899,1-py/2048)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r12.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r12.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r12.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();tri+=len(m.loop_triangles);ev.to_mesh_clear()
report.update(triangles=tri,wave_guides_retained=True,local_nasal_patch_removed_faces=len(remove),nasal_new_topology='128 angular segments, 18 outer rings, 12 cavity rings',global_flat_subdivision=False,neck_attempt_reverted=True,likeness_accepted=False,print_ready=False,remaining=['neck/head continuity','likeness and smile','garment anatomy','hairline realism','not certified watertight'])
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R12_CORRECTED',tri,flush=True)
