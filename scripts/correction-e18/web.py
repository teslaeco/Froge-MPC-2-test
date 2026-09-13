import bpy,json
from pathlib import Path
P=Path('/workspace/scratch/584c9d97a5a1/correction-e18')
for im in bpy.data.images:
 if im.type!='IMAGE':continue
 w,h=im.size
 limit=512 if any(k in im.name.lower() for k in ('rough','normal','weave','microrelief')) else 1024
 if max(w,h)>limit:
  r=limit/max(w,h);im.scale(max(1,int(w*r)),max(1,int(h*r)));im.pack()
bpy.ops.export_scene.gltf(filepath=str(P/'FORGE-model-E18-web.glb'),export_format='GLB',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=14,export_draco_normal_quantization=10,export_draco_texcoord_quantization=12,export_cameras=False,export_lights=False,export_animations=False)
print('WEB_BYTES',(P/'FORGE-model-E18-web.glb').stat().st_size,flush=True)
