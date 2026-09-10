"""Photo landmark residual fitting of the existing closed anatomical mesh.

478 measured landmarks are pose-normalized against a rendered neutral template.
Only a regularized, bounded residual changes the mesh. Hidden depth, symmetry and
back-of-head anatomy remain estimates; this is not an identity scan.
No network, ML dependency or model-provided executable code runs in Blender.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

TEMPLATE = Path(__file__).resolve().parent / 'assets/face-template-feminine.json'


def neutral_points(observation):
    p = np.asarray(observation['points'], dtype=float)
    if p.shape != (478, 3) or not np.isfinite(p).all():
        raise ValueError('Nieprawidlowe pomiary twarzy.')
    w, h = observation['width'], observation['height']
    p = p * [w, -h, -w]
    # Work in right/up/front coordinates until the final axis conversion.
    left = p[[33, 133]].mean(axis=0)
    right = p[[362, 263]].mean(axis=0)
    horizontal = right-left
    distance = np.linalg.norm(horizontal)
    if distance < 12:
        raise ValueError('Twarz jest za mala do dopasowania geometrii.')
    horizontal /= distance
    up = p[10]-p[152]
    up -= horizontal*np.dot(up, horizontal)
    if np.linalg.norm(up) < 12:
        raise ValueError('Nie mozna okreslic orientacji twarzy.')
    up /= np.linalg.norm(up)
    front = np.cross(horizontal, up)
    local = (p-(left+right)/2) @ np.array([horizontal, up, front]).T
    local *= .0647/distance
    return local[:, [0, 2, 1]] * [1, -1, 1]


def smooth(a, b, values):
    t = np.clip((values-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


class FaceFit:
    def __init__(self, observation):
        template = json.loads(TEMPLATE.read_text())
        baseline = neutral_points(template['observation'])
        target = neutral_points(observation)
        mirror = np.asarray(template['mirror'])
        # The hidden cheek is not independently observed in a three-quarter
        # photograph. Average paired points instead of copying perspective skew.
        for points in (baseline, target):
            points[:468] = (points[:468]+points[mirror]*[-1, 1, 1])*.5
        ids = np.asarray(template['indices'])
        self.anchors = np.asarray(template['anchors_xz'])
        residual = (target[ids]-baseline[ids])*.85
        # Single-image depth is less reliable than the visible feature layout.
        residual[:, 1] *= .55
        lengths = np.linalg.norm(residual, axis=1)
        residual *= np.minimum(1, .016/np.maximum(lengths, 1e-9))[:, None]
        self.radius = .027
        self.strength = 1.
        self.observation = observation
        self.template = template
        k = self.kernel(self.anchors, self.anchors)
        self.weights = np.linalg.solve(k + np.eye(len(k))*.012, residual)
        fitted = k @ self.weights
        self.report = {
            'revision': 1, 'method': 'measured-landmark-residual',
            'detected_landmarks': len(target), 'fitted_controls': len(ids),
            'anchor_rms_before_mm': float(np.sqrt(np.mean(residual**2))*1000),
            'anchor_rms_after_mm': float(np.sqrt(np.mean((fitted-residual)**2))*1000),
            'single_view_depth_estimated': True, 'hidden_side_symmetrized': True,
            'likeness_verified': False,
        }

    def kernel(self, a, b):
        return np.exp(-np.sum((a[:, None]-b[None, :])**2, axis=2)/(2*self.radius**2))

    def reference_depth(self, points):
        """Bounded authored tissue depth; preserve fitted horizontal/up axes.

        One photograph cannot measure these depths. This reference-only
        refinement separates cheek crest, nasal tip and the two lip rolls;
        it neither replaces the mesh nor refits the measured anchor system.
        """
        from reference_surfaces import has_guide
        if not has_guide(self):return np.zeros(len(points))
        x,y,z=np.asarray(points,dtype=float).T
        def bell(value,centre,radius):
            return np.exp(-.5*((value-centre)/radius)**2)
        cheek=bell(np.abs(x),.045,.016)*bell(z,1.651,.008)
        hollow=bell(np.abs(x),.048,.016)*bell(z,1.629,.009)
        tip=bell(x,0,.009)*bell(z,1.646,.005)
        alar=bell(np.abs(x),.012,.004)*bell(z,1.640,.004)
        mouth=1-smooth(.017,.025,np.abs(x))
        upper=bell(z,1.618,.0028)*mouth
        lower=bell(z,1.606,.0032)*mouth
        depth=-.0012*cheek+.00055*hollow-.00055*tip-.00035*alar-.00070*upper-.0010*lower
        # Eyes, hair, nose bridge, neck and unseen back retain their fit.
        region=(1-smooth(-.085,-.050,y))*smooth(1.588,1.600,z)*(1-smooth(1.660,1.671,z))
        return np.clip(depth,-.0018,.0008)*region

    def warp(self, points):
        points = np.asarray(points, dtype=float)
        delta = np.empty_like(points)
        for i in range(0, len(points), 2048):
            delta[i:i+2048] = self.kernel(points[i:i+2048, [0, 2]], self.anchors) @ self.weights
        mask = (1-smooth(-.060, -.015, points[:, 1]))
        mask *= smooth(1.525, 1.560, points[:, 2])*(1-smooth(1.710, 1.755, points[:, 2]))
        delta *= mask[:, None]
        delta[:,1]+=self.reference_depth(points)
        lengths = np.linalg.norm(delta, axis=1)
        delta *= np.minimum(1, .020/np.maximum(lengths, 1e-9))[:, None]
        return points+delta*self.strength

    def apply(self, parts):
        import bpy
        from mathutils import Vector
        bpy.context.view_layer.update()
        head = next(o for o in parts if o.get('anatomical_head'))
        head.data.calc_loop_triangles()
        triangles = np.asarray([tuple(t.vertices) for t in head.data.loop_triangles])
        original = np.asarray([tuple(v.co) for v in head.data.vertices])
        def normals(points):
            a,b,c=points[triangles[:,0]],points[triangles[:,1]],points[triangles[:,2]]
            return np.cross(b-a,c-a)
        before=normals(original)
        for _ in range(8):
            after=normals(self.warp(original))
            flipped=np.sum((before*after).sum(axis=1)<-1e-18)
            if not flipped: break
            self.strength *= .5
        if flipped:
            raise ValueError('Dopasowanie twarzy odwrociloby sciany siatki.')
        self.report.update(deformation_strength=self.strength, inverted_triangles=0,
            max_displacement_mm=float(np.linalg.norm(self.warp(original)-original,axis=1).max()*1000))
        depth=self.reference_depth(original)
        self.report.update(reference_depth_authored=bool(np.any(depth)),
            reference_depth_max_mm=float(np.max(np.abs(depth)))*self.strength*1000,
            reference_depth_preserves_neutral_xz=True)
        from photo_face_color import apply as apply_color
        apply_color(self, head, original)
        for obj in parts:
            if obj.type != 'MESH':
                continue
            if obj.get('anatomical_eye'):
                # Move the eye rigidly. The facial tissue warp must not
                # deform its globe or the circular iris texture.
                obj.location = Vector(self.warp(np.asarray([tuple(obj.location)]))[0])
                obj['photo_fit_rigid_eye'] = True
                continue
            matrix = obj.matrix_world.copy()
            points = np.asarray([tuple(matrix @ v.co) for v in obj.data.vertices])
            moved = self.warp(points)
            inverse = obj.matrix_world.inverted()
            for v, co in zip(obj.data.vertices, moved):
                v.co = inverse @ Vector(co)
            obj.data.update()
            if obj.get('anatomical_head'):
                obj['photo_face_fit'] = json.dumps(self.report)
                obj['photo_face_source_sha256'] = self.source_sha256


def load_fit(folder, parts):
    """Select one labelled subject, never blend different people or group faces."""
    report = {'revision': 1, 'applied': False, 'reason': 'no_measured_face'}
    if folder is None or not (folder/'reference-photos.json').is_file():
        return None, report
    path = folder/'reference-photos.json'
    if path.is_symlink() or path.stat().st_size > 160000:
        raise ValueError('Nieprawidlowe pomiary referencji.')
    photos = json.loads(path.read_text())
    people = [p for p in parts if p['kind'] in ('portrait','person','reference_character')]
    if len(people) != 1:
        report['reason'] = 'one_person_required'
        return None, report
    person = people[0]
    if person['kind'] != 'reference_character' and person.get('presentation') != 'feminine':
        report['reason'] = 'feminine_template_required'
        return None, report
    labels = {p.get('subject','').strip().casefold() for p in photos if p.get('faceLandmarks')}
    if len(labels) > 1:
        report['reason'] = 'ambiguous_subject_labels'
        return None, report
    candidates = [(i, p) for i, p in enumerate(photos)
                  if p.get('faceLandmarks') and p.get('view') not in ('back','detail')]
    if not candidates:
        return None, report
    i, photo = max(candidates, key=lambda pair: (pair[1]['view']=='front',
        abs(pair[1]['faceLandmarks']['points'][263][0]-pair[1]['faceLandmarks']['points'][33][0])))
    image = folder/('reference-%d.jpg' % i)
    if image.is_symlink() or not image.is_file() or image.stat().st_size > 2*1024*1024:
        raise ValueError('Brakuje zdjecia do pomiarow twarzy.')
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if digest != photo['sha256'] or digest != photo['faceLandmarks']['imageSha256']:
        raise ValueError('Pomiary twarzy pochodza z innego zdjecia.')
    fit = FaceFit(photo['faceLandmarks'])
    fit.source_sha256 = digest
    fit.image_path = image
    fit.part_name = person['name']
    from reference_match import match_fit
    match_fit(fit)
    report.update(fit.report, applied=True, reason='measured_reference', reference_index=i)
    return fit, report
