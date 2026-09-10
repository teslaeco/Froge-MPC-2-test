import base64
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import photo_input
from runtime.reference_quality import fit_dimensions, texture_limit
from runtime.reference_match import compare, SIGNATURE


def jpeg(width, height):
    return bytes([255,216,255,192,0,11,8,height>>8,height&255,width>>8,width&255,1,1,17,0,255,218,0,2,0,255,217])


class ReferenceQualityTests(unittest.TestCase):
    def test_aspect_ratio_and_no_invented_pixels(self):
        self.assertEqual(fit_dimensions(8192,4096,4096),(4096,2048))
        self.assertEqual(fit_dimensions(1122,1402,8192),(1122,1402))
        self.assertEqual(fit_dimensions(400,8000,2048),(102,2048))
        for value in (True,'8192',8193,0,4096.0):
            with self.assertRaises(ValueError):texture_limit(value)

    def test_eight_k_admission_metadata_replay_and_limits(self):
        raw=jpeg(8192,4096)
        source={'name':'large.jpg','view':'front','textureMaxSize':8192,
                'dataUrl':'data:image/jpeg;base64,'+base64.b64encode(raw).decode()}
        photos=photo_input.validate_photos([source])
        self.assertEqual(photos[0]['bytes'],raw)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'reference-0.jpg').write_bytes(raw)
            (folder/'reference-photos.json').write_text(json.dumps(photo_input.metadata(photos)))
            self.assertEqual(photo_input.read_photos(folder),photos)
        with self.assertRaises(ValueError):photo_input.validate_photos([source]*3)
        with self.assertRaises(ValueError):photo_input.jpeg_dimensions(jpeg(8193,2))

    def test_reencoded_composition_is_tolerated_but_other_face_or_outfit_is_not(self):
        template=json.loads(SIGNATURE.read_text())
        pixels=np.asarray(template['rgb'])
        self.assertTrue(compare(pixels,template)['matched'])
        self.assertTrue(compare(np.clip(pixels+.004,0,1),template)['matched'])
        self.assertFalse(compare(pixels[:,::-1],template)['matched'])
        self.assertFalse(compare(pixels[:30],template)['matched'])
        for region in ((slice(5,15),slice(15,25)),(slice(26,40),slice(15,30))):
            changed=pixels.copy();changed[region]=[.9,.1,.8]
            self.assertFalse(compare(changed,template)['matched'])
