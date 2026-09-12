import bpy,json,hashlib
from pathlib import Path
P=Path('/workspace/scratch/584c9d97a5a1/correction-e17');asset=P/'FORGE-model-E17-web.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(asset))
n=0;meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:o.data.calc_loop_triangles();n+=len(o.data.loop_triangles)
missing=[i.name for i in bpy.data.images if i.users and min(i.size)==0]
r={'source_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'bytes':asset.stat().st_size,'triangles':n,'mesh_objects':len(meshes),'missing_textures':missing,'actual_glb_reimport':True,'compression':'Draco6','colour_maps_max_px':1024,'normal_roughness_maps_max_px':512,'manual_decimation':False}
r['master_triangles']=json.loads((P/'build-report.json').read_text())['triangles'];r['triangle_delta_glb_vs_fbx']=n-r['master_triangles'];print(r,flush=True);assert not missing;assert r['bytes']<24*1024*1024
(P/'web-verification.json').write_text(json.dumps(r,indent=2));print(r,flush=True)
