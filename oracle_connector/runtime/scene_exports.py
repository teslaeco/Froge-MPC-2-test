"""Portable exports of the completed master, with explicit partial failures."""
from contextlib import contextmanager
import hashlib
import re
from pathlib import Path


def _file_record(path, output):
    data = path.read_bytes()
    if not data:
        raise ValueError('Exporter produced an empty file: ' + path.name)
    return {'path': path.relative_to(output).as_posix(), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


@contextmanager
def _portable_images(bpy, output, report):
    """Bind temporary file images during export; restore original nodes afterward.

    Empty paths alias unrelated FBX maps. OBJ cannot copy packed images.
    """
    materials = {m for o in bpy.context.scene.objects if o.type == 'MESH'
                 for m in o.data.materials if m and m.use_nodes}
    images = {n.image for m in materials for n in m.node_tree.nodes
              if n.type == 'TEX_IMAGE' and n.image}
    original = []
    temporary = []
    try:
        folder = output / 'textures'
        folder.mkdir(exist_ok=True)
        for index, image in enumerate(sorted(images, key=lambda item: item.name)):
            if image.source not in {'FILE', 'GENERATED'} or min(image.size) < 1:
                raise ValueError('Unsupported or missing texture: ' + image.name)
            if image.packed_file is None or image.is_dirty:
                image.pack()
            if image.packed_file is None:
                raise ValueError('Texture could not be packed: ' + image.name)
            data = bytes(image.packed_file.data)
            if data.startswith(b'\x89PNG\r\n\x1a\n'):
                suffix = '.png'
            elif data.startswith(b'\xff\xd8\xff'):
                suffix = '.jpg'
            else:
                raise ValueError('Texture must be packed PNG or JPEG: ' + image.name)
            digest = hashlib.sha256(data).hexdigest()
            label = re.sub(r'[^A-Za-z0-9_-]+', '-', image.name).strip('-')[:48] or 'image'
            target = folder / ('%02d-%s-%s%s' % (index, label, digest[:12], suffix))
            target.write_bytes(data)
            # OBJ's native exporter ignores GENERATED/packed sources even with
            # a filepath. Temporarily bind ordinary file images to the same nodes.
            portable = bpy.data.images.load(str(target.resolve()), check_existing=False)
            portable.colorspace_settings.name = image.colorspace_settings.name
            portable.alpha_mode = image.alpha_mode
            temporary.append(portable)
            for material in materials:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == image:
                        original.append((node, image))
                        node.image = portable
            report['textures'].append({**_file_record(target, output), 'image': image.name,
                                       'size': list(image.size), 'pixels_resampled': False})
        yield
    finally:
        for node, image in original:
            node.image = image
        for image in temporary:
            bpy.data.images.remove(image)


def _checked_export(report, output, key, format_name, filenames, operation):
    entry = report[key]
    try:
        # A cancelled operator must not make stale output look successful.
        for name in filenames:
            (output / name).unlink(missing_ok=True)
        status = operation()
        if status != {'FINISHED'}:
            raise RuntimeError('Export did not finish: ' + str(status))
        records = [_file_record(output / name, output) for name in filenames]
        if key == 'obj':
            for line in (output / 'model.mtl').read_text().splitlines():
                if line.startswith(('map_', 'bump ', 'disp ', 'norm ')):
                    path = (output / line.split()[-1]).resolve()
                    if not path.is_relative_to(output.resolve()) or not path.is_file():
                        raise ValueError('OBJ material references a missing texture')
        entry.update(status='ready', files=records)
        report['formats'].append(format_name)
    except Exception as error:
        for name in filenames:
            (output / name).unlink(missing_ok=True)
        entry.update(status='failed', error=str(error)[:400])


def export_interchange(output, scene_source=None):
    import bpy

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {
        'revision': 2, 'formats': [], 'same_master_scene': True, 'textures': [],
        'fbx': {'axis_forward': '-Z', 'axis_up': 'Y', 'textures_embedding_requested': True,
                'reimport_verified': False,
                'shader_boundary': 'FBX preserves supported image-based channels, not every Blender PBR shader',
                'rig_policy': 'Export existing armatures and animation; do not invent a rig'},
        'obj': {'mtl': 'model.mtl', 'uvs_requested': True, 'normals_requested': True,
                'reimport_verified': False,
                'shader_boundary': 'OBJ/MTL cannot reproduce every Blender or glTF PBR shader'},
        'stl': {'numeric_unit': 'millimetre', 'textures': False,
                'print_readiness_assessed': False, 'reimport_verified': False},
        'scene_json': {'schema': 'Froge scene contract', 'present': False, 'status': 'unavailable'},
    }
    for name, format_name in (('model.glb', 'glb'), ('model.blend', 'blend')):
        path = output / name
        if path.is_file() and path.stat().st_size:
            report['formats'].append(format_name)
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    try:
        bpy.ops.object.select_all(action='SELECT')
        try:
            with _portable_images(bpy, output, report):
                _checked_export(report, output, 'fbx', 'fbx', ['model.fbx'], lambda:
                    bpy.ops.export_scene.fbx(
                        filepath=str(output / 'model.fbx'), use_selection=True,
                        apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                        axis_forward='-Z', axis_up='Y', add_leaf_bones=False,
                        bake_anim=True, path_mode='COPY', embed_textures=True))
                _checked_export(report, output, 'obj', 'obj+mtl', ['model.obj', 'model.mtl'], lambda:
                    bpy.ops.wm.obj_export(
                        filepath=str(output / 'model.obj'), export_selected_objects=True,
                        export_materials=True, export_pbr_extensions=True,
                        export_uv=True, export_normals=True,
                        forward_axis='NEGATIVE_Z', up_axis='Y', path_mode='RELATIVE'))
        except Exception as error:
            for key in ('fbx', 'obj'):
                report[key].update(status='failed', error=str(error)[:400])
        # STL has no unit metadata: write numeric millimetres.
        scale = 1000.0 * bpy.context.scene.unit_settings.scale_length
        _checked_export(report, output, 'stl', 'stl', ['model-mm.stl'], lambda:
            bpy.ops.wm.stl_export(
                filepath=str(output / 'model-mm.stl'), export_selected_objects=True,
                global_scale=scale, use_scene_unit=False,
                forward_axis='NEGATIVE_Z', up_axis='Y'))
        if scene_source and Path(scene_source).is_file():
            target = output / 'model.froge-scene.json'
            try:
                target.write_bytes(Path(scene_source).read_bytes())
                record = _file_record(target, output)
                report['scene_json'].update(status='ready', present=True, files=[record])
                report['formats'].append('froge-scene-json')
            except Exception as error:
                report['scene_json'].update(status='failed', error=str(error)[:400])
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
    report['status'] = 'partial' if any(report[k].get('status') == 'failed'
                                      for k in ('fbx', 'obj', 'stl', 'scene_json')) else 'ready'
    return report
