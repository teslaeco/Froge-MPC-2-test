import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
import face_measurement
import photo_input
from photo_face import FaceFit, TEMPLATE, neutral_points, load_fit, reviewed_observation
from photo_face_color import project


class MeasuredPhotoFaceTest(unittest.TestCase):
    def test_registered_measurement_is_explicit_and_cannot_cross_compositions(self):
        digest='a'*64
        self.assertIsNone(reviewed_observation({'matched':False},1122,1402,digest))
        self.assertIsNone(reviewed_observation({'matched':True},1200,1402,digest))
        result=reviewed_observation({'matched':True},1122,1402,digest)
        self.assertEqual((result['width'],result['height'],result['imageSha256']),(1122,1402,digest))
        self.assertEqual(len(result['points']),478)
        self.assertGreater(FaceFit(result).report['anchor_rms_before_mm'],.1)

    def setUp(self):
        self.observation=json.loads(TEMPLATE.read_text())['observation']

    def test_measurements_are_bound_to_exact_image_and_dimensions(self):
        o=self.observation
        self.assertEqual(face_measurement.validate(o,o['width'],o['height'],o['imageSha256']),o)
        for width,digest in [(o['width']+1,o['imageSha256']),(o['width'],'0'*64)]:
            with self.assertRaises(ValueError):face_measurement.validate(o,width,o['height'],digest)
        bad=copy.deepcopy(o);bad['points'][1][0]=float('nan')
        with self.assertRaises(ValueError):face_measurement.validate(bad,o['width'],o['height'],o['imageSha256'])

    def test_template_replays_without_deforming_neck_or_face(self):
        fit=FaceFit(self.observation)
        points=np.array([[-.03,-.12,1.68],[.04,-.12,1.62],[0,0,1.75],[0,-.02,1.50]])
        np.testing.assert_allclose(fit.warp(points),points,atol=1e-12)

    def test_saved_photo_retry_preserves_measurements_and_rejects_stale_image(self):
        import base64
        image=bytes([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
        digest=hashlib.sha256(image).hexdigest()
        measurement={'revision':1,'width':1,'height':1,'imageSha256':digest,'points':[[.5,.5,0]]*478}
        photos=photo_input.validate_photos([{'name':'face.jpg','view':'front','dataUrl':'data:image/jpeg;base64,'+base64.b64encode(image).decode(),'faceLandmarks':measurement}])
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);(folder/'reference-0.jpg').write_bytes(image)
            (folder/'reference-photos.json').write_text(json.dumps(photo_input.metadata(photos)))
            self.assertEqual(photo_input.read_photos(folder)[0]['faceLandmarks'],measurement)
            (folder/'reference-0.jpg').write_bytes(image+b'x')
            with self.assertRaises(ValueError):photo_input.read_photos(folder)

    def test_changed_landmarks_move_actual_points_with_bounded_residual(self):
        measured=copy.deepcopy(self.observation)
        for i,p in enumerate(measured['points']):
            if i not in (33,133,362,263):
                p[0]=.5+(p[0]-.5)*1.08
        fit=FaceFit(measured)
        points=np.array([[-.055,-.12,1.63],[.055,-.12,1.63],[0,0,1.75],[0,-.02,1.50]])
        moved=fit.warp(points)
        self.assertGreater(np.linalg.norm(moved[:2]-points[:2]),.0001)
        self.assertLessEqual(np.linalg.norm(moved-points,axis=1).max(),.020001)
        np.testing.assert_array_equal(moved[2:],points[2:])

    def test_degenerate_eye_geometry_is_rejected(self):
        bad=copy.deepcopy(self.observation);bad['points']=[[0,0,0]]*478
        with self.assertRaises(ValueError):neutral_points(bad)

    def test_authored_reference_depth_is_isolated_and_preserves_planar_fit(self):
        from reference_surfaces import EMERALD_SHA256
        fit=FaceFit(self.observation)
        points=np.array([[.045,-.12,1.651],[0,-.13,1.646],[0,-.12,1.618],
                         [0,-.12,1.606],[.033,-.11,1.684],[0,-.04,1.53]])
        baseline=fit.warp(points)
        fit.source_sha256=EMERALD_SHA256
        changed=fit.warp(points)
        np.testing.assert_array_equal(changed[:,[0,2]],baseline[:,[0,2]])
        self.assertGreater(np.linalg.norm(changed[:4]-baseline[:4]),.0005)
        self.assertLessEqual(np.abs(changed-baseline).max(),.0018)
        np.testing.assert_array_equal(changed[4:],baseline[4:])
        fit.source_sha256='unrelated photo'
        np.testing.assert_array_equal(fit.warp(points),baseline)

    def test_photo_projection_never_extrapolates_background_past_measured_face(self):
        anchors=np.array([[0.,0.],[1.,0.],[0.,1.]])
        uv,valid=project(anchors,anchors,np.array([[0,1,2]]),np.array([[.2,.3],[1.2,.3]]))
        np.testing.assert_array_equal(valid,[True,False])
        np.testing.assert_allclose(uv[0],[.2,.3])

    def test_fresh_install_and_update_include_every_worker_dependency(self):
        import zipfile
        from apply_update import FILES
        for name in ('froge-oracle-connector.zip','froge-oracle-update.zip'):
            with zipfile.ZipFile(ROOT.parent/'public/downloads'/name) as archive:
                for file in FILES:
                    self.assertEqual(archive.read(file),(ROOT/file).read_bytes(),name+': '+file)

    def test_group_and_different_subjects_are_not_blended(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            photo={'view':'front','faceLandmarks':self.observation}
            (folder/'reference-photos.json').write_text(json.dumps([photo]))
            person={'kind':'reference_character','name':'first'}
            fit,report=load_fit(folder,[person,{**person,'name':'second'}])
            self.assertIsNone(fit);self.assertEqual(report['reason'],'one_person_required')
            (folder/'reference-photos.json').write_text(json.dumps([{**photo,'subject':'Anna'},{**photo,'subject':'Ewa'}]))
            fit,report=load_fit(folder,[person])
            self.assertIsNone(fit);self.assertEqual(report['reason'],'ambiguous_subject_labels')


if __name__=='__main__':unittest.main()
