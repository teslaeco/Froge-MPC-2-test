import bpy,sys,json
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15';sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs
for ob in list(bpy.context.scene.objects):
 if ob.name.startswith('R15 lifted forelock'):bpy.data.objects.remove(ob,do_unlink=True)
refinement=json.loads((OUT/'final-refinement-report.json').read_text());refinement['lifted_forelock_fibres']=0;refinement['forelock_trials_rejected']=True;(OUT/'final-refinement-report.json').write_text(json.dumps(refinement,indent=2))
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
report.update(triangles=tri,long_fibres=4992,root_fibres=1200,inner_hair_volume_radius_factor=.43,wave_guides_retained=True,anatomy=json.loads((OUT/'anatomy-report.json').read_text()),likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R15_SAVED_FINAL',tri,flush=True)
