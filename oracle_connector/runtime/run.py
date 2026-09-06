"""Runs only inside the isolated Blender container, with /runner read-only and /work writable."""
import bpy
import builtins
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import numpy as np
from mathutils import Vector

# Blender's --python launcher need not add the script's directory to sys.path.
# Only our read-only renderer directory is added, never the writable job folder.
sys.path.insert(0, str(Path(__file__).resolve().parent))

def make_material(name, rgb, pattern='plain', roughness=0.7, metallic=0.0):
    if len(bpy.data.materials) >= 8:
        raise ValueError('Use at most 8 materials, reusing them across objects.')
    rgb = np.clip(np.array(rgb[:3], dtype=float), 0, 1)
    material = bpy.data.materials.new(str(name)[:80])
    material.diffuse_color = (*rgb, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = max(0, min(1, float(roughness)))
    shader.inputs['Metallic'].default_value = max(0, min(1, float(metallic)))
    if pattern != 'plain':
        n = 512
        seed = int.from_bytes(hashlib.sha256(str(name).encode()).digest()[:4], 'little')
        rng = np.random.default_rng(seed)
        y, x = np.mgrid[0:1:complex(n), 0:1:complex(n)]
        noise = rng.random((n, n)) - 0.5
        if pattern in ('bark', 'wood'):
            waves = np.sin(x * 110 + 3 * np.sin(y * 14) + 0.5 * np.sin(y * 63))
            texture = 0.82 + 0.2 * waves + 0.18 * noise
            if pattern == 'bark':
                texture -= (waves < -0.75) * 0.35
        elif pattern == 'leaf':
            veins = np.maximum(0, np.cos((y + np.abs(x - 0.5) * 0.7) * 80)) ** 12
            texture = 0.82 + 0.14 * np.sin(y * 8) + 0.16 * veins + 0.08 * noise
            texture += 0.14 * np.exp(-((x - 0.5) * 110) ** 2)
        elif pattern == 'fabric':
            texture = 0.9 + 0.12 * np.sin(x * 350) * np.cos(y * 350) + 0.1 * noise
        elif pattern == 'metal':
            texture = 0.94 + 0.06 * np.sin(x * 1100) + 0.08 * noise
        else:
            texture = 0.85 + 0.16 * np.sin(x * 40 + np.sin(y * 18)) + 0.22 * noise
        pixels = np.ones((n, n, 4), dtype=np.float32)
        pixels[:, :, :3] = np.clip(texture[:, :, None] * rgb, 0, 1)
        image = bpy.data.images.new(str(name)[:64] + '-UV', width=n, height=n, alpha=False)
        image.pixels.foreach_set(pixels.reshape(-1))
        image.update()
        image.file_format = 'PNG'
        image.pack()
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    return material

def mesh_object(name, vertices, faces, material):
    mesh = bpy.data.meshes.new(str(name)[:80])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(str(name)[:80], mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    return obj

def tube(name, points, radii, material, sides=12):
    points = [Vector(p) for p in points]
    if len(points) < 2 or len(points) != len(radii) or len(points) > 200:
        raise ValueError('tube needs 2-200 points and one radius per point')
    sides = max(3, min(48, int(sides)))
    vertices, faces = [], []
    for i, point in enumerate(points):
        tangent = (points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]).normalized()
        ref = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
        axis = tangent.cross(ref).normalized()
        other = tangent.cross(axis).normalized()
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            vertices.append(tuple(point + max(0.0001, float(radii[i])) * (axis * math.cos(angle) + other * math.sin(angle))))
    for i in range(len(points) - 1):
        for j in range(sides):
            faces.append((i * sides + j, i * sides + (j + 1) % sides, (i + 1) * sides + (j + 1) % sides, (i + 1) * sides + j))
    faces.extend([tuple(reversed(range(sides))), tuple((len(points) - 1) * sides + j for j in range(sides))])
    obj = mesh_object(name, vertices, faces, material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    uv = obj.data.uv_layers.new(name='UVMap')
    for loop in obj.data.loops:
        ring, j = divmod(loop.vertex_index, sides)
        uv.data[loop.index].uv = (j / sides, ring / (len(points) - 1))
    return obj

def ellipsoid(name, center, scale, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=max(1, min(3, int(subdivisions))), radius=1, location=center)
    obj = bpy.context.object
    obj.name, obj.scale = str(name)[:80], scale
    if material:
        obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj

def join_meshes(objects, name):
    objects = [o for o in objects if o and o.type == 'MESH']
    if not objects:
        raise ValueError('No meshes to join')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.context.object.name = name
    return bpy.context.object

def finish():
    if len(bpy.data.materials) > 8 or len(bpy.data.images) > 8:
        raise ValueError('Use at most 8 materials and 8 images.')
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not objects or len(objects) > 256:
        raise ValueError('Scene needs 1-256 mesh objects; join repeated small details.')
    for obj in objects:
        if any(m.type == 'SUBSURF' and m.levels > 2 for m in obj.modifiers):
            raise ValueError('Subdivision limit: 2.')
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    for axis in range(3):
        values = [p[axis] for p in points]
        if not all(math.isfinite(v) for v in values) or max(values) - min(values) <= 1e-7:
            raise ValueError('The complete asset must have finite, nonzero width, height and depth.')
    vertices = sum(len(o.data.vertices) for o in objects)
    triangles = sum(sum(max(0, len(p.vertices) - 2) for p in o.data.polygons) for o in objects)
    if vertices > 200000 or not 1 <= triangles <= 400000:
        raise ValueError('Geometry limit: 200000 vertices, 400000 triangles.')
    for obj in objects:
        mesh = obj.data
        if not mesh.uv_layers:
            uv = mesh.uv_layers.new(name='UVMap')
            coords = np.array([tuple(v.co) for v in mesh.vertices])
            if not len(coords):
                continue
            axes = np.argsort(np.ptp(coords, axis=0))[-2:]
            minimum, span = coords.min(axis=0), np.maximum(np.ptp(coords, axis=0), 1e-6)
            for loop in mesh.loops:
                uv.data[loop.index].uv = tuple(((coords[loop.vertex_index] - minimum) / span)[axes])
    for image in bpy.data.images:
        if image.size[0] > 1024 or image.size[1] > 1024:
            image.scale(min(image.size[0], 1024), min(image.size[1], 1024))
        # Packing an unchanged generated image again can discard its packed PNG
        # in Blender 4.3 when it has no external filepath. Preserve those bytes.
        if image.has_data and (image.packed_file is None or image.is_dirty):
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath='/work/model.blend')
    bpy.ops.export_scene.gltf(filepath='/work/model.glb', export_format='GLB', export_image_format='AUTO', export_cameras=False, export_lights=False)
    Path('/work/result.json').write_text(json.dumps({'vertices': vertices, 'triangles': triangles, 'objects': len(objects), 'images': len(bpy.data.images)}))

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if Path('/work/scene.json').is_file():
        from scene_contract import parse_scene
        from build_scene import build_scene
        scene = parse_scene(Path('/work/scene.json').read_text(encoding='utf-8'))
        build_scene(scene, make_material, mesh_object, tube, ellipsoid, join_meshes)
        finish()
        print('FROGE_MODEL_READY')
        raise SystemExit(0)
    code = Path('/work/generate.py').read_text(encoding='utf-8')
    # Validation is also done on the host. Secrets and the host filesystem are never mounted.
    allowed = {'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'int', 'isinstance', 'len', 'list', 'max', 'min', 'pow', 'print', 'range', 'reversed', 'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip', 'Exception', 'ValueError'}
    safe_builtins = {name: getattr(builtins, name) for name in allowed}
    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name not in {'bpy', 'math', 'random', 'mathutils'}:
            raise ImportError('Import blocked')
        return builtins.__import__(name, globals, locals, fromlist, level)
    safe_builtins['__import__'] = restricted_import
    scope = {'__builtins__': safe_builtins, 'bpy': bpy, 'math': math, 'random': random,
             'Vector': Vector, 'make_material': make_material, 'mesh_object': mesh_object,
             'tube': tube, 'ellipsoid': ellipsoid, 'join_meshes': join_meshes}
    exec(compile(code, '/work/generate.py', 'exec'), scope, scope)
    finish()
    print('FROGE_MODEL_READY')
