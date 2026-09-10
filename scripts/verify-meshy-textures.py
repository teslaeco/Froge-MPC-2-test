"""Verify the supplied single-material Meshy FBX and its four external PNG maps.

This is benchmark tooling, not a FORGE-generated reconstruction or worker install.
blender -b -t 4 --python-exit-code 1 --python scripts/verify-meshy-textures.py -- \
  --input /path/name_texture.fbx --geometry-reference /path/name_generate.fbx --output /tmp/review
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np

audit = runpy.run_path(str(Path(__file__).with_name('inspect-reference-asset.py')))


def geometry_digest(include_uv=False):
    digest = hashlib.sha256()
    for obj in sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: o.name):
        digest.update(np.asarray(obj.matrix_world, dtype='<f8').tobytes())
        for collection, field, width, dtype in [
            (obj.data.vertices, 'co', 3, np.float32),
            (obj.data.polygons, 'loop_total', 1, np.int32),
            (obj.data.loops, 'vertex_index', 1, np.int32),
        ]:
            digest.update(np.asarray([len(collection), width], dtype='<i8').tobytes())
            digest.update(audit['values'](collection, field, width, dtype).tobytes())
        if include_uv:
            digest.update(audit['values'](obj.data.polygons, 'material_index').tobytes())
            for layer in obj.data.uv_layers:
                digest.update(layer.name.encode() + b'\0')
                digest.update(audit['values'](layer.data, 'uv', 2, np.float32).tobytes())
    return digest.hexdigest()


def import_fbx(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=False)


def embedded_images():
    result = []
    for im in bpy.data.images:
        if im.users and im.packed_file:
            data = im.packed_file.data
            result.append({'name': im.name, 'bytes': len(data), 'header_hex': data[:12].hex(),
                           'sha256': hashlib.sha256(data).hexdigest(),
                           'encoding': 'JPEG' if data.startswith(b'\xff\xd8\xff') else
                                       'PNG' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'other'})
    return result


def scene_bounds(report):
    return np.array([[min(m['world_bounds']['min'][i] for m in report['meshes']) for i in range(3)],
                     [max(m['world_bounds']['max'][i] for m in report['meshes']) for i in range(3)]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--geometry-reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--skip-renders', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.input.resolve(strict=True)
    geometry = args.geometry_reference.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {'blender': bpy.app.version_string, 'reference_only': True,
              'source_file': source.name, 'source_sha256': audit['file_sha'](source),
              'geometry_reference_file': geometry.name, 'geometry_reference_sha256': audit['file_sha'](geometry),
              'likeness_verified': False}
    report_path = output / 'texture-verification.json'

    def checkpoint():
        report_path.write_text(json.dumps(report, indent=2) + '\n')

    import_fbx(geometry)
    report['geometry_reference_digest'] = geometry_digest()
    import_fbx(source)
    report['textured_fbx_geometry_digest'] = geometry_digest()
    report['indexed_geometry_bytes_identical'] = report['geometry_reference_digest'] == report['textured_fbx_geometry_digest']
    report['geometry_comparison_note'] = 'Raw indexed-coordinate hashes; use compare-reference-geometry.py to distinguish numeric rounding from a surface change.'
    report['native_fbx'] = audit['inspect'](source)
    report['native_embedded_images'] = embedded_images()
    report['native_8k_validation'] = audit['validate'](report['native_fbx'], min_base_color_edge=8192)
    checkpoint()
    if report['native_8k_validation']['status'] != 'passed':
        raise RuntimeError('Native FBX did not pass 8K base-color validation; inspect the saved report.')
    if report['native_fbx']['mesh_objects'] != 1 or len(report['native_fbx']['materials']) != 1:
        raise RuntimeError('This fixture verifier requires one mesh and one material.')

    mat = bpy.data.materials[report['native_fbx']['materials'][0]['name']]
    shaders = [node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED']
    if len(shaders) != 1:
        raise RuntimeError('Expected one imported Principled shader.')
    shader = shaders[0]
    before = geometry_digest(include_uv=True)
    maps = [('Base Color', '', 'sRGB', 8192), ('Metallic', '_metallic', 'Non-Color', 4096),
            ('Roughness', '_roughness', 'Non-Color', 4096), ('Normal', '_normal', 'Non-Color', 4096)]
    report['external_png_maps'] = []
    for channel, suffix, color_space, edge in maps:
        path = source.with_name(source.stem + suffix + '.png')
        path.resolve(strict=True)
        nodes = [node for node in audit['upstream_nodes'](shader.inputs[channel]) if node.type == 'TEX_IMAGE']
        if len(nodes) != 1:
            raise RuntimeError('Expected one connected image for ' + channel)
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = color_space
        if list(image.size) != [edge, edge]:
            raise RuntimeError('Unexpected source map dimensions: ' + path.name)
        image.pack()
        nodes[0].image = image
        report['external_png_maps'].append({'channel': channel, 'file': path.name,
            'sha256': audit['file_sha'](path), 'size': list(image.size), 'color_space': color_space})
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    report['geometry_uv_material_indices_unchanged_by_png_binding'] = geometry_digest(include_uv=True) == before
    if not report['geometry_uv_material_indices_unchanged_by_png_binding']:
        raise RuntimeError('PNG binding changed geometry, UVs or material assignments.')
    report['png_bound_geometry_digest'] = before
    pixels = sum(m['size'][0] * m['size'][1] for m in report['external_png_maps'])
    policy = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'oracle_connector/runtime/reference_quality.py'))
    pixel_budget = policy['MAX_TOTAL_PIXELS']
    report['memory'] = {'source_map_pixels': pixels, 'rgba32f_bytes_for_maps_only': pixels * 16,
        'current_forge_export_pixel_budget': pixel_budget,
        'fits_current_forge_export_budget': pixels <= pixel_budget,
        'note': 'Image estimate only; mesh, encoder, renderer and duplicated buffers require additional memory.'}
    checkpoint()

    glb = output / 'meshy-pbr-reference.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', export_image_format='AUTO',
        export_animations=False, export_cameras=False, export_lights=False)
    report['export_geometry_uv_material_indices_unchanged'] = geometry_digest(include_uv=True) == before
    report['glb_file'] = glb.name
    report['glb_sha256'] = audit['file_sha'](glb)
    report['glb_bytes'] = glb.stat().st_size
    checkpoint()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    report['glb_reimport'] = audit['inspect'](glb)
    report['reimport_8k_validation'] = audit['validate'](report['glb_reimport'], min_base_color_edge=8192)
    report['reimport_preserves_triangle_count'] = report['glb_reimport']['totals']['triangles'] == report['native_fbx']['totals']['triangles']
    report['reimport_bounds_max_abs_difference'] = float(np.abs(scene_bounds(report['native_fbx']) - scene_bounds(report['glb_reimport'])).max())
    report['reimport_embedded_images'] = embedded_images()
    png_hashes = {m['channel']: m['sha256'] for m in report['external_png_maps']}
    embedded_hashes = {im['sha256'] for im in report['reimport_embedded_images']}
    report['base_color_png_bytes_preserved'] = png_hashes['Base Color'] in embedded_hashes
    report['normal_png_bytes_preserved'] = png_hashes['Normal'] in embedded_hashes
    checkpoint()
    if (report['reimport_8k_validation']['status'] != 'passed'
        or not report['export_geometry_uv_material_indices_unchanged']
        or not report['reimport_preserves_triangle_count']
        or report['reimport_bounds_max_abs_difference'] > 1e-5
        or not report['base_color_png_bytes_preserved'] or not report['normal_png_bytes_preserved']):
        raise RuntimeError('Export/reimport fidelity check failed; inspect the report.')
    if not args.skip_renders:
        report['material_review'] = audit['render_clay'](report['glb_reimport'], output, 'negative-y', 768, 0, use_materials=True)
    report['technical_checks_passed'] = True
    report['note'] = 'Reference geometry with supplied PNG materials, reimported from GLB. Not FORGE-generated output.'
    checkpoint()
    print('MESHY_TEXTURE_REFERENCE_VERIFIED', flush=True)


if __name__ == '__main__':
    main()
