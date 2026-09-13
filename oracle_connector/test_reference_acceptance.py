"""Host acceptance regressions. Synthetic PNG fixtures are not likeness evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from quality_report import model_status, quality_report
from runtime.reference_reconstruction import REQUIRED_VIEWS
from test_reference_reconstruction import png_fixture, specimen


class HostAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.folder=Path(self.temp.name)
        self.payload=b'glTF'+b'host-gate-fixture'*8
        (self.folder/'model.glb').write_bytes(self.payload)
        self.sha=hashlib.sha256(self.payload).hexdigest()
        self.result={'triangles':12,'portrait_quality':{'structural_checks_passed':True,'actual':{'heads':1,'eyes':2}},
                     'reference_socket_checks':{'passed':True}}
        self.write('result.json',self.result)
        self.write('scene.json',{'subject_type':'portrait'})
        self.write('reference-photos.json',[{'sha256':specimen()['reference_sha256']}])
        self.outcome={'finished':True,'accepted':True,'model_sha256':self.sha}
        self.write('agent-outcome.json',self.outcome)
        self.write('visual-review.json',{'accepted':True,'assessment_completed':True,'issues':[]})
        self.candidate=self.folder
        bridge=types.ModuleType('blender_mcp')
        bridge.completed_outcome=lambda folder:self.outcome
        bridge.current_candidate=lambda folder:{'path':self.candidate,'result':self.result}
        self.bridge=patch.dict(sys.modules,{'blender_mcp':bridge})
        self.bridge.start()

    def tearDown(self):
        self.bridge.stop()
        self.temp.cleanup()

    def write(self,name,value,folder=None):
        ((folder or self.folder)/name).write_text(json.dumps(value),encoding='utf-8')

    def complete_evidence(self,folder=None):
        folder=folder or self.folder
        spec=specimen()
        self.write('reference-spec.json',spec,folder)
        (folder/'reference.png').write_bytes(png_fixture())
        (folder/'review').mkdir(exist_ok=True)
        for view in REQUIRED_VIEWS:
            (folder/'review'/('reference-'+view+'.png')).write_bytes(png_fixture())
        evidence={'model_sha256':self.sha,'reference_sha256':spec['reference_sha256'],
                  'reimport_verified':True,'same_camera_as_baseline':True,'critical_defects':[],
                  'views':{view:{'model_sha256':self.sha,'reference_sha256':spec['reference_sha256'],
                       'image_sha256':hashlib.sha256(png_fixture()).hexdigest(),'nonempty_verified':True}
                       for view in REQUIRED_VIEWS}}
        self.write('reference-evidence.json',evidence,folder)

    def test_agent_acceptance_cannot_promote_missing_reference_review(self):
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'draft')
        self.assertFalse(value['automaticQualityAccepted'])
        self.assertFalse(value['agent']['accepted'])
        self.assertTrue(value['agent']['reportedAccepted'])
        self.assertFalse(value['visualReview']['accepted'])
        self.assertIn('reference_reconstruction_incomplete',value['acceptanceGate']['failures'])
        self.assertEqual((self.folder/'model.glb').read_bytes(),self.payload)

    def test_real_image_hash_change_revokes_readiness(self):
        self.complete_evidence()
        self.assertEqual(model_status(self.folder,'succeeded')['modelStatus'],'reviewed')
        (self.folder/'review/reference-front.png').write_bytes(png_fixture(129,128))
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'draft')
        self.assertIn('view_missing_or_unverified:front',value['acceptanceGate']['referenceReview']['failures'])

    def test_reference_change_revokes_readiness(self):
        self.complete_evidence()
        (self.folder/'reference.png').write_bytes(png_fixture(129,128))
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'draft')
        self.assertIn('reference_hash_mismatch',value['acceptanceGate']['referenceReview']['failures'])

    def test_malformed_evidence_preserves_draft(self):
        self.complete_evidence()
        (self.folder/'reference-evidence.json').write_text('{')
        self.assertEqual(model_status(self.folder,'succeeded')['modelStatus'],'draft')
        self.assertEqual((self.folder/'model.glb').read_bytes(),self.payload)

    def test_text_only_person_does_not_require_invented_photo(self):
        (self.folder/'reference-photos.json').unlink()
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'reviewed')
        self.assertFalse(value['acceptanceGate']['referenceRequired'])
        self.assertFalse(value['acceptanceGate']['likenessVerified'])
        self.result['portrait_quality']['structural_checks_passed']=False
        self.write('result.json',self.result)
        self.assertEqual(model_status(self.folder,'succeeded')['modelStatus'],'draft')

    def test_failed_board_material_contract_blocks_agent_approval(self):
        (self.folder/'reference-photos.json').unlink()
        self.result['board_review']={'status':'needs_correction','passed':False,'failures':['material_parity'],
                                     'unverified':[],'expected_cells':64}
        self.write('result.json',self.result)
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'draft')
        self.assertIn('board_geometry_or_materials_unverified',value['acceptanceGate']['failures'])

    def test_current_candidate_sidecars_override_unrelated_root_readiness(self):
        self.complete_evidence()
        self.candidate=self.folder/'candidates/2'
        self.candidate.mkdir(parents=True)
        (self.candidate/'model.glb').write_bytes(self.payload)
        self.write('scene.json',{'subject_type':'portrait'},self.candidate)
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'draft')
        self.assertIn('reference_spec_missing',value['acceptanceGate']['referenceReview']['failures'])

    def test_unaccepted_outcome_cannot_be_promoted_by_complete_evidence(self):
        self.complete_evidence()
        self.outcome['accepted']=False
        self.assertEqual(model_status(self.folder,'succeeded')['modelStatus'],'draft')

    def test_prior_atlas_failure_is_history_not_current_validation(self):
        (self.folder/'reference-photos.json').unlink()
        failed=self.folder/'candidates/1';failed.mkdir(parents=True)
        self.write('anatomy-failure.json',{'structural_checks_passed':False,
            'expected':{'heads':1},'actual':{'heads':1},
            'violations':[{'code':'skin_atlas','object':'old-head','message':'previous candidate atlas missing'}]},failed)
        value=quality_report(self.folder,'succeeded')
        self.assertEqual(value['modelStatus'],'reviewed')
        self.assertEqual(value['validationErrors'],[])
        self.assertEqual(value['currentValidation']['modelSha256'],self.sha)
        self.assertEqual(value['failureHistory'][0]['attempt'],1)
        self.assertFalse(value['failureHistory'][0]['current'])
        self.assertIsNone(value['failureHistory'][0]['revision'])


if __name__=='__main__':
    unittest.main()
