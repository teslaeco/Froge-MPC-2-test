"""Package a neural asset without building or fitting a procedural character."""
import hashlib
import json
import math
from pathlib import Path
import shutil

import bpy
from mathutils import Vector

from scene_exports import export_interchange, _file_record

PREVIEW_LIMIT = 48 * 1024**2


def import_and_export(folder):
    folder = Path(folder)
    source = folder / 'model-master.glb'
    manifest = json.loads((folder / 'image3d-manifest.json').read_text())
    record = next(r for r in manifest['files'] if r['path'] == source.name)
    if source.is_symlink() or source.stat().st_size != record['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Neural master is missing or changed; no template substituted.')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.ops.import_scene.gltf(filepath=str(source)) != {'FINISHED'}:
        raise ValueError('Neural GLB import failed.')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        raise ValueError('Neural model has no mesh.')
    triangles = 0
    for obj in meshes:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        if any(not math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co):
            raise ValueError('Non-finite mesh coordinates.')
    if not triangles:
        raise ValueError('Neural model has no triangles.')
    images = [i for i in bpy.data.images if i.type == 'IMAGE']
    if not images or any(min(i.size) < 1 for i in images):
        raise ValueError('Neural model has missing textures.')
    bounds = [obj.matrix_world @ Vector(p) for obj in meshes for p in obj.bound_box]
    dimensions = [max(p[i] for p in bounds) - min(p[i] for p in bounds) for i in range(3)]
    if not all(math.isfinite(x) and x > 0 for x in dimensions):
        raise ValueError('Model does not have a finite three-dimensional extent.')
    # glTF's numeric unit is metre. This does not establish a real person's
    # height: preserve the generator's scale and report that it is unmeasured.
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1
    master_images = [{'name': i.name, 'size': list(i.size)} for i in images]
    bpy.ops.file.pack_all()
    if bpy.ops.wm.save_as_mainfile(filepath=str(folder / 'model.blend')) != {'FINISHED'}:
        raise ValueError('Blender master could not be saved.')
    # Full-size FBX / OBJ / STL are made BEFORE reducing preview textures.
    exports = export_interchange(folder)
    exports['master'] = {'status': 'ready', 'files': [record],
                         'provider_bytes_preserved': True}
    exports['formats'].append('master-glb')
    exports['physical_dimensions_verified'] = False
    if exports['fbx'].get('status') != 'ready':
        raise ValueError('FBX export failed; original master retained for a free export retry.')
    preview = folder / 'model.glb'
    preview_images = master_images
    if source.stat().st_size <= PREVIEW_LIMIT:
        shutil.copyfile(source, preview)
    else:
        for maximum in (4096, 2048, 1024, 512):
            for image in images:
                width, height = image.size
                if max(width, height) > maximum:
                    factor = maximum / max(width, height)
                    image.scale(max(1, round(width * factor)), max(1, round(height * factor)))
                    image.pack()
            status = bpy.ops.export_scene.gltf(filepath=str(preview), export_format='GLB',
                export_image_format='AUTO', export_texcoords=True, export_normals=True,
                export_materials='EXPORT', export_extras=True, export_yup=True)
            if status != {'FINISHED'}:
                raise ValueError('Browser preview export failed; master retained.')
            if preview.stat().st_size <= PREVIEW_LIMIT:
                preview_images = [{'name': i.name, 'size': list(i.size)} for i in images]
                break
        else:
            raise ValueError('Mesh exceeds the browser preview budget; original master retained. No automatic geometry reduction applied.')
    report = {'source': 'image-to-3d', 'image3d': manifest, 'vertices': sum(len(o.data.vertices) for o in meshes),
              'triangles': triangles, 'objects': len(meshes), 'dimensions_m': dimensions,
              'master_textures': master_images, 'interchange_exports': exports,
              'preview': {'files': [_file_record(preview, folder)], 'textures': preview_images,
                          'geometry_reduced': False, 'master_modified': False,
                          'textures_reduced': preview_images != master_images},
              'likeness_verified': False, 'physical_dimensions_verified': False,
              'anatomy_template_used': False, 'reference_projection_used': False}
    (folder / 'result.json').write_text(json.dumps(report), encoding='utf-8')
    # Review failure is reported separately; valid master/exports survive OIDN
    # or other render issues. Images are real renders of the delivered GLB.
    from review_views import render_review_checked
    report['review_render'] = render_review_checked(preview, folder / 'review', asset_views=True)
    (folder / 'result.json').write_text(json.dumps(report), encoding='utf-8')
    return report
