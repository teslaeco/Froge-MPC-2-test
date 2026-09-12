import bpy,shutil,json,tempfile
from pathlib import Path
source=Path('/workspace/scratch/584c9d97a5a1/face-repair/delivery/FORGE-model-1M.fbx')
with tempfile.TemporaryDirectory(prefix='forge-fbx-portable-',dir='/tmp') as directory:
 root=Path(directory);target=root/source.name;shutil.copyfile(source,target)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(target))
 used={n.image for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
 images=[{'name':i.name,'size':list(i.size),'embedded_extracted':Path(bpy.path.abspath(i.filepath)).resolve().is_relative_to(root),'available':min(i.size)>0} for i in used]
 assert all(i['embedded_extracted'] and i['available'] for i in images),images
 report={'fbx_alone_portable':True,'images':images}
 (source.parent/'fbx-portability-report.json').write_text(json.dumps(report,indent=2));print('FBX_EMBEDDED_PORTABLE_PASS',len(images))
