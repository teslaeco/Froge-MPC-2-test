"""Final material balance and strand fullness correction after actual FBX review."""
import bpy,json,sys
import numpy as np
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r11'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
for name,old,new,contrast in [('R11 chestnut fine hair BaseColor 2K',(.053,.025,.010),(.10,.045,.018),1),('R11 warm skin BaseColor 2K',(.54,.35,.225),(.54,.39,.28),1),('R11 ivory woven cloth BaseColor 2K',(.52,.47,.36),(.62,.57,.46),.60)]:
 im=bpy.data.images[name];a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a);a=a.reshape(-1,4)
 a[:,:3]=np.clip((1+(a[:,:3]/np.array(old)-1)*contrast)*np.array(new),0,1);im.pixels.foreach_set(a.ravel());im.update();im.pack()
# Retain three distinct fine strands, but restore fuller aggregate hair coverage.
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name.startswith('R11_Reference_'):
  a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);r=a.reshape(-1,8,3);c=r.mean(axis=1,keepdims=True);r=c+(r-c)*(.48/.35);o.data.vertices.foreach_set('co',r.ravel());o.data.update();o['relative_cross_section_radius']=.48
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r11-2000k.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r11-2000k.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r11-2000k.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
assert tri==2000000,tri
report.update(triangles=tri,target_triangles=2000000,hair_preserved=False,wave_guides_retained=True,original_locks=104,new_thin_locks=312,relative_strand_radius=.48,pbr_map_resolution=2048,likeness_accepted=False,print_ready=False,texture_details='authored procedural PBR; original registered photo diffuse retained on observed face')
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R11_FINAL_SAVED',tri,flush=True)
