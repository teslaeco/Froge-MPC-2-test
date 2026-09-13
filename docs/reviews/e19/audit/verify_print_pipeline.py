import bpy
from pathlib import Path
root=Path(__file__).resolve().parent/'fixture'
root.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.045,depth=.7,location=(0,0,.35))
bpy.context.object.name='fixture_body'
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.08,location=(0,0,.73))
bpy.context.object.name='fixture_head'
bpy.ops.export_scene.gltf(filepath=str(root/'fixture.glb'),export_format='GLB')
