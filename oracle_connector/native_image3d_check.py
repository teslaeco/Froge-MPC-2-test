"""Run with Blender --background --python this.py -- OUTDIR.

An authored transport fixture, NOT a generated character or likeness test.
Exercises original preservation, preview resampling and actual export reimports.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent / 'runtime'))
from imported_asset import import_and_export


def metrics():
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        o.data.calc_loop_triangles()
    points = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    return {'triangles': sum(len(o.data.loop_triangles) for o in meshes),
            'dimensions': [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]}


folder = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
folder.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
image = bpy.data.images.new('transport-fixture-8192x64', width=8192, height=64)
pixels = np.ones((64, 8192, 4), dtype=np.float32)
pixels[:, :, 0] = np.linspace(.1, .9, 8192)[None, :]
pixels[:, :, 1] = .35
pixels[:, :, 2] = np.linspace(.8, .1, 64)[:, None]
image.pixels.foreach_set(pixels.ravel())
image.pack()
material = bpy.data.materials.new('UV gradient fixture'); material.use_nodes = True
node = material.node_tree.nodes.new('ShaderNodeTexImage'); node.image = image
material.node_tree.links.new(node.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
bpy.ops.mesh.primitive_cube_add(location=(-.9, 0, .2), scale=(.4, .6, .8))
bpy.context.object.data.materials.append(material)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=(.5, .1, .2), scale=(1,.7,1.3))
bpy.context.object.data.materials.append(material)
source = folder / 'model-master.glb'
bpy.ops.export_scene.gltf(filepath=str(source), export_format='GLB')
# Valid, unused binary buffer padding triggers the large-master branch while
# retaining a small, fast fixture. No input or texture resolution is fabricated.
raw = source.read_bytes()
json_size = struct.unpack_from('<I', raw, 12)[0]
document = json.loads(raw[20:20+json_size])
at = 20 + json_size
if struct.unpack_from('<I', raw, at + 4)[0] != 0x004E4942:
    raise RuntimeError('Expected BIN chunk')
padding = 49 * 1024**2
binary = raw[at+8:] + b'\0' * padding
document['buffers'][0]['byteLength'] = len(binary)
encoded = json.dumps(document).encode(); encoded += b' ' * (-len(encoded) % 4)
raw = struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary)) + struct.pack('<II',len(encoded),0x4e4f534a) + encoded + struct.pack('<II',len(binary),0x004e4942) + binary
source.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
del raw
(folder / 'image3d-manifest.json').write_text(json.dumps({'revision': 1,
    'provider': 'offline-authored-test-fixture', 'files': [{'path': source.name,
    'bytes': source.stat().st_size, 'sha256': digest}], 'textures': [],
    'likeness_verified': False}), encoding='utf-8')
report = import_and_export(folder)
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
assert report['preview']['textures_reduced'] is True
assert report['master_textures'][0]['size'] == [8192, 64]
assert report['preview']['textures'][0]['size'] == [4096, 32]
results = {}
for format in ('master', 'preview', 'fbx', 'obj', 'stl'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if format in ('master', 'preview'):
        bpy.ops.import_scene.gltf(filepath=str(source if format == 'master' else folder / 'model.glb'))
    elif format == 'fbx':
        bpy.ops.import_scene.fbx(filepath=str(folder / 'model.fbx'))
    elif format == 'obj':
        bpy.ops.wm.obj_import(filepath=str(folder / 'model.obj'))
    else:
        bpy.ops.wm.stl_import(filepath=str(folder / 'model-mm.stl'), global_scale=.001, forward_axis='NEGATIVE_Z', up_axis='Y')
    result = metrics()
    assert result['triangles'] == report['triangles'], (format, result)
    assert max(abs(a-b) for a,b in zip(result['dimensions'], report['dimensions_m'])) < .0001, (format, result)
    if format in ('master', 'preview', 'fbx', 'obj'):
        result['textures'] = [list(i.size) for i in bpy.data.images if i.type == 'IMAGE']
        assert [4096, 32] in result['textures'] if format == 'preview' else [8192, 64] in result['textures'], (format, result)
    results[format] = result
results['kind'] = 'offline authored fixture; no neural generation or likeness claim'
(folder / 'native-verification.json').write_text(json.dumps(results, indent=2))
print('NATIVE_IMAGE3D_EXPORTS_OK', json.dumps(results))
