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
    # Scene RGB is display/sRGB, just like the packed PNG texture values.
    # Principled constants are linear; without this conversion plain gems/hair
    # become much paler than adjacent textured surfaces using the same color.
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    shader.inputs['Base Color'].default_value = (*linear, 1)
    shader.inputs['Roughness'].default_value = max(0, min(1, float(roughness)))
    shader.inputs['Metallic'].default_value = max(0, min(1, float(metallic)))
    if pattern == 'crystal':
        # Faceted gemstones keep their colour through dielectric coat and a
        # little transmission.  Metallic crystal produced chrome-white panels.
        shader.inputs['Metallic'].default_value=min(.08,float(metallic))
        shader.inputs['Coat Weight'].default_value=.58
        shader.inputs['Coat Roughness'].default_value=.12
        shader.inputs['IOR'].default_value=1.48
        shader.inputs['Transmission Weight'].default_value=.10
        shader.inputs['Roughness'].default_value=max(.16,min(.24,float(roughness)))
    if pattern == 'satin':
        # Satin is reflective cloth, not metal.  A larger metallic factor made
        # broad studio highlights turn the emerald gown into silver armour.
        shader.inputs['Coat Weight'].default_value=.06
        shader.inputs['Coat Roughness'].default_value=.45
        shader.inputs['Specular IOR Level'].default_value=.26
        shader.inputs['Sheen Weight'].default_value=.27
        # Blender 4.3 glTF exports the sheen tint independently of its weight.
        # Leaving the default white tint exported sheenColorFactor=[1,1,1],
        # which overwhelmed emerald albedo and made the whole gown silver.
        shader.inputs['Sheen Tint'].default_value=(*np.minimum(linear*.35,.08),1)
        shader.inputs['Roughness'].default_value=max(.48,min(.58,float(roughness)))
        shader.inputs['Metallic'].default_value=min(.06,float(metallic))
    if pattern in ('skin', 'fabric'):
        shader.inputs['Metallic'].default_value = 0
        shader.inputs['Roughness'].default_value = max(.5 if pattern == 'skin' else .75, float(roughness))
    if pattern in ('cotton','denim'):
        import textiles
        textiles.apply(material,pattern,rgb)
        return material
    if pattern not in ('plain','crystal'):
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
        elif pattern in ('fabric','satin'):
            texture = 0.98 + 0.008 * np.sin(x * 450) * np.cos(y * 450) + 0.012 * noise
        elif pattern == 'metal':
            texture = 0.94 + 0.06 * np.sin(x * 1100) + 0.08 * noise
        elif pattern == 'windows':
            cols, rows = 12, 48
            fx, fy = (x*cols)%1, (y*rows)%1
            panes = rng.uniform(.56, 1.06, (rows, cols))
            texture = panes[np.minimum((y*rows).astype(int),rows-1),np.minimum((x*cols).astype(int),cols-1)]
            texture = texture * (.88+.16*fx) + .08*np.sin(y*math.pi*4)
            texture = np.where((fx<.04)|(fy<.08),1.35,texture)
        elif pattern == 'skin':
            texture = .985 + .022*noise + .006*np.sin(x*310)*np.cos(y*370)
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

def ellipsoid(name, center, scale, material, subdivisions=4):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=max(1, min(4, int(subdivisions))), radius=1, location=center)
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

