"""Build and inspect complete authored scenes in real Blender; no mocked bpy or AI.

The optional output directory saves the oak GLB and a review render. Its timing
measures this host's Blender stage, never OpenAI latency or the Oracle ARM host.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
import tempfile
import time

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'runtime'))
from scene_contract import parse_scene
from build_scene import build_scene


def components(mesh):
    parent = list(range(len(mesh.vertices)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for edge in mesh.edges:
        a, b = map(find, edge.vertices)
        parent[a] = b
    return len({find(i) for i in parent})


def inspect_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert (magic, version, length) == (0x46546C67, 2, len(data))
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(data[20:20+size])
    for image in doc.get('images', []):
        assert image.get('mimeType') == 'image/png' and 'uri' not in image
        view = doc['bufferViews'][image['bufferView']]
        start = 28+size+view.get('byteOffset', 0)
        assert data[start:start+8] == b'\x89PNG\r\n\x1a\n' and view['byteLength'] > 1000
    assert all('uri' not in b for b in doc['buffers'])
    return doc, len(data)


def render_review(folder):
    bpy.ops.object.camera_add(location=(10, -13, 9))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0,0,3))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type = 'ORTHO'; camera.data.ortho_scale = 8.2
    bpy.context.scene.camera = camera
    for location, energy, size in [((3,-5,9), 2200, 7), ((-5,1,6), 1700, 5), ((1,5,8), 2300, 4)]:
        bpy.ops.object.light_add(type='AREA', location=location)
        light = bpy.context.object; light.data.energy = energy; light.data.shape='DISK'; light.data.size=size
        light.rotation_euler = (Vector((0,0,3))-light.location).to_track_quat('-Z','Y').to_euler()
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('review-world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.055,0.075,0.09,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    scene.render.engine='CYCLES'; scene.cycles.samples=16
    scene.render.threads_mode='FIXED'; scene.render.threads=2
    scene.render.resolution_x=900; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(folder/'oak-review.png')
    bpy.ops.render.render(write_still=True)


def verify(name, folder, render=False):
    started=time.monotonic()
    scene=parse_scene((ROOT/'examples'/name).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Only trusted export paths differ from production. The functions are identical.
    code=(ROOT/'runtime/run.py').read_text().replace('/work/', str(folder)+'/')
    scope={'__name__':'froge_runtime_fixture', '__file__': str(ROOT/'runtime/run.py')}
    exec(compile(code, 'runtime/run.py', 'exec'), scope)
    built=build_scene(scene, *(scope[n] for n in ['make_material','mesh_object','tube','ellipsoid','join_meshes']))
    if name.startswith('oak'):
        assert len(built)==2
        assert len(built['dab'][1].data.vertices)>40000
        assert built['lampki'][1]['bulb_count']==20
        assert components(built['lampki'][1].data)==20
    scope['finish']()
    document, size=inspect_glb(folder/'model.glb')
    report=json.loads((folder/'result.json').read_text())
    assert report['vertices']<200000 and report['triangles']<400000
    if name.startswith('oak'):
        assert len(document['images'])==2
        assert any(max(m.get('emissiveFactor',[0]))>0 for m in document['materials'])
    result={'scene':name,'blender':bpy.app.version_string,'seconds':round(time.monotonic()-started,2),'glb_bytes':size,**report}
    print(json.dumps(result),flush=True)
    (folder/'verification.json').write_text(json.dumps(result,indent=2))
    if render:render_review(folder)
    # Reimport the self-contained GLB to exercise the exporter/importer contract.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/'model.glb'))
    assert any(o.type=='MESH' for o in bpy.context.scene.objects)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='froge-scene-') as temporary:
        base=Path(temporary)
        verify('rocket.scene.json',base)
        oak=Path(args.output) if args.output else base
        oak.mkdir(parents=True,exist_ok=True)
        verify('oak-lights.scene.json',oak,render=bool(args.output))
