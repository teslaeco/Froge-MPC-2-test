"""Deterministic mesh preflight metrics; never certifies manufacturing readiness.

NumPy required. SciPy, if present, accelerates component counting. Exact position
welding is analysis-only and removes export seam duplicates without changing files.
"""
import numpy as np


def component_count(vertex_count, edges):
    if vertex_count == 0:
        return 0
    try:
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        graph = coo_matrix((np.ones(len(edges), dtype=np.uint8),
                           (edges[:, 0], edges[:, 1])),
                          shape=(vertex_count, vertex_count)).tocsr()
        return int(connected_components(graph, directed=False, return_labels=False))
    except ImportError:
        parent = list(range(vertex_count))
        size = [1] * vertex_count
        groups = vertex_count
        for a, b in edges:
            a, b = int(a), int(b)
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            while parent[b] != b:
                parent[b] = parent[parent[b]]
                b = parent[b]
            if a != b:
                if size[a] < size[b]:
                    a, b = b, a
                parent[b] = a
                size[a] += size[b]
                groups -= 1
        return groups


def edge_metrics(faces, vertex_count):
    edges = faces[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2)
    low, high = np.minimum(edges[:, 0], edges[:, 1]), np.maximum(edges[:, 0], edges[:, 1])
    keys = low.astype(np.uint64) * np.uint64(max(1, vertex_count)) + high
    unique, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)
    signs = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    directions = np.bincount(inverse, weights=signs, minlength=len(unique))
    pairs = np.column_stack((unique // max(1, vertex_count), unique % max(1, vertex_count))).astype(np.int64)
    return {
        'edges': int(len(unique)),
        'boundary_edges': int(np.count_nonzero(counts == 1)),
        'nonmanifold_edges_more_than_two_faces': int(np.count_nonzero(counts > 2)),
        'inconsistent_winding_edges_two_faces': int(np.count_nonzero((counts == 2) & (directions != 0))),
        'collapsed_edges': int(np.count_nonzero(low == high)),
    }, pairs


def mesh_metrics(vertices_mm, faces, area_epsilon_mm2=1e-12):
    vertices = np.asarray(vertices_mm, dtype=np.float64)
    faces = np.asarray(faces, dtype=np.int64).reshape(-1, 3)
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError('vertices must be Nx3')
    if len(faces) and (faces.min() < 0 or faces.max() >= len(vertices)):
        raise ValueError('triangle index outside vertex array')
    if not np.isfinite(vertices).all():
        return {'status': 'invalid', 'reason': 'nonfinite_coordinates', 'vertices': int(len(vertices)), 'triangles': int(len(faces))}
    if not len(vertices) or not len(faces):
        return {'status': 'invalid', 'reason': 'empty_mesh', 'vertices': int(len(vertices)), 'triangles': int(len(faces))}
    raw, _ = edge_metrics(faces, len(vertices))
    # Exact equals only: no geometric tolerance can invisibly bridge a real gap.
    welded, inverse = np.unique(vertices, axis=0, return_inverse=True)
    welded_faces = inverse[faces]
    metrics, pairs = edge_metrics(welded_faces, len(welded))
    metrics['components_including_unused_vertices'] = component_count(len(welded), pairs)
    metrics['unused_vertices'] = int(len(welded) - len(np.unique(welded_faces)))
    a, b, c = (vertices[faces[:, index]] for index in range(3))
    areas = np.linalg.norm(np.cross(b - a, c - a), axis=1) * 0.5
    # Translation to mesh-local centroid improves cancellation at large coordinates.
    origin = vertices.mean(axis=0)
    signed_volume = np.einsum('ij,ij->i', a - origin, np.cross(b - origin, c - origin)).sum() / 6.0
    closed = not any(metrics[key] for key in ['boundary_edges', 'nonmanifold_edges_more_than_two_faces', 'inconsistent_winding_edges_two_faces', 'collapsed_edges'])
    degenerate = int(np.count_nonzero(areas <= area_epsilon_mm2))
    return {
        'status': 'topology_pass' if closed and degenerate == 0 else 'topology_fail',
        'vertices': int(len(vertices)), 'triangles': int(len(faces)),
        'position_welded_vertices': int(len(welded)),
        'exact_duplicate_positions': int(len(vertices) - len(welded)),
        'raw_topology': raw, 'position_welded_topology': metrics,
        'degenerate_triangles': degenerate, 'degenerate_area_threshold_mm2': area_epsilon_mm2,
        'bounds_min_mm': vertices.min(axis=0).tolist(), 'bounds_max_mm': vertices.max(axis=0).tolist(),
        'dimensions_mm': np.ptp(vertices, axis=0).tolist(),
        'surface_area_mm2': float(areas.sum()),
        'signed_volume_mm3': float(signed_volume) if closed and not degenerate else None,
        'volume_note': 'Algebraic per-object volume only; overlaps, nesting, self intersections and union are not evaluated.',
    }
