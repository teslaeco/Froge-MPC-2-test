import unittest
import numpy as np
from mesh_metrics import mesh_metrics

V = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]], dtype=float)
F = np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])

class MeshMetricsTests(unittest.TestCase):
    def test_cube_closed_positive_volume(self):
        d=mesh_metrics(V,F)
        self.assertEqual(d['status'], 'topology_pass')
        self.assertAlmostEqual(d['signed_volume_mm3'],8)
        self.assertEqual(d['position_welded_topology']['components_including_unused_vertices'],1)
    def test_uv_seam_duplicate_vertices_are_not_holes(self):
        d=mesh_metrics(V[F].reshape(-1,3), np.arange(F.size).reshape(-1,3))
        self.assertGreater(d['raw_topology']['boundary_edges'],0)
        self.assertEqual(d['position_welded_topology']['boundary_edges'],0)
        self.assertEqual(d['status'],'topology_pass')
    def test_real_open_face_cannot_pass(self):
        d=mesh_metrics(V,F[2:])
        self.assertEqual(d['position_welded_topology']['boundary_edges'],4)
        self.assertEqual(d['status'],'topology_fail')
        self.assertIsNone(d['signed_volume_mm3'])
    def test_reversed_face_detected(self):
        f=F.copy(); f[0]=f[0][::-1]
        d=mesh_metrics(V,f)
        self.assertGreater(d['position_welded_topology']['inconsistent_winding_edges_two_faces'],0)
    def test_disconnected_solids_are_counted(self):
        d=mesh_metrics(np.vstack((V,V+[4,0,0])),np.vstack((F,F+8)))
        self.assertEqual(d['position_welded_topology']['components_including_unused_vertices'],2)
    def test_degenerate_triangle_detected(self):
        d=mesh_metrics(V,np.vstack((F,[0,0,0])))
        self.assertEqual(d['degenerate_triangles'],1)
        self.assertEqual(d['status'],'topology_fail')
    def test_nonfinite_data_blocked(self):
        v=V.copy();v[0,0]=float('nan')
        self.assertEqual(mesh_metrics(v,F)['status'],'invalid')
    def test_tiny_real_gap_is_not_tolerance_welded(self):
        v=V[F].reshape(-1,3).copy();v[0,0]+=1e-7
        d=mesh_metrics(v,np.arange(F.size).reshape(-1,3))
        self.assertEqual(d['status'],'topology_fail')
    def test_negative_index_rejected(self):
        f=F.copy();f[0,0]=-1
        with self.assertRaises(ValueError):mesh_metrics(V,f)

if __name__ == '__main__':unittest.main()
