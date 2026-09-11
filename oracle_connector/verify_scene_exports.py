"""Native portable export regression: Blender --background --python this_file."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'runtime'))
from scene_exports import export_interchange


def image_hash(image):
    data = bytes(image.packed_file.data) if image.packed_file else Path(bpy.path.abspath(image.filepath)).read_bytes()
    return hashlib.sha256(data).hexdigest()


def snapshot():
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    vertices = sorted({tuple(round(v, 5) for v in o.matrix_world @ point.co)
                       for o in meshes for point in o.data.vertices})
    materials = {}
    uv = {}
    for obj in meshes:
        for material in obj.data.materials:
            if material and material.use_nodes:
                materials[material.name] = sorted(image_hash(n.image) for n in material.node_tree.nodes
                                                  if n.type == 'TEX_IMAGE' and n.image)
        if obj.data.uv_layers:
            for loop in obj.data.loops:
                position = tuple(round(v, 5) for v in obj.matrix_world @ obj.data.vertices[loop.vertex_index].co)
                uv.setdefault(position, set()).add(tuple(round(v, 5) for v in obj.data.uv_layers.active.data[loop.index].uv))
    return {'vertices': vertices,
            'triangles': sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),
            'materials': materials, 'uv': uv}


def verify():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); output = root / 'original'; output.mkdir()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        originals = []
        for index, label in enumerate(('red', 'blue')):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(index * 2, 0, .5))
            obj = bpy.context.object; obj.name = label
            material = bpy.data.materials.new(label); material.use_nodes = True
            obj.data.materials.append(material)
            texture = bpy.data.images.new(label, width=8, height=8)
            pixels = []
            for y in range(8):
                for x in range(8):
                    pixels.extend(((x+1)/8, y/8, .05, 1) if index == 0 else (.03, y/8, (x+1)/8, 1))
            texture.pixels.foreach_set(pixels); texture.update(); texture.file_format = 'PNG'; texture.pack()
            assert texture.filepath == ''
            node = material.node_tree.nodes.new('ShaderNodeTexImage'); node.image = texture
            shader = material.node_tree.nodes.get('Principled BSDF')
            material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
            # The source uses a named second UV channel; FBX omits texture
            # UVSet names and previously displayed the decoy first channel.
            first=obj.data.uv_layers.active
            values=[tuple(loop.uv) for loop in first.data]
            for loop in first.data:loop.uv=(0.,0.)
            primary=obj.data.uv_layers.new(name='AlbedoUV')
            for loop,value in zip(primary.data,values):loop.uv=value
            obj.data.uv_layers.active=primary;primary.active_render=True
            uvnode=material.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=primary.name
            material.node_tree.links.new(uvnode.outputs['UV'],node.inputs['Vector'])
            originals.append((node, texture, image_hash(texture)))
        before = snapshot()
        selected = list(bpy.context.selected_objects)
        bpy.ops.wm.save_as_mainfile(filepath=str(output / 'model.blend'))
        bpy.ops.export_scene.gltf(filepath=str(output / 'model.glb'), export_format='GLB')
        report = export_interchange(output)
        assert report['status'] == 'ready', report
        assert set(report['formats']) == {'glb', 'blend', 'fbx', 'obj+mtl', 'stl'}
        assert not report['scene_json']['present']
        assert list(bpy.context.selected_objects) == selected
        for node, texture, digest in originals:
            assert node.image == texture and texture.filepath == '' and image_hash(texture) == digest
        assert snapshot() == before
        hidden = root / 'moved-original'; output.rename(hidden)
        portable = root / 'portable'; portable.mkdir()
        # FBX must work with only the FBX file and no accessible source textures.
        shutil.copy2(hidden / 'model.fbx', portable / 'model.fbx')
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(portable / 'model.fbx'))
        assert snapshot() == before, 'FBX geometry, UV or texture identity changed'
        shutil.copy2(hidden / 'model.obj', portable / 'model.obj')
        shutil.copy2(hidden / 'model.mtl', portable / 'model.mtl')
        shutil.copytree(hidden / 'textures', portable / 'textures')
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=str(portable / 'model.obj'), forward_axis='NEGATIVE_Z', up_axis='Y')
        assert snapshot() == before, 'Relocated OBJ geometry, UV or texture identity changed'
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.stl_import(filepath=str(hidden / 'model-mm.stl'), global_scale=.001,
                             forward_axis='NEGATIVE_Z', up_axis='Y')
        after = snapshot()
        assert after['vertices'] == before['vertices'] and after['triangles'] == before['triangles']
        assert not after['materials'] and not after['uv']
        return {'blender': bpy.app.version_string, 'triangles': before['triangles'],
                'packed_texture_count': 2, 'fbx_embedded_bytes_preserved': True,
                'obj_relocated_textures_preserved': True, 'uv_and_geometry_preserved': True,
                'master_state_preserved': True, 'stl_millimetres_verified': True,
                'named_secondary_colour_uv_preserved': True,
                'scope': 'Native regression fixture; does not claim every Blender shader survives interchange'}


if __name__ == '__main__':
    result = verify()
    if '--' in sys.argv:
        Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
