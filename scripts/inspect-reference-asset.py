"""Inspect an actual FBX/GLB and optionally render untextured review views.

blender -b --disable-autoexec --python-exit-code 1 --python \
  scripts/inspect-reference-asset.py -- --input /path/model.fbx --output /path/review

This reports geometry and texture evidence, not a likeness or printability score.
It never saves over the input or changes the production generator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
import numpy as np


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def values(collection, field, size=1, dtype=np.int32):
    result = np.empty(len(collection) * size, dtype=dtype)
    collection.foreach_get(field, result)
    return result


def mesh_record(obj):
    mesh = obj.data
    face_sizes = values(mesh.polygons, 'loop_total')
    edge_uses = np.bincount(values(mesh.loops, 'edge_index'), minlength=len(mesh.edges))
    vertex_uses = np.bincount(values(mesh.loops, 'vertex_index'), minlength=len(mesh.vertices))
    coordinates = values(mesh.vertices, 'co', 3, np.float32).reshape(-1, 3)
    corners = [obj.matrix_world @ Vector(point) for point in obj.bound_box]
    assigned = set(values(mesh.polygons, 'material_index').tolist())
    return {
        'name': obj.name,
        'vertices': len(mesh.vertices),
        'faces': len(mesh.polygons),
        'triangles': int(np.maximum(face_sizes - 2, 0).sum()),
        'edges': len(mesh.edges),
        'boundary_edges': int(np.count_nonzero(edge_uses == 1)),
        'wire_edges': int(np.count_nonzero(edge_uses == 0)),
        'edges_with_more_than_two_faces': int(np.count_nonzero(edge_uses > 2)),
        'vertices_unused_by_faces': int(np.count_nonzero(vertex_uses == 0)),
        'nonfinite_vertices': int(np.count_nonzero(~np.isfinite(coordinates).all(axis=1))),
        'uv_layers': [layer.name for layer in mesh.uv_layers],
        'material_slots': [slot.material.name if slot.material else None for slot in obj.material_slots],
        'used_materials': sorted({obj.material_slots[i].material.name for i in assigned
                                  if i < len(obj.material_slots) and obj.material_slots[i].material}),
        'unassigned_material_faces': sum(1 for face in mesh.polygons
                                        if face.material_index >= len(obj.material_slots)
                                        or obj.material_slots[face.material_index].material is None),
        'world_bounds': {
            'min': [min(c[i] for c in corners) for i in range(3)],
            'max': [max(c[i] for c in corners) for i in range(3)],
        },
        'matrix_world': [list(row) for row in obj.matrix_world],
    }


def upstream_nodes(socket, seen=None):
    """Traverse connected shader inputs; no claim about procedural/UV quality."""
    seen = set() if seen is None else seen
    for link in socket.links:
        node = link.from_node
        if node.as_pointer() in seen:
            continue
        seen.add(node.as_pointer())
        yield node
        for entry in node.inputs:
            yield from upstream_nodes(entry, seen)


def material_record(material):
    channels = {}
    if material.use_nodes:
        outputs = [n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
        for output in outputs:
            for node in upstream_nodes(output.inputs['Surface']):
                if node.type != 'BSDF_PRINCIPLED':
                    continue
                for channel in ('Base Color', 'Metallic', 'Roughness', 'Normal'):
                    channels.setdefault(channel, set()).update(
                        n.image.name for n in upstream_nodes(node.inputs[channel])
                        if n.type == 'TEX_IMAGE' and n.image is not None)
    return {'name': material.name, 'image_channels': {k: sorted(v) for k, v in channels.items()}}


def inspect(source):
    objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    meshes = [mesh_record(obj) for obj in sorted(objects, key=lambda item: item.name)]
    used = {name for mesh in meshes for name in mesh['used_materials']}
    materials = [material_record(bpy.data.materials[name]) for name in sorted(used)]
    images = [{'name': im.name, 'size': list(im.size), 'has_pixels': bool(im.has_data),
               'source': im.source, 'packed': bool(im.packed_file),
               'file_name': im.filepath.replace('\\', '/').rsplit('/', 1)[-1],
               'color_space': im.colorspace_settings.name}
              for im in bpy.data.images if im.users]
    image_by_name = {im['name']: im for im in images}
    base_color_edges = []
    for material in materials:
        names = material['image_channels'].get('Base Color', [])
        sizes = [max(image_by_name[name]['size']) for name in names if name in image_by_name
                 and image_by_name[name]['has_pixels'] and min(image_by_name[name]['size']) > 0]
        base_color_edges.append(min(sizes) if sizes and len(sizes) == len(names) else 0)
    assigned = bool(meshes) and all(mesh['unassigned_material_faces'] == 0 for mesh in meshes)
    return {
        'schema_version': 1, 'source_file': source.name, 'source_sha256': file_sha(source),
        'source_bytes': source.stat().st_size, 'blender': bpy.app.version_string,
        'totals': {key: sum(mesh[key] for mesh in meshes) for key in
                   ('vertices', 'faces', 'triangles', 'boundary_edges', 'wire_edges',
                    'edges_with_more_than_two_faces', 'nonfinite_vertices')},
        'mesh_objects': len(meshes), 'unique_meshes': len({obj.data.as_pointer() for obj in objects}),
        'meshes': meshes, 'materials': materials, 'images': images,
        'texture_evidence': {
            'all_meshes_have_uv_layers': bool(meshes) and all(mesh['uv_layers'] for mesh in meshes),
            'all_faces_have_materials': assigned,
            'all_used_materials_have_loaded_base_color_images': assigned and bool(base_color_edges)
                and all(edge > 0 for edge in base_color_edges),
            'minimum_loaded_base_color_long_edge': min(base_color_edges, default=0),
        },
        'limitations': [
            'Counts include each scene mesh instance. They do not measure identity or reconstruction fidelity.',
            'Boundary counts use imported indices without welding; UV seams can split GLB vertices.',
            'Two faces per edge alone does not establish watertightness, correct normals or print readiness.',
            'Image dimensions and UV presence do not establish native detail, UV quality or physical PBR albedo.',
            'Channel traversal supports ordinary imported Principled shaders; arbitrary node groups need manual review.',
            'Bounds are in imported scene units. Physical scale is not independently calibrated.',
        ],
    }


def render_clay(report, output, front, size, lower_crop):
    scene = bpy.context.scene
    low = Vector(tuple(min(m['world_bounds']['min'][i] for m in report['meshes']) for i in range(3)))
    high = Vector(tuple(max(m['world_bounds']['max'][i] for m in report['meshes']) for i in range(3)))
    low.z += (high.z - low.z) * lower_crop
    center, extent = (low + high) / 2, max(high - low)
    forward = Vector((0, -1 if front == 'negative-y' else 1, 0))
    clay = bpy.data.materials.new('Inspection neutral clay')
    clay.use_nodes = True
    shader = clay.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.48, .48, .48, 1)
    shader.inputs['Roughness'].default_value = .78
    scene.view_layers[0].material_override = clay
    scene.world = bpy.data.worlds.new('Inspection studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.065, .065, .065, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    for offset, strength in [((-1.8, -2.5, 2.5), 220), ((2, -1, 1), 100), ((0, 2, 2), 180)]:
        vector = Vector((offset[0], offset[1] * -forward.y, offset[2]))
        bpy.ops.object.light_add(type='AREA', location=center + vector * extent)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.size = strength * extent * extent, 1.5 * extent
        lamp.rotation_euler = (center - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = extent * 1.2
    camera.data.clip_end = max(1000, extent * 10)
    camera.data.clip_start = max(.0001, extent / 10000)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = -1
    views = [('front', forward), ('three-quarter', Vector((.7, forward.y, .05))),
             ('back', -forward)]
    renders = []
    for name, direction in views:
        camera.location = center + direction.normalized() * extent * 3
        camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
        path = output / (name + '-clay.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders.append({'file': path.name, 'sha256': file_sha(path), 'size': [size, size]})
    return {'mode': 'neutral clay material override', 'front': front,
            'lower_crop_fraction': lower_crop, 'renders': renders}


def validate(report, require_textures=False, min_base_color_edge=None):
    failures = []
    if not report['mesh_objects'] or not report['totals']['triangles']:
        failures.append('No surface mesh was imported.')
    if report['totals']['nonfinite_vertices']:
        failures.append('The mesh contains nonfinite vertices.')
    evidence = report['texture_evidence']
    if require_textures or min_base_color_edge:
        if not evidence['all_meshes_have_uv_layers']:
            failures.append('At least one mesh has no UV layer.')
        if not evidence['all_used_materials_have_loaded_base_color_images']:
            failures.append('At least one mesh/material has no loaded base-color texture.')
    if min_base_color_edge and evidence['minimum_loaded_base_color_long_edge'] < min_base_color_edge:
        failures.append('Not every used material reaches the requested base-color texture edge.')
    return {'status': 'failed' if failures else 'passed', 'failures': failures,
            'require_textures': require_textures, 'min_base_color_edge': min_base_color_edge,
            'likeness_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--render-clay', action='store_true')
    parser.add_argument('--front', choices=('negative-y', 'positive-y'), default='negative-y')
    parser.add_argument('--render-size', type=int, choices=(512, 768, 1024), default=768)
    parser.add_argument('--lower-crop', type=float, default=0,
                        help='Frame the upper part; fraction of scene height omitted, from 0 to 0.8.')
    parser.add_argument('--require-textures', action='store_true')
    parser.add_argument('--min-base-color-edge', type=int, choices=(2048, 4096, 8192))
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not 0 <= args.lower_crop <= .8:
        parser.error('--lower-crop must be between 0 and 0.8.')
    source = args.input.resolve(strict=True)
    if source.suffix.lower() not in ('.fbx', '.glb'):
        parser.error('Input must be FBX or self-contained GLB.')
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if source.suffix.lower() == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(source), use_image_search=False)
    else:
        bpy.ops.import_scene.gltf(filepath=str(source))
    report = inspect(source)
    report['validation'] = validate(report, args.require_textures, args.min_base_color_edge)
    failures = report['validation']['failures']
    report_path = args.output / 'asset-inspection.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    if args.render_clay and report['totals']['triangles'] and not report['totals']['nonfinite_vertices']:
        report['clay_review'] = render_clay(report, args.output, args.front, args.render_size, args.lower_crop)
        report_path.write_text(json.dumps(report, indent=2) + '\n')
    if file_sha(source) != report['source_sha256']:
        raise RuntimeError('Source changed during inspection.')
    print(json.dumps({'report': str(report_path), 'totals': report['totals'],
                      'validation': report['validation']}), flush=True)
    if failures:
        raise RuntimeError('; '.join(failures))


if __name__ == '__main__':
    main()
