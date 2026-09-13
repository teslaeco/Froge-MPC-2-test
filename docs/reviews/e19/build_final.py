"""Compose reviewed E19 corrections on an untouched E18R source and export real assets."""
from pathlib import Path
import bpy, importlib.util, json, hashlib, time

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'final'; OUT.mkdir(exist_ok=True)
SOURCE=ROOT.parent/'resume-model/FORGE-E18R-recovered-checkpoint.blend'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run_module(folder,name):
    path=ROOT/folder/name
    spec=importlib.util.spec_from_file_location('e19_'+folder,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=mod.apply()
    return {'script':str(path.relative_to(ROOT)), 'sha256':sha(path),'result':result}

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
report={'source':SOURCE.name,'source_sha256':sha(SOURCE),'changes':{},'versions':{},'blender':bpy.app.version_string}
for folder,name in [('dental','apply_dental.py'),('body','apply_body.py'),('hair','apply_hair.py')]:
    print('E19_APPLY',folder,flush=True)
    report['changes'][folder]=run_module(folder,name)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
report['triangles']=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
report['mesh_objects']=len(meshes)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.
bpy.ops.file.pack_all()
master=OUT/'FORGE-E19-8K.glb'
bpy.ops.export_scene.gltf(filepath=str(master),export_format='GLB',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_apply=True)
report['versions']['master']={'path':master.name,'sha256':sha(master),'bytes':master.stat().st_size,'body_texture_resolution':8192,'facial_likeness_texture':'inherited lower-resolution reference texture, not newly captured 8K detail'}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-E19-8K.blend'),compress=True)

# Separate portable preview; master GLB and saved BLEND retain the actual 8K bakes.
replaced={}
for m in bpy.data.materials:
    if not m.use_nodes:continue
    for n in m.node_tree.nodes:
        if n.type!='TEX_IMAGE' or not n.image or max(n.image.size)<=2048:continue
        old=n.image
        if old.name not in replaced:
            small=old.copy();small.name=old.name+' web2048';small.scale(2048,2048)
            replaced[old.name]=small
        n.image=replaced[old.name]
web=OUT/'FORGE-E19-web.glb'
bpy.ops.export_scene.gltf(filepath=str(web),export_format='GLB',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_apply=True)
report['versions']['web']={'path':web.name,'sha256':sha(web),'bytes':web.stat().st_size,'body_texture_resolution':2048}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print('E19_EXPORTS_COMPLETE',json.dumps(report['versions']),flush=True)
