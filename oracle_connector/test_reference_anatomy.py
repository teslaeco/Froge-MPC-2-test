"""Reference semantics regression, including mirrored hybrid faces."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
from scene_contract import validate_scene
from photo_face import load_fit


class ReferenceAnatomyTests(unittest.TestCase):
    def setUp(self):
        self.scene=json.loads((ROOT/'examples/portrait-floor-components.scene.json').read_text())

    def test_old_portraits_keep_both_eyes(self):
        result=validate_scene(self.scene)
        self.assertEqual(result['parts'][0]['eye_states'],
                         {'left':'present','right':'present','evidence':''})

    def test_deliberate_socket_is_explicit_sided_and_bounded(self):
        for side in ('left','right'):
            scene=deepcopy(self.scene)
            state={'left':'present','right':'present','evidence':'Original reference shows an empty skeletal orbit.'}
            state[side]='empty_socket';scene['parts'][0]['eye_states']=state
            self.assertEqual(validate_scene(scene)['parts'][0]['eye_states'],state)
        for bad in ('missing','hidden',False):
            scene=deepcopy(self.scene)
            scene['parts'][0]['eye_states']={'left':bad,'right':'present','evidence':'Original reference shows an empty skeletal orbit.'}
            with self.assertRaises(ValueError):validate_scene(scene)

    def test_missing_or_blank_evidence_cannot_lower_eye_requirement(self):
        for evidence in ('',' '*40,'oops'):
            scene=deepcopy(self.scene)
            scene['parts'][0]['eye_states']={'left':'empty_socket','right':'present','evidence':evidence}
            with self.assertRaisesRegex(ValueError,'opis.*celowej anatomii'):validate_scene(scene)

    def test_human_landmarks_never_warp_declared_skeletal_face(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            # Deliberately unusable human landmarks: the hybrid path must not
            # try fitting these. Original photo/projection is handled separately.
            (folder/'reference-photos.json').write_text(json.dumps([
                {'view':'front','faceLandmarks':{'points':[]}}]))
            head=self.scene['parts'][0]
            head['eye_states']={'left':'empty_socket','right':'present','evidence':'Visible skeletal half on viewer right.'}
            fit,report=load_fit(folder,[head])
            self.assertIsNone(fit)
            self.assertEqual(report['reason'],'nonhuman_anatomy_requires_reference_sculpt')
            self.assertTrue(report['human_landmarks_ignored'])
            self.assertFalse(report['applied'])


if __name__=='__main__':unittest.main()
