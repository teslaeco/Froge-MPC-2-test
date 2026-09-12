"""Integrate nasal annulus into actual boundary vertices; no overlapping patch plate."""
import bpy,bmesh,math,json,sys
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'reconstruction-r12'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
head=bpy.data.objects['anatomical-head']
with bpy.data.libraries.load(str(ROOT/'refinement-r11/FORGE-model-r11-2000k.blend'),link=False) as (src,dst):dst.objects=['anatomical-head']
ref=dst.objects[0];old=head.data;head.data=ref.data;bpy.data.objects.remove(ref,do_unlink=True)
if old.users==0:bpy.data.meshes.remove(old)
for name in ('R12_reconstructed_nasal_rim','R12_nasal_cavity'):
 ob=bpy.data.objects.get(name)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
observed=bpy.data.materials['Reference_observed_face'];cavity=bpy.data.materials['Cavity']
for i,m in enumerate(head.data.materials):
 if m and m.name.startswith('Reference_observed_face'):head.data.materials[i]=observed
if cavity not in list(head.data.materials):head.data.materials.append(cavity)
mi=list(head.data.materials).index(observed);ci=list(head.data.materials).index(cavity)
bm=bmesh.new();bm.from_mesh(head.data)
remove=[]
for f in bm.faces:
 c=f.calc_center_median()
 if -.005<c.x<.029 and 1.498<c.z<1.566 and c.y<.050:remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bound=[v for v in bm.verts if v.is_boundary and -.009<v.co.x<.033 and 1.494<v.co.z<1.570 and v.co.y<.055]
assert len(bound)>30,len(bound)
# The cut contour is star-shaped in frontal projection; order its real boundary vertices.
for v in bound:v.tag=True
bound.sort(key=lambda v:math.atan2((v.co.z-1.532)/.034,(v.co.x-.009)/.018))
angles=[math.atan2((v.co.z-1.532)/.034,(v.co.x-.009)/.018) for v in bound]
original=[v.co.copy() for v in bound];previous=bound;added=[];nr=16
for i in range(1,nr+1):
 t=i/nr;ring=[]
 for p,a in zip(original,angles):
  from mathutils import Vector
  inner=Vector((.008+.0065*(.8+.2*(1-math.sin(a))*.5)*math.cos(a),.010,1.532+.0175*math.sin(a)))
  co=p.lerp(inner,t);co.y=p.y+(inner.y-p.y)*(t*t*(3-2*t));ring.append(bm.verts.new(co))
 for j in range(len(ring)):
  k=(j+1)%len(ring);f=bm.faces.new((previous[j],previous[k],ring[k],ring[j]));f.material_index=mi;f.smooth=True;added.append(f)
 previous=ring
for i in range(1,9):
 t=i/8;ring=[]
 for a in angles:ring.append(bm.verts.new((.008+.0065*(.8+.2*(1-math.sin(a))*.5)*math.cos(a)*(1-.97*t),.010+.030*t,1.532+.0175*math.sin(a)*(1-.97*t))))
 for j in range(len(ring)):
  k=(j+1)%len(ring);f=bm.faces.new((previous[j],previous[k],ring[k],ring[j]));f.material_index=ci;f.smooth=True;added.append(f)
 previous=ring
added_set=set(added)
uv=bm.loops.layers.uv.verify()
for f in bm.faces:
 c=f.calc_center_median()
 if c.y<.04 and c.z>1.43 and (f.normal.y<-.10 or f in added_set):
  if f.material_index!=ci:f.material_index=mi
  for loop in f.loops:
   q=loop.vert.co;py=(1.8856-q.z)/.0006;seam=490-(py-240)*28/520;loop[uv].uv=((seam+q.x/.00064)/899,1-py/2048)
# New annular face direction matches front-facing head topology.
bmesh.ops.recalc_face_normals(bm,faces=added)
bm.to_mesh(head.data);bm.free();head.data.update()
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
report.update(triangles=tri,wave_guides_retained=True,nasal_boundary_vertices=len(bound),nasal_local_new_faces=len(added),nose_patch_uses_actual_head_boundary=True,global_flat_subdivision=False,neck_attempt_reverted=True,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R12_STITCHED',tri,len(bound),flush=True)
