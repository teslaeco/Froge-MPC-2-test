import copy
import unittest
from production_gate import production_preflight

SHA='a'*64
CLEAN={'schema':'forge.production.preflight/1','source_sha256':SHA,'mesh_objects':1,'triangles':12,
       'totals_position_welded_per_object':{'boundary_edges':0,'nonmanifold_edges_more_than_two_faces':0,'inconsistent_winding_edges_two_faces':0,'collapsed_edges':0,'components_including_unused_vertices':1,'unused_vertices':0},
       'degenerate_triangles':0,'dimensions_mm':[40.,40.,100.]}
PROFILE={'technology':'SLA','machine':'test fixture only','material':'test fixture only','profile_revision':'fixture-v1'}

class ProductionGateTests(unittest.TestCase):
    def test_topology_pass_does_not_approve_production(self):
        d=production_preflight(CLEAN,SHA,PROFILE,100)
        self.assertFalse(d['can_order_physical_product'])
        self.assertEqual(d['reasons'],['process_specific_engineering_checks_and_sample_not_verified'])
    def test_stale_report_rejected(self):
        self.assertIn('stale_or_wrong_artifact_audit',production_preflight(CLEAN,'b'*64)['reasons'])
    def test_open_mesh_requests_geometry_repair(self):
        audit=copy.deepcopy(CLEAN); audit['totals_position_welded_per_object']['boundary_edges']=4
        self.assertEqual(production_preflight(audit,SHA)['status'],'requires_geometry_repair')
    def test_claimed_ready_does_not_override_missing_checks(self):
        audit=copy.deepcopy(CLEAN);audit['manufacturing_ready']=True;audit['unchecked']=[]
        self.assertFalse(production_preflight(audit,SHA,PROFILE,100)['can_order_physical_product'])
    def test_different_scale_blocked(self):
        self.assertIn('physical_dimensions_do_not_match_order',production_preflight(CLEAN,SHA,PROFILE,200)['reasons'])
    def test_missing_measurements_blocked(self):
        self.assertIn('missing_or_invalid_topology_measurements',production_preflight({},SHA)['reasons'])
    def test_nan_scale_blocked(self):
        self.assertIn('target_height_mm_required',production_preflight(CLEAN,SHA,PROFILE,float('nan'))['reasons'])



class VisualReviewTests(unittest.TestCase):
    def test_rejected_review_requests_repair(self):
        h='a'*64
        result=production_preflight(CLEAN,h,PROFILE,100,visual_review={'source_sha256':h,'accepted':False})
        self.assertEqual(result['status'],'requires_geometry_repair')
        self.assertFalse(result['can_order_physical_product'])
    def test_stale_review_is_identified(self):
        result=production_preflight(CLEAN,'a'*64,PROFILE,100,visual_review={'source_sha256':'b'*64,'accepted':True})
        self.assertIn('stale_or_wrong_visual_review',result['reasons'])
    def test_incomplete_review_is_identified(self):
        h='a'*64
        result=production_preflight(CLEAN,h,PROFILE,100,visual_review={'source_sha256':h,'accepted':'yes'})
        self.assertIn('visual_review_incomplete',result['reasons'])
    def test_visual_approval_cannot_approve_manufacturing(self):
        h='a'*64
        result=production_preflight(CLEAN,h,PROFILE,100,visual_review={'source_sha256':h,'accepted':True})
        self.assertFalse(result['can_order_physical_product'])
        self.assertIn('process_specific_engineering_checks_and_sample_not_verified',result['reasons'])

if __name__=='__main__':unittest.main()
