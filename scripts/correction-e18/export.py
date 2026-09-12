import bpy,json,sys
from pathlib import Path
P=Path('/workspace/scratch/584c9d97a5a1/correction-e18');sys.path.insert(0,str(P.parent/'correction-e16/runtime'))
from scene_exports import _portable_images,_portable_uvs
report=json.loads((P/'build-report.json').read_text())
bpy.ops.export_scene.gltf(filepath=str(P/'FORGE-model-E18.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
portable={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,portable),_portable_images(bpy,P,portable):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(P/'FORGE-model-E18.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report['portable']=portable;(P/'build-report.json').write_text(json.dumps(report,indent=2));print('EXPORTED',report['triangles'],flush=True)
