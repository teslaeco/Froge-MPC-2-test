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
    def test_reconstructed_cape_wraps_back_and_stays_outside_the_gown(self):
        for hem,width in ((.22,.94),(.30,1.),(.45,1.)):
            for side in (False,True):
                vertices,faces=g.cape_surface(hem,width,side,offset=.018)
                self.assertTrue(all(math.isfinite(c) for p in vertices for c in p))
                # Outer cloth must clear the actual gown even at fold valleys.
                self.assertGreater(min(g.envelope_ratio(v,hem,width,.018) for v in vertices),1.)
                for face in faces:
                    a,b,c=(vertices[i] for i in face[:3])
                    ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
                    area=sum((ab[(i+1)%3]*ac[(i+2)%3]-ab[(i+2)%3]*ac[(i+1)%3])**2 for i in range(3))
                    self.assertGreater(area,1e-16)
            left=g.cape_point(.5,0,hem,width);middle=g.cape_point(.5,.5,hem,width)
            self.assertGreater(middle[1]-left[1],.08,'Back must curve around the torso')
            self.assertGreater(g.cape_point(1,0,hem,width)[2]-g.cape_point(1,.5,hem,width)[2],.07)

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

    def test_cut_jewels_preserve_the_pointed_outline_and_closed_depth(self):
        for outline in ([(-.013,-.020),(.013,-.020),(0,.029)],
                        [(-.043,-.010),(.018,.052),(.033,.050),(-.006,-.012)]):
            vertices,faces=self.check_solid(g.cut_jewel(outline,.008))
            self.assertEqual([(x,z) for x,y,z in vertices[:len(outline)]],outline)
            self.assertAlmostEqual(max(y for x,y,z in vertices)-min(y for x,y,z in vertices),.0116)

    def test_reference_fixture_matches_ten_visible_turbines_and_relative_size(self):
        scene=parse_scene((Path(__file__).parent/'examples/couture-fan-v20.scene.json').read_text())
        fan=scene['parts'][0]['fan']
        self.assertEqual((fan['panels'],fan['rotors']),(10,10))
        self.assertLess(2*fan['radius']*math.sin(fan['spread']/2),.53)

    def test_rotor_centres_stay_on_specified_arc(self):
        positions=g.radial_positions(14,.33,-1.1,2.2,(.2,-.4,1.))
        self.assertEqual(len(positions),14)
        for x,y,z in positions:
            self.assertAlmostEqual(math.hypot(x-.2,z-1),.33)
            self.assertEqual(y,-.4)

    def test_turbine_frame_is_closed_but_has_no_face_across_its_opening(self):
        for inner,outer in ((.01,.014),(.023,.028)):
            vertices,faces=self.check_solid(g.turbine_frame(inner,outer))
            for face in faces:
                # A cap across the central aperture would have a centroid
                # inside the inscribed hole radius, unlike a real annular rim.
                x=sum(vertices[i][0] for i in face)/len(face)
                z=sum(vertices[i][2] for i in face)/len(face)
                self.assertGreaterEqual(math.hypot(x,z),inner*math.cos(math.pi/6)-1e-9)

    def test_crystal_surround_fills_whole_sector_except_hexagonal_window(self):
        # A missing wedge may pass a manifold test. Its projected area must
        # equal the entire outer silhouette minus exactly one open hexagon.
        for radius in (.20,.28,.50):
            for count in (4,6,10,14,18):
                for spread in (1.5,2.35,2.6):
                    opening=g.fan_rotor_radius(radius,spread,count)*1.12
                    for i in range(count):
                        angle=-spread/2+spread*(i+.5)/count;half=spread/(2*count)
                        vertices,faces=self.check_solid(g.window_surround(radius,angle,half,opening))
                        front=len(vertices)//2;area=0.
                        for face in faces:
                            if not all(j<front for j in face):continue
                            a,b,c=[vertices[j] for j in face]
                            area+=abs((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0]))/2
                        outer=g.window_outline(radius,angle,half)
                        outline_area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(outer,outer[1:]+outer[:1])))/2
                        self.assertAlmostEqual(area,outline_area-3*math.sqrt(3)*opening**2/2,places=10)

    def test_seam_centres_and_segment_interiors_clear_the_gown(self):
        # A pipe following only endpoints can sink inside a curved garment.
        # Check every segment midpoint as well as its sampled surface points.
        for hem,width,offset in ((.22,.94,.001),(.30,1.,.004),(.45,1.,.018)):
            for path in g.garment_seams(hem,width,offset):
                samples=path+[tuple((a[k]+b[k])*.5 for k in range(3)) for a,b in zip(path,path[1:])]
                for point in samples:
                    self.assertTrue(all(math.isfinite(c) for c in point))
                    self.assertGreater(g.envelope_ratio(point,hem,width,offset+.00062),1.)

    def test_hidden_anatomy_stays_inside_at_all_supported_fits(self):
        # Includes the thigh footprint which visibly pierced v19, plus the
        # full supported hem/fit/clearance boundary rather than just defaults.
        for hem in (.22,.30,.45):
            for width in (.94,1.):
                for offset,thickness in ((.001,.001),(.004,.002),(.018,.006)):
                    for z in (.10,.35,.53,.65,.86,.94,1.10,1.30,1.44):
                        for i in range(48):
                            a=i*math.tau/48
                            point=(.097+.073*math.cos(a),.079*math.sin(a),z)
                            fixed=g.contain_under_gown(point,hem,width,offset,thickness)
                            self.assertLessEqual(g.envelope_ratio(fixed,hem,width,offset-thickness),1.)
        self.assertEqual(g.contain_under_gown((.02,.04,1.6)),(.02,.04,1.6))

    def test_inlay_interiors_do_not_cut_through_gown(self):
        # Checking only the panel corners is exactly the old false-positive.
        # Sample triangle interiors and edges against the production surface.
        for hem,width in ((.22,.94),(.30,1.),(.45,1.)):
            vertices,faces,slots=g.garment_inlays(hem,width)
            self.assertEqual(set(slots),{0,1})
            for face in faces:
                points=[vertices[i] for i in face]
                for weights in ((1/3,1/3,1/3),(.5,.5,0),(0,.5,.5),(.5,0,.5)):
                    sample=tuple(sum(p[k]*w for p,w in zip(points,weights)) for k in range(3))
                    self.assertGreater(g.envelope_ratio(sample,hem,width,.004),1.)

    def test_shoulder_plates_are_thin_closed_shards_with_metal_only_on_edges(self):
        for side in (-1,1):
            vertices,faces,slots=g.shoulder_plate(side)
            self.check_solid((vertices,faces))
            self.assertEqual(slots[:4],[0]*4)
            self.assertTrue(all(slot==1 for slot in slots[4:]))
            self.assertLessEqual(max(x for x,_,_ in vertices)-min(x for x,_,_ in vertices),.181)
            self.assertLessEqual(max(z for _,_,z in vertices)-min(z for _,_,z in vertices),.10)
            self.assertGreater(max(y for _,y,_ in vertices)-min(y for _,y,_ in vertices),.07)

    def test_swept_hair_lock_taper_is_thin_symmetric_and_bounded(self):
        radii=g.hair_lock_radii(27)
        self.assertEqual(len(radii),27)
        self.assertAlmostEqual(radii[0],.00022)
        self.assertAlmostEqual(radii[0],radii[-1])
        self.assertAlmostEqual(radii[13],.00115)
        self.assertTrue(all(.0002<radius<.0012 for radius in radii))
        with self.assertRaises(ValueError):g.hair_lock_radii(3)

    def test_fan_uses_jewels_and_cloth_not_silver_panel_fill(self):
        self.assertEqual(set(g.fan()[2]),{0,1})

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
