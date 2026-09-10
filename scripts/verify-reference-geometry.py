"""Native Blender tests: reindexing passes; deformation, winding and face loss fail."""
import copy
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np

compare = runpy.run_path(str(Path(__file__).with_name('compare-reference-geometry.py')))['compare_part']
left = {'name': 'source', 'vertices': np.array([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (1., 1., 0.)]),
        'face_sizes': np.array([3, 3]), 'vertex_indices': np.array([0, 1, 2, 1, 3, 2])}
order = np.array([2, 0, 3, 1])
inverse = np.argsort(order)
right = {'name': 'reindexed', 'vertices': left['vertices'][order], 'face_sizes': np.array([3, 3]),
         'vertex_indices': inverse[left['vertex_indices']].reshape(-1, 3)[::-1].ravel()}
assert compare(left, right)['within_tolerance']
deformed = copy.deepcopy(right)
deformed['vertices'][0, 2] += .01
assert not compare(left, deformed)['within_tolerance']
reversed_face = copy.deepcopy(right)
reversed_face['vertex_indices'][:3] = reversed_face['vertex_indices'][:3][::-1]
assert not compare(left, reversed_face)['within_tolerance']
duplicate = copy.deepcopy(right)
duplicate['vertex_indices'][3:] = duplicate['vertex_indices'][:3]
assert not compare(left, duplicate)['within_tolerance']
output = Path(sys.argv[sys.argv.index('--') + 1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'blender': bpy.app.version_string, 'passed': 4,
    'checks': ['Vertex/face reordering passes.', 'A moved vertex fails.',
               'Reversed face winding fails.', 'Duplicate face replacing another face fails.']}, indent=2) + '\n')
print('REFERENCE_GEOMETRY_CHECKS_OK', flush=True)
