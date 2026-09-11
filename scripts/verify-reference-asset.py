"""Native Blender regression cases for the reference asset inspector.

blender -b --python-exit-code 1 --python scripts/verify-reference-asset.py -- /tmp/audit-test
"""
import json
from pathlib import Path
import runpy
import sys

import bpy

audit = runpy.run_path(str(Path(__file__).with_name('inspect-reference-asset.py')))
output = Path(sys.argv[sys.argv.index('--') + 1])
output.mkdir(parents=True, exist_ok=True)
checks = []
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.object
source = output / 'cube.glb'
bpy.ops.export_scene.gltf(filepath=str(source), export_format='GLB')
report = audit['inspect'](source)
assert report['totals']['triangles'] == 12 and report['totals']['boundary_edges'] == 0
assert audit['validate'](report, require_textures=True)['status'] == 'failed'
checks.append('Closed cube has 12 triangles; missing material fails texture admission.')

mat = bpy.data.materials.new('Used 4K texture')
mat.use_nodes = True
image = bpy.data.images.new('Native 4096 x 16', width=4096, height=16, alpha=False)
image.generated_color = (.15, .3, .5, 1)
node = mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image = image
mat.node_tree.links.new(node.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
cube.data.materials.append(mat)
unused = bpy.data.images.new('Unused 8K must not count', width=8192, height=16)
unused_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
unused_node.image = unused  # Deliberately not connected to the active shader.
report = audit['inspect'](source)
assert audit['validate'](report, min_base_color_edge=4096)['status'] == 'passed'
assert audit['validate'](report, min_base_color_edge=8192)['status'] == 'failed'
assert report['texture_evidence']['minimum_loaded_base_color_long_edge'] == 4096
checks.append('An unconnected 8K image does not qualify a 4K material as 8K.')

missing = bpy.data.images.new('Missing file', width=8, height=8)
missing.source = 'FILE'
missing.filepath = str(output / 'does-not-exist.png')
node.image = missing
report = audit['inspect'](source)
assert audit['validate'](report, require_textures=True)['status'] == 'failed'
checks.append('A missing connected texture is rejected.')

node.image = image
cube.data.uv_layers.remove(cube.data.uv_layers[0])
report = audit['inspect'](source)
assert audit['validate'](report, require_textures=True)['status'] == 'failed'
checks.append('A texture without a mesh UV layer does not pass texture admission.')

# A triangle is an open surface even though every coordinate is valid.
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new('Open triangle')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
obj = bpy.data.objects.new('Open triangle', mesh)
bpy.context.collection.objects.link(obj)
report = audit['inspect'](source)
assert report['totals']['boundary_edges'] == 3 and report['totals']['triangles'] == 1
checks.append('An open triangle reports three boundary edges; no print-readiness claim.')

(output / 'verification.json').write_text(json.dumps({'blender': bpy.app.version_string,
    'passed': len(checks), 'checks': checks}, indent=2) + '\n')
print('FROGE_REFERENCE_ASSET_CHECKS_OK', len(checks), flush=True)
