"""Compare indexed FBX surfaces in world space, excluding intentional UV/material changes.

blender -b --python-exit-code 1 --python scripts/compare-reference-geometry.py -- \
  --before /path/geometry.fbx --after /path/textured.fbx --output /tmp/comparison.json
"""
import argparse
import json
from pathlib import Path
import runpy
import sys

import bpy
from mathutils.kdtree import KDTree
import numpy as np

audit = runpy.run_path(str(Path(__file__).with_name('inspect-reference-asset.py')))


def snapshot(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=False)
    result = []
    for obj in sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: o.name):
        vertices = audit['values'](obj.data.vertices, 'co', 3, np.float32).reshape(-1, 3).astype(np.float64)
        transform = np.asarray(obj.matrix_world, dtype=np.float64)
        result.append({'name': obj.name, 'vertices': vertices @ transform[:3, :3].T + transform[:3, 3],
            'face_sizes': audit['values'](obj.data.polygons, 'loop_total'),
            'vertex_indices': audit['values'](obj.data.loops, 'vertex_index')})
    return result


def normalized_triangles(indices):
    triangles = indices.reshape(-1, 3)
    # Cyclic rotation preserves winding, unlike sorting each triangle's vertices.
    start = triangles.argmin(axis=1)
    triangles = np.take_along_axis(triangles, (start[:, None] + np.arange(3)) % 3, axis=1)
    order = np.lexsort((triangles[:, 2], triangles[:, 1], triangles[:, 0]))
    return triangles[order]


def compare_part(left, right, tolerance=1e-6):
    same_count = left['vertices'].shape == right['vertices'].shape
    same_topology = np.array_equal(left['face_sizes'], right['face_sizes']) and np.array_equal(left['vertex_indices'], right['vertex_indices'])
    delta = float(np.max(np.abs(left['vertices'] - right['vertices']))) if same_count and left['vertices'].size else None
    result = {'before_object': left['name'], 'after_object': right['name'],
        'same_vertex_count': same_count, 'same_indexed_connectivity': same_topology,
        'max_abs_coordinate_difference_at_same_index': delta,
        'within_tolerance': same_topology and delta is not None and delta <= tolerance}
    if result['within_tolerance']:
        result['correspondence'] = 'identical indexing'
        return result
    if not same_count or not left['vertices'].size or not (np.all(left['face_sizes'] == 3) and np.all(right['face_sizes'] == 3)):
        result['correspondence'] = 'not established; reindex matching requires equal vertex counts and triangles'
        return result
    print('Matching reindexed surface: canonical vertices', flush=True)
    unique, original_ids = np.unique(left['vertices'], axis=0, return_inverse=True)
    tree = KDTree(len(unique))
    # Lexicographic insertion is pathological for Blender's tree balancing on
    # dense surfaces. Shuffle insertion only; preserve the canonical vertex IDs.
    for index in np.random.default_rng(0).permutation(len(unique)):
        tree.insert(unique[index], int(index))
    print('Matching reindexed surface: balance tree', flush=True)
    tree.balance()
    print('Matching reindexed surface: find correspondence', flush=True)
    remapped = np.empty(len(right['vertices']), dtype=np.int32)
    max_distance = 0.0
    for index, point in enumerate(right['vertices']):
        _, match, distance = tree.find(point)
        remapped[index] = match
        max_distance = max(max_distance, distance)
    print('Matching reindexed surface: compare triangle multisets', flush=True)
    before_faces = normalized_triangles(original_ids[left['vertex_indices']])
    after_faces = normalized_triangles(remapped[right['vertex_indices']])
    same_faces = np.array_equal(before_faces, after_faces)
    result.update(correspondence='nearest source vertices; triangle multiset and winding checked',
        max_nearest_vertex_distance=max_distance, triangles_and_winding_match_after_reindex=same_faces,
        within_tolerance=max_distance <= tolerance and same_faces)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    before, after = args.before.resolve(strict=True), args.after.resolve(strict=True)
    a, b = snapshot(before), snapshot(after)
    parts = []
    for left, right in zip(a, b):
        parts.append(compare_part(left, right))
    report = {'blender': bpy.app.version_string, 'before_file': before.name, 'after_file': after.name,
        'before_sha256': audit['file_sha'](before), 'after_sha256': audit['file_sha'](after),
        'before_mesh_count': len(a), 'after_mesh_count': len(b), 'parts': parts,
        'coordinate_tolerance_scene_units': 1e-6,
        'same_surface_within_tolerance': bool(parts) and len(a) == len(b) and all(p['within_tolerance'] for p in parts),
        'note': 'Reindexed triangular surfaces are matched by nearest source vertices and triangle multisets with winding. UVs/materials are intentionally excluded. Not a likeness score or proof of byte-identical coordinates.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
