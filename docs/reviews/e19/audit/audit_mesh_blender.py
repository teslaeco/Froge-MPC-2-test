"""blender -b --python audit_mesh_blender.py -- --input MODEL.glb --output report.json

Read-only audit of evaluated visible/renderable scene geometry. Excludes cameras,
lights, hidden-render objects. No mesh mutation, tolerance welding or auto repair.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_metrics import mesh_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-height-mm', type=float)
    parser.add_argument('--stl-units', choices=['mm','m'])
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.input.resolve()
    if source.suffix.lower() == '.blend':
        bpy.ops.wm.open_mainfile(filepath=str(source))
    elif source.suffix.lower() == '.glb':
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(source))
    elif source.suffix.lower() == '.stl':
        if not args.stl_units:raise ValueError('STL has no standard unit; provide --stl-units mm or m')
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.stl_import(filepath=str(source),use_mesh_validate=False,use_scene_unit=False)
    else:
        raise ValueError('Input must be GLB, BLEND or explicitly-unit-labelled STL')
    scale = float(bpy.context.scene.unit_settings.scale_length)
    if source.suffix.lower() == '.glb':
        scale = 1.0  # glTF positions use metres; importer converts axes only.
    elif source.suffix.lower() == '.stl':
        scale = 0.001 if args.stl_units == 'mm' else 1.0
    deps = bpy.context.evaluated_depsgraph_get()
    rows = []
    for index, original in enumerate(sorted(bpy.context.scene.objects, key=lambda obj: obj.name)):
        if original.hide_render or original.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            continue
        evaluated = original.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        if mesh is None:
            continue
        try:
            mesh.calc_loop_triangles()
            coords = np.empty((len(mesh.vertices), 3), dtype=np.float64)
            mesh.vertices.foreach_get('co', coords.ravel())
            matrix = np.asarray(evaluated.matrix_world, dtype=np.float64)
            coords = (coords @ matrix[:3, :3].T + matrix[:3, 3]) * scale * 1000.0
            triangles = np.empty((len(mesh.loop_triangles), 3), dtype=np.int64)
            mesh.loop_triangles.foreach_get('vertices', triangles.ravel())
            metrics = mesh_metrics(coords, triangles)
            metrics.update(name=original.name, object_type=original.type,
                           negative_transform_determinant=bool(np.linalg.det(matrix[:3, :3]) < 0))
            rows.append(metrics)
            print('AUDIT', len(rows), original.name, len(triangles), metrics['status'], flush=True)
        finally:
            evaluated.to_mesh_clear()
    finite = [row for row in rows if 'bounds_min_mm' in row]
    low = np.min([row['bounds_min_mm'] for row in finite], axis=0) if finite else np.zeros(3)
    high = np.max([row['bounds_max_mm'] for row in finite], axis=0) if finite else np.zeros(3)
    bad = [row['name'] for row in rows if row['status'] != 'topology_pass']
    topology = {'boundary_edges': 0, 'nonmanifold_edges_more_than_two_faces': 0,
                'inconsistent_winding_edges_two_faces': 0, 'collapsed_edges': 0,
                'components_including_unused_vertices': 0, 'unused_vertices': 0}
    for row in rows:
        for key in topology:
            topology[key] += row.get('position_welded_topology', {}).get(key, 0)
    report = {
        'schema': 'forge.production.preflight/1', 'blender': bpy.app.version_string,
        'source_name': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope': 'Evaluated scene objects, per-object exact-position welded triangle topology. No cross-object welding or Boolean union.',
        'source_units': 'metres' if source.suffix.lower() == '.glb' else (args.stl_units if source.suffix.lower()=='.stl' else 'scene_scale_length'),
        'scene_scale_length': scale, 'dimensions_mm': (high-low).tolist(),
        'expected_height_mm': args.expected_height_mm,
        'physical_scale_confirmed': args.expected_height_mm is not None and abs((high-low)[2]-args.expected_height_mm) <= 0.01,
        'mesh_objects': len(rows), 'triangles': sum(row['triangles'] for row in rows),
        'objects_failing_topology': bad,
        'totals_position_welded_per_object': topology,
        'degenerate_triangles': sum(row.get('degenerate_triangles', 0) for row in rows),
        'manufacturing_ready': False,
        'manufacturing_status': 'blocked' if bad else 'not_certified',
        'unchecked': ['self_intersections', 'cross_object_intersections', 'nested_internal_shells',
                      'minimum_wall_thickness', 'minimum_feature_diameter', 'support_orientation',
                      'base_stability', 'slicer_result', 'material_profile', 'CNC_tool_access',
                      'laser_stone_process_test', 'physical_sample'],
        'objects': rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print('AUDIT_DONE', json.dumps({key: report[key] for key in ['source_sha256', 'mesh_objects', 'triangles', 'dimensions_mm', 'manufacturing_status', 'totals_position_welded_per_object', 'degenerate_triangles']}), flush=True)

if __name__ == '__main__':
    main()
