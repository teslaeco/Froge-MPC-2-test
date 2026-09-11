"""Bounded portrait proportions on the connected anatomical head.

These controls are authored from a reference, not a biometric reconstruction.
The orbit mask keeps the original eye globes and eyelid contact coherent.
"""
import math

CONTROLS = ('nose_width', 'nose_projection', 'mouth_width', 'lip_fullness',
            'jaw_width', 'chin_height', 'cheek_fullness')


def profile(values=None):
    values = values or {}
    if set(values) - set(CONTROLS):
        raise ValueError('Unknown portrait control')
    result = {key: 0. for key in CONTROLS}
    for key, value in values.items():
        if type(value) not in (int, float) or not math.isfinite(value) or not -1 <= value <= 1:
            raise ValueError('Portrait controls must be finite numbers between -1 and 1')
        result[key] = float(value)
    return result


def step(lo, hi, value):
    t = max(0., min(1., (value - lo) / (hi - lo)))
    return t*t*(3-2*t)


def gauss(value, centre, width):
    return math.exp(-.5*((value-centre)/width)**2)


def brow_height(t,eye_z,glam=False):
    if glam:
        return eye_z+.020+.0062*math.sin(math.pi*t)*(.62+1.10*t)-.001*t
    return eye_z+.020+.005*math.sin(t*math.pi)-.004*t


def measured_gaze(observation, baseline):
    """Return a conjugate iris offset from image-plane landmark measurements.

    Iris z values are not on the face-depth scale in MediaPipe. Projecting them
    through the face pose produces a spurious sideways gaze on a turned head.
    Use each eye's 2D corner frame, subtract the neutral detector calibration,
    and average the two eyes to avoid inventing binocular divergence.
    Offsets are expressed in globe-radius units, without moving lids or skin.
    """
    def offsets(data):
        points = [(p[0]*data['width'], -p[1]*data['height']) for p in data['points']]
        result = []
        for iris, a, b in ((468, 33, 133), (473, 362, 263)):
            ax, ay = points[a]; bx, by = points[b]
            dx, dy = bx-ax, by-ay
            width = math.hypot(dx, dy)
            if width < 4:
                return None
            ix, iy = points[iris]
            rx, ry = ix-(ax+bx)/2, iy-(ay+by)/2
            horizontal = (rx*dx+ry*dy)/(width*width)
            vertical = (-rx*dy+ry*dx)/(width*width)
            if not all(math.isfinite(v) for v in (horizontal, vertical)) or abs(horizontal) > .4 or abs(vertical) > .3:
                return None
            result.append((horizontal, vertical))
        return result
    target, neutral = offsets(observation), offsets(baseline)
    if target is None or neutral is None:
        return (0., 0.)
    # Aperture width is approximately 1.9 globe radii in the neutral anatomy.
    delta = [sum(t[i]-n[i] for t,n in zip(target, neutral))*.95 for i in (0,1)]
    return (max(-.32, min(.32, delta[0])), max(-.22, min(.22, delta[1])))


def point(position, controls):
    x, y, z = map(float, position)
    # Preserve the complete orbital region and the neck, even at extreme values.
    front = (1-step(-.135, -.082, y))*step(1.535, 1.570, z)*(1-step(1.657, 1.674, z))
    if front == 0:
        return x, y, z
    nose = gauss(x, 0, .019)*gauss(z, 1.645, .012)*front
    mouth = gauss(x, 0, .031)*gauss(z, 1.612, .014)*front
    # The anatomical mouth seam is near 1.612 m. Its upper and lower lips
    # need separate volumes; centring the entire bulge at 1.620 raised the
    # philtrum while leaving the lower lip almost unchanged.
    lips=gauss(x,0,.024)*(gauss(z,1.618,.0045)+.90*gauss(z,1.606,.0045))*front
    jaw = gauss(abs(x), .052, .030)*gauss(z, 1.599, .023)*front
    chin = gauss(x, 0, .043)*gauss(z, 1.583, .020)*front
    cheek = gauss(abs(x), .050, .025)*gauss(z, 1.650, .019)*front
    # Previous millimetre-scale coefficients made non-neutral plans visually
    # indistinguishable from the generic head.  These remain bounded below the
    # topology test's 25 mm envelope, but now read in portrait and figure views.
    dx = x*(.38*controls['nose_width']*nose + .30*controls['mouth_width']*mouth + .26*controls['jaw_width']*jaw)
    dy = -.012*controls['nose_projection']*nose - .006*controls['lip_fullness']*lips - .0065*controls['cheek_fullness']*cheek
    dz = (z-1.612)*.30*controls['lip_fullness']*lips + .010*controls['chin_height']*chin
    return x+dx, y+dy, z+dz


def sculpt(obj, values):
    controls = profile(values)
    for vertex in obj.data.vertices:
        vertex.co = point(vertex.co, controls)
    obj.data.update()
    obj['portrait_controls'] = str(controls)
    obj['portrait_method'] = 'Reference-guided anatomical sculpt; likeness requires visual review'
