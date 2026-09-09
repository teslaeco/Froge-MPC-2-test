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


def point(position, controls):
    x, y, z = map(float, position)
    # Preserve the complete orbital region and the neck, even at extreme values.
    front = (1-step(-.135, -.082, y))*step(1.535, 1.570, z)*(1-step(1.657, 1.674, z))
    if front == 0:
        return x, y, z
    nose = gauss(x, 0, .019)*gauss(z, 1.645, .012)*front
    mouth = gauss(x, 0, .031)*gauss(z, 1.620, .014)*front
    jaw = gauss(abs(x), .052, .030)*gauss(z, 1.599, .023)*front
    chin = gauss(x, 0, .043)*gauss(z, 1.583, .020)*front
    cheek = gauss(abs(x), .050, .025)*gauss(z, 1.650, .019)*front
    dx = x*(.24*controls['nose_width']*nose + .23*controls['mouth_width']*mouth + .16*controls['jaw_width']*jaw)
    dy = -.006*controls['nose_projection']*nose - .002*controls['lip_fullness']*mouth - .005*controls['cheek_fullness']*cheek
    dz = (z-1.620)*.30*controls['lip_fullness']*mouth + .008*controls['chin_height']*chin
    return x+dx, y+dy, z+dz


def sculpt(obj, values):
    controls = profile(values)
    for vertex in obj.data.vertices:
        vertex.co = point(vertex.co, controls)
    obj.data.update()
    obj['portrait_controls'] = str(controls)
    obj['portrait_method'] = 'Reference-guided anatomical sculpt; likeness requires visual review'
