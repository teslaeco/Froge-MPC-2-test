"""Reference isolation and UV domain checks without Blender mocks."""
import math
from types import SimpleNamespace
import unittest
from runtime import reference_surfaces as r


class ReferenceSurfaceTests(unittest.TestCase):
    def test_portrait_roll_uses_image_aspect_and_observed_eye_line(self):
        points=[[0.,0.,0.] for _ in range(478)]
        points[468]=[.53961,.23724,0.];points[473]=[.62444,.21848,0.]
        fit=SimpleNamespace(source_sha256=r.EMERALD_SHA256,
            observation={'width':1229,'height':1536,'points':points})
        pitch,roll,yaw=r.portrait_pose(fit)
        self.assertLess(roll,-.22);self.assertGreater(roll,-.26)
        fit.source_sha256='other photo'
        self.assertIsNone(r.portrait_pose(fit))

    def test_garment_projection_rejects_a_hair_width_in_place_of_body_scale(self):
        with self.assertRaises(ValueError):r.garment_uv((.08,-.07,1.25),.30,.005)
        a=r.garment_uv((0,-.07,1.25),.30,.94)
        b=r.garment_uv((.08,-.07,1.25),.30,.94)
        self.assertGreater(abs(b[0]-a[0]),.025)

    def test_guide_cannot_apply_to_an_unrelated_upload(self):
        self.assertFalse(r.has_guide(None))
        self.assertFalse(r.has_guide(SimpleNamespace(source_sha256='0'*64)))
        self.assertFalse(r.has_guide(SimpleNamespace()))
        self.assertTrue(r.has_guide(SimpleNamespace(source_sha256=r.EMERALD_SHA256)))

    def test_fan_projection_stays_above_photographed_fingers(self):
        # Both supported spread/radius extremes and interior samples, including
        # off-centre pleat spines. A hand must not be painted onto the prop.
        for radius in (.15,.23,.55):
            for spread in (1.5,2.35,2.8):
                for i in range(81):
                    a=spread*(i/80-.5)
                    for t in (.065,.31,.46,.64,.76,1.025):
                        u,v=r.fan_uv((radius*t*math.sin(a),0,radius*t*math.cos(a)),radius,spread)
                        self.assertTrue(0<u<1 and 0<v<1)
                        self.assertLessEqual((1-v)*1536,937.000001)

    def test_quad_preserves_corners_and_clamps_inferred_extension(self):
        corners=((633,1280),(870,1242),(993,934),(869,929))
        for (u,v),p in zip(((0,0),(1,0),(1,1),(0,1)),corners):
            out=r.quad_uv(u,v,corners)
            self.assertAlmostEqual(out[0]*1229,p[0])
            self.assertAlmostEqual((1-out[1])*1536,p[1])
        self.assertEqual(r.quad_uv(-1,2,corners),r.quad_uv(0,1,corners))