def finish(output=None):
    output=Path('/work') if output is None else Path(output)
    # A material may have both an albedo and a normal map. Eight legitimate
    # textured materials therefore need more than eight image datablocks.
    # Replaced eyebrow meshes and temporary Boolean cutters can retain unused
    # material/image users after their objects are deleted. Release those data
    # blocks before applying the budget to the actual export.
    for mesh in list(bpy.data.meshes):
        if mesh.users==0:bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    extra=max(0,bpy.context.scene.get('expected_heads',0)-1)
    if len(bpy.data.materials) > 16+4*extra or len(bpy.data.images) > 16+4*extra:
        raise ValueError('Export limit: 16 used materials and 16 used texture images. Plans still allow 8 shared materials. Actual: %d materials, %d images.' % (len(bpy.data.materials),len(bpy.data.images)))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not objects or len(objects) > 256:
        raise ValueError('Scene needs 1-256 mesh objects; join repeated small details.')
    from portrait import verify_components
    quality=verify_components(objects,bpy.context.scene.get('expected_heads',0),bpy.context.scene.get('expected_hands',0))
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
    heads=bpy.context.scene.get('expected_heads',0)
    if heads > 3:raise ValueError('Scene supports at most three detailed characters.')
    allowance=max(1,heads)
    vertex_limit=(320000 if heads else 250000)*allowance
    triangle_limit=(640000 if heads else 500000)*allowance
    if vertices > vertex_limit or not 1 <= triangles <= triangle_limit:
        raise ValueError('Geometry limit exceeded; keep portrait anatomy and simplify clothing or background.')
    for obj in objects:
        mesh = obj.data
        if obj.get('anatomical_head'):
            obj['makeup_tint_required']=mesh.color_attributes.get('CosmeticTint') is not None
        if not mesh.uv_layers:
            uv = mesh.uv_layers.new(name='UVMap')
            coords = np.array([tuple(v.co) for v in mesh.vertices])
            if not len(coords):
                continue
            axes = np.argsort(np.ptp(coords, axis=0))[-2:]
            minimum, span = coords.min(axis=0), np.maximum(np.ptp(coords, axis=0), 1e-6)
            for loop in mesh.loops:
                uv.data[loop.index].uv = tuple(((coords[loop.vertex_index] - minimum) / span)[axes])
    from reference_quality import export_textures, geometry_digest
    geometry_before = geometry_digest(objects)
    texture_report = export_textures(list(bpy.data.images), output)
    if geometry_before != geometry_digest(objects):
        raise ValueError('Texture export changed mesh, pose, UVs or material assignments.')
    texture_report['geometry_preserved_during_texture_export'] = True
    texture_report['geometry_sha256_before_export'] = geometry_before
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'model.blend'))
    high_quality=bpy.context.scene.get('material_max_edge',2048)>2048
    bpy.ops.export_scene.gltf(filepath=str(output/'model.glb'), export_format='GLB', export_image_format='AUTO', export_cameras=False, export_lights=False, export_extras=True,
                             export_vertex_color='ACTIVE',
                             export_draco_mesh_compression_enable=heads>1 and not high_quality,export_draco_position_quantization=16)
    report={'vertices':vertices,'triangles':triangles,'objects':len(objects),'images':len(bpy.data.images),'portrait_quality':quality,
            'characterStandard':20,'reference_likeness_verified':False,
            'master_export':{'formats':['blend','glb'],'decimation_applied':False,
                             'position_quantization_applied':heads>1 and not high_quality}}
    report['texture_quality']=texture_report
    report['photo_face_fit']=json.loads(bpy.context.scene.get('photo_face_fit','{}'))
    if heads:
        from couture_qa import verify_export
        report['export_validation']=verify_export(output/'model.glb',objects)
    from scene_exports import export_interchange
    report['interchange_exports']=export_interchange(
        output, output/'scene.json' if (output/'scene.json').is_file() else None)
    report['master_export']['formats']=report['interchange_exports']['formats']
    (output/'result.json').write_text(json.dumps(report))
    review_request=output/'review-request.json'
    if review_request.is_file() and json.loads(review_request.read_text()).get('enabled') is True:
        from review_views import render_review_checked
        report['review_render']=render_review_checked(output/'model.glb',output/'review')
        (output/'result.json').write_text(json.dumps(report))

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if Path('/work/scene.json').is_file():
        from scene_contract import parse_scene
        from build_scene import build_scene
        scene = parse_scene(Path('/work/scene.json').read_text(encoding='utf-8'))
        build_scene(scene, make_material, mesh_object, tube, ellipsoid, join_meshes, reference_folder=Path('/work'))
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
