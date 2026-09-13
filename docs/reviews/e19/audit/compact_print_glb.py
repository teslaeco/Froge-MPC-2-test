import bpy
from pathlib import Path
root=Path('/workspace/scratch/584c9d97a5a1/e19/print')
bpy.ops.wm.open_mainfile(filepath=str(root/'FORGE-E19-print-candidate-200mm.blend'))
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
# millimetre BLEND -> metre glTF. Smooth normals affect appearance only.
mesh.scale=(.001,)*3
for face in mesh.data.polygons:face.use_smooth=True
bpy.context.view_layer.objects.active=mesh;mesh.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'FORGE-E19-print-candidate-200mm.glb'),export_format='GLB',use_selection=True,export_materials='NONE',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=30,export_draco_normal_quantization=16)
