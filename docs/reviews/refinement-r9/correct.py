"""Resolve observed side-view chest/cloth intersection and register crown hair flow."""
import bpy,bmesh,math,json,sys
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r9'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
chest=bpy.data.objects['R9_continuous_shoulders_neck']
bm=bmesh.new();bm.from_mesh(chest.data);remove=[]
for f in bm.faces:
 c=f.calc_center_median();t=math.atan2(c.x/.213,-(c.y-.025)/.12);front=max(0,math.cos(t));top=1.272-.110*front**5+.014*math.exp(-((abs(math.sin(t))-.62)/.23)**2)*front
 if c.z<top-.009:remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(chest.data);bm.free();chest.data.update()
# Sample source hair pixels as a front-scalp material; this is not a landmark registration; keep unseen back material.
cap=bpy.data.objects['Reference_fitted_scalp'];old=cap.data.materials[0]
m=bpy.data.materials.new('R9 observed crown flow');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.68;bs.inputs['Specular IOR Level'].default_value=.18
tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images['Observed_original_face'];m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);cap.data.materials.append(m)
uv=cap.data.uv_layers[0]
for p in cap.data.polygons:
 if p.center.y<.055:
  p.material_index=len(cap.data.materials)-1
  for li in p.loop_indices:
   v=cap.data.vertices[cap.data.loops[li].vertex_index].co
   uv.data[li].uv=((450-abs(v.x)*1700)/899,1-(240+(1.735-v.z)*650)/2048)
# The initial fine-root experiment did not visibly solve the cap. Remove it from delivery.
for o in list(bpy.context.scene.objects):
 if o.name.startswith('R9_swept_root_'):bpy.data.objects.remove(o,do_unlink=True)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r9.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r9.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r9.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report.update(triangles=tri,hair_preserved=True,long_locks_preserved=True,cap_modified=True,likeness_accepted=False,print_ready=False,removed_hidden_chest_faces=len(remove),crown='source hair pixels used as cap texture; unseen back unchanged; not exact reconstruction',remaining=['likeness is approximate','separate neck/head join','unseen anatomy inferred','not watertight'])
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R9_CORRECTED',tri,len(remove),flush=True)
