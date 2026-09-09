"""Production numerical meshes and contract tests; these do not mock Blender."""
from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path
import unittest
from runtime import couture_geometry as g
from runtime.scene_contract import parse_scene,validate_scene


class CoutureGeometryTests(unittest.TestCase):
    def check_solid(self,mesh):
        vertices,faces=mesh[:2]
        self.assertTrue(all(math.isfinite(c) for v in vertices for c in v))
        edges=Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
        self.assertEqual(set(edges.values()),{2},'Open or non-manifold seam')
        directed=Counter((a,b) for f in faces for a,b in zip(f,f[1:]+f[:1]))
        self.assertTrue(all(n==directed[(b,a)] for (a,b),n in directed.items()),'Inconsistent face winding')
        volume=0
        for face in faces:
            a=vertices[face[0]]
            for i in range(1,len(face)-1):
                b,c=vertices[face[i]],vertices[face[i+1]]
                cross=[b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3] for k in range(3)]
                volume+=sum(a[k]*cross[k] for k in range(3))/6
        self.assertGreater(volume,0,'Inside-out shell')
        return vertices,faces

    def test_dress_is_fitted_closed_shell_and_keeps_real_thickness(self):
        for offset,thickness in ((.004,.002),(.001,.001),(.018,.006)):
            vertices,_=self.check_solid(g.gown(offset=offset,thickness=thickness))
            half=len(vertices)//2
            self.assertTrue(all(abs(math.dist(a,b)-thickness)<1e-9 for a,b in zip(vertices[:half],vertices[half:])))
            rx,ry,_=g.profile(1.10)
            self.assertLess(rx,.12);self.assertLess(ry,.08)
        with self.assertRaises(ValueError):g.gown(thickness=.03)

    def test_fan_and_each_rotor_are_solid_at_min_and_max_counts(self):
        for panels in (8,12,18):self.check_solid(g.fan(panels=panels))
        for blades in (3,5,16):self.check_solid(g.rotor(blades=blades))

    def test_rotor_centres_stay_on_specified_arc(self):
        positions=g.radial_positions(14,.33,-1.1,2.2,(.2,-.4,1.))
        self.assertEqual(len(positions),14)
        for x,y,z in positions:
            self.assertAlmostEqual(math.hypot(x-.2,z-1),.33)
            self.assertEqual(y,-.4)

    def test_reference_contract_preserves_anatomy_and_rejects_invalid_clearance(self):
        path=Path(__file__).parent/'examples/couture-fan-v19.scene.json'
        scene=parse_scene(path.read_text(),'Kobieta w sukni z wachlarzem')
        self.assertEqual(scene['parts'][0]['kind'],'reference_character')
        self.assertEqual(scene['parts'][0]['fan']['rotors'],14)
        for change in ({'garment_offset':.002,'garment_thickness':.006},{'crystal_material':'missing'}):
            bad=deepcopy(scene);bad['parts'][0].update(change)
            with self.assertRaises(ValueError):validate_scene(bad)
        bad=deepcopy(scene);bad['parts'][0]['face']['nose_width']=5
        with self.assertRaises(ValueError):validate_scene(bad)

    def test_three_people_keep_existing_anatomy_budget_and_four_are_rejected(self):
        scene=parse_scene((Path(__file__).parent/'examples/couture-fan-v19.scene.json').read_text())
        for i in (1,2):
            person=deepcopy(scene['parts'][0]);person['name']+='-'+str(i);person['center'][0]=i*.8;scene['parts'].append(person)
        validate_scene(scene)
        person=deepcopy(scene['parts'][0]);person['name']='fourth';scene['parts'].append(person)
        with self.assertRaises(ValueError):validate_scene(scene)


if __name__=='__main__':unittest.main()
