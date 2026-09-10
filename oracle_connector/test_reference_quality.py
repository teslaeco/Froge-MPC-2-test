import base64
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import photo_input
from runtime.reference_quality import fit_dimensions, texture_limit, material_budget, export_textures, GIB
from unittest.mock import patch, Mock
from runtime.reference_match import compare, SIGNATURE


def jpeg(width, height):
    return bytes([255,216,255,192,0,11,8,height>>8,height&255,width>>8,width&255,1,1,17,0,255,218,0,2,0,255,217])


class ReferenceQualityTests(unittest.TestCase):
    def test_complete_8k_pbr_set_uses_material_budget_not_photo_budget(self):
        sizes=[((8192,8192),(8192,8192))]+[((4096,4096),(4096,4096))]*3
        report=material_budget(sizes,8*GIB)
        self.assertEqual(report['export_pixels'],117440512)
        self.assertLess(report['estimated_peak_bytes'],8*GIB)
        with self.assertRaisesRegex(ValueError,'budzecie'):material_budget(sizes,4*GIB)
        with self.assertRaises(ValueError):material_budget(sizes*2,8*GIB)

    def test_low_memory_rejection_does_not_mutate_any_image(self):
        images=[]
        for size in [(8192,8192)]+[(4096,4096)]*3:
            image=Mock(size=size);image.get.return_value=False;images.append(image)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'reference-photos.json').write_text('[{"textureMaxSize":8192}]')
            with patch('runtime.reference_quality.export_memory_bytes',return_value=4*GIB),self.assertRaises(ValueError):
                export_textures(images,folder)
        for image in images:
            image.scale.assert_not_called();image.pack.assert_not_called()

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
