"""Versioned, data-only modeling contract shared by the planner and Blender.

No Python, expressions, file paths or dynamic attribute lookup are executed.
The same schema sent to the model is checked again before and inside Blender.
"""
import json
import math


def number(lo=-1000, hi=1000):
    return {'type': 'number', 'minimum': lo, 'maximum': hi}


def array(item, lo, hi):
    return {'type': 'array', 'items': item, 'minItems': lo, 'maxItems': hi}


def record(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties),
            'additionalProperties': False}


NAME = {'type': 'string', 'minLength': 1, 'maxLength': 64}
VEC = array(number(), 3, 3)
SIZE = array(number(0.0001, 100), 3, 3)
COLOR = array(number(0, 1), 3, 3)
INDEX = {'type': 'integer', 'minimum': 0, 'maximum': 4095}


def part(kind, fields):
    return record({'kind': {'type': 'string', 'enum': [kind]}, 'name': NAME, **fields})


def choice(*values):
    return {'type': 'string', 'enum': list(values)}


def round_sides(sides):
    # Preserve explicitly polygonal columns; round surfaces get real geometry.
    return max(64, sides) if sides >= 12 else sides


PARTS = [
    part('ellipsoid', {'material': NAME, 'center': VEC, 'radii': SIZE}),
    part('box', {'material': NAME, 'center': VEC, 'size': SIZE, 'rotation': VEC}),
    part('tube', {'material': NAME, 'points': array(VEC, 2, 128),
                  'radii': array(number(0.0001, 100), 2, 128),
                  'sides': {'type': 'integer', 'minimum': 3, 'maximum': 32}}),
    part('lathe', {'material': NAME, 'center': VEC,
                   'profile': {**array(array(number(-100, 100), 2, 2), 2, 64), 'description': 'Ordered cross-section points [radius, z]. Radius >= 0. Z can increase or decrease. Open profiles are capped to the axis; repeat the first point to close an annular profile. Never swap radius and height.'},
                   'sides': {'type': 'integer', 'minimum': 6, 'maximum': 128}}),
    part('loft', {'material': NAME, 'sections': array(record({'center': VEC, 'radii': array(number(.0001, 100), 2, 2)}), 2, 24),
                  'sides': {'type': 'integer', 'minimum': 16, 'maximum': 64}}),
    part('extrusion', {'material': NAME, 'cap_material': NAME, 'center': VEC,
                       'outline': array(array(number(-100,100),2,2),3,64),
                       'levels': array(record({'z': number(-100,100), 'scale': number(.01,3), 'offset': array(number(-100,100),2,2)}),2,24)}),
    part('person', {'center': VEC, 'height': number(.2, 3),
                    'skin_material': NAME, 'hair_material': NAME, 'top_material': NAME,
                    'trouser_material': NAME, 'shoe_material': NAME, 'accent_material': NAME,
                    'eye_material': NAME,
                    'build': choice('slim', 'average', 'broad'),
                    'presentation': choice('masculine', 'feminine', 'androgynous'),
                    'outfit': choice('streetwear', 'casual', 'formal', 'tshirt', 'sweatshirt', 'hoodie', 'couture'),
                    'hair_style': choice('short', 'buzz', 'bald', 'updo'),
                    'headwear': choice('none', 'cap', 'beanie'),
                    'pose': choice('standing', 'performing'),
                    'necklace': {'type': 'boolean'}, 'microphone': {'type': 'boolean'}}),
    part('mesh', {'material': NAME, 'vertices': array(VEC, 3, 4096),
                  'faces': array(array(INDEX, 3, 16), 1, 4096)}),
    part('copies', {'source': NAME, 'offsets': array(VEC, 1, 64)}),
    part('oak', {'material': NAME, 'leaf_material': NAME, 'center': VEC,
                 'height': number(0.1, 30), 'crown_radius': number(0.05, 15),
                 'trunk_radius': number(0.005, 3),
                 'seed': {'type': 'integer', 'minimum': 0, 'maximum': 2147483647}}),
    part('garland', {'material': NAME, 'bulb_material': NAME, 'center': VEC,
                     'radius': number(0.01, 20), 'bottom': number(0, 30),
                     'top': number(0.01, 40), 'turns': number(0.25, 6),
                     'bulbs': {'type': 'integer', 'minimum': 1, 'maximum': 100},
                     'bulb_radius': number(0.001, 1)}),
]
SCHEMA = record({
    'version': {'type': 'integer', 'enum': [1]}, 'name': NAME,
    'materials': array(record({'name': NAME, 'rgb': COLOR,
                              'pattern': {'type': 'string', 'enum': ['plain', 'bark', 'wood', 'leaf', 'stone', 'fabric', 'cotton', 'denim', 'metal', 'windows', 'skin']},
                              'roughness': number(0, 1), 'metallic': number(0, 1),
                              'emission': number(0, 5)}), 1, 8),
    'parts': array({'anyOf': PARTS}, 1, 80),
})

PROMPT = '''Design the user's requested 3D asset as a compact Froge scene JSON, version 1.
Return only the JSON object matching the provided schema. No Python or explanations.
All geometry is built by tested Blender tools. Choose the parts and parameters yourself.
Use metres, Z up, finite dimensions, shared materials and recognizable silhouettes.
Available parts: ellipsoid (radii are half dimensions), box (size is full dimensions,
rotation in radians), tube (one radius per distinct point), lathe (ordered cross-section
pairs [radius,z], radius >= 0, around Z; closed and descending profiles are supported),
loft (smooth elliptical cross-sections along an ordered 3D path), mesh (vertices and
indexed polygon faces), copies (translate a previously named primitive), person,
oak and garland. Use model-scale dimensions (usually .2-10 metres), not 828m for a tower.
Never confuse [radius,z] with [z,radius]. Stepped profiles can repeat a height with a
different radius. Do not sort or cross the profile. Example closed spire:
[[0,0],[.3,0],[.3,1],[.15,1],[.15,2],[0,3],[0,0]].
For round parts use lathe sides 64 or loft sides 48-64; reserve 6-10 sides for explicitly
polygonal architecture. Loft sections specify a center and two elliptical radii, giving
continuous sculpted bodies and limbs instead of disconnected balls and cylinders.
Use person for adult human figurines, rappers, singers and fashion characters: it uses a licensed anatomical adult base
with connected nose/lips/eyelids/ears, UV skin texture, five-finger hands, fitted headwear,
layered clothing with seams, compression folds and detailed footwear. Use a separate skin
material with pattern skin, a separate eye material, and physically plausible clothing materials.
Use cotton for jersey/tees and denim for jeans: both export real packed albedo and normal maps.
Select outfit tshirt for short sleeves and bare anatomical forearms, sweatshirt for a
crewneck without hood, hoodie for an explicitly requested hood, formal for a jacket,
and couture for a fitted floor-length fashion dress. Couture follows the body closely at
the torso and waist and expands into a long skirt; do not turn fitted clothing into thick armor.
For a woman in a reference image wearing a dress, preserve the visible original outfit and
use couture instead of substituting a jacket, hoodie or generic armor. Reconstruct missing
lower-body coverage as a coherent continuation of that dress. Use hair_style updo for a
sculpted swept-up hairstyle, buzz for close cropped hair, short for short hair, bald for none.
Do not add a hood or necklace unless requested. A classic rapper may wear a loose
white cotton tshirt, dark denim trousers and sneakers with hair_style buzz and headwear none.
Choose the person's palette, build, presentation, clothing, pose, headwear and accessories
to match the description. Add requested crystalline panels, jewelry, fans and mechanical
props as separate compact primitives. For repeated details such as fan turbines, create one
small primitive assembly and use copies/short repeated structures instead of thousands of
mesh vertices. Preserve silhouette and recognizable reference details before adding decoration.
Person faces are generic anatomical adults, not guaranteed likenesses of named real people.
For modern skyscrapers use tiers, wings, setbacks, a podium and spire as appropriate;
use the windows material pattern for a repeating glazed facade. Preserve architectural
edges. Do not call a simple cone a realistic skyscraper.
Use extrusion for noncircular towers: outline is an ordered simple XY polygon; levels
give ascending z, XY scale and XY offset. Repeat z with a smaller scale for a setback.
cap_material covers roofs and terraces. A Y-shaped outline can make a Dubai-style tower.
Use oak for oak trees: it builds a branching trunk, roots and thousands of lobed leaves.
height includes the crown; center is the base. Set leaf_material and bark material.
Garland wraps a wire around Z from bottom to top relative to center, with exact bulb
count. Radius is the outer wire radius; use bulb_material with emission > 0 for lights.
Use lathe, custom mesh, tubes, boxes and ellipsoids for other objects, including rockets,
furniture and figurines. Copies may reference only previous primitive parts, not oak,
garland, person or copies. Mesh faces must use existing, distinct vertex indices.
All names must be unique within their category; material references must exist.
For simple assets aim for 4-20 parts. Use procedural parts and copies instead of listing
repetitive geometry. Up to 40 parts / 6000 output tokens are appropriate when a complex
reference needs them; do not sacrifice silhouette, anatomy, clothing identity or requested
details just to minimize part count. Never emit giant raw vertex lists when procedural
parts can express the same feature. Match every requested feature; never substitute an oak
or example for a different requested object. Do not request input files.
Materials are exported as PBR and packed UV textures; emission makes visible luminous
surfaces, not physical illumination of other meshes in every viewer.'''


def check(value, schema, path='$'):
    """Validate the deliberately small JSON Schema subset used above."""
    if 'anyOf' in schema:
        variant = next((s for s in schema['anyOf'] if isinstance(value, dict)
                        and value.get('kind') == s['properties']['kind']['enum'][0]), None)
        if variant is None:
            raise ValueError(path + ': nieznany typ czesci.')
        return check(value, variant, path)
    kind = schema['type']
    if kind == 'object':
        if not isinstance(value, dict) or set(value) != set(schema['required']):
            raise ValueError(path + ': wymagane pola: ' + ', '.join(schema['required']))
        for key, val in value.items():
            check(val, schema['properties'][key], path + '.' + key)
    elif kind == 'array':
        if not isinstance(value, list) or not schema['minItems'] <= len(value) <= schema['maxItems']:
            raise ValueError(path + ': nieprawidlowa liczba elementow.')
        for i, val in enumerate(value):
            check(val, schema['items'], path + '[%d]' % i)
    elif kind in ('number', 'integer'):
        valid_type = type(value) is int if kind == 'integer' else type(value) in (int, float)
        if not valid_type or not math.isfinite(value) or not schema.get('minimum', -math.inf) <= value <= schema.get('maximum', math.inf):
            raise ValueError(path + ': liczba poza zakresem.')
    elif kind == 'boolean':
        if type(value) is not bool:
            raise ValueError(path + ': wymagane true lub false.')
    elif kind == 'string':
        if not isinstance(value, str) or not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 100):
            raise ValueError(path + ': nieprawidlowy tekst.')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(path + ': niedozwolona wartosc.')


def lathe_profile(profile):
    """Return an oriented, simple closed radial cross-section, never sorted.

    A lathe can have descending walls, ledges, a closed outline or an open
    outer wall. The old monotonic-height check incorrectly rejected these.
    Self-crossing and zero-volume contours remain invalid.
    """
    eps = 1e-10
    points = []
    for radius, z in profile:
        if radius < 0:
            raise ValueError('Profil: promien musi byc >= 0; kolejnosc par to [promien, Z].')
        point = (radius, z)
        if not points or math.dist(point, points[-1]) > eps:
            points.append(point)
    if len(points) < 2 or max(r for r, z in points) <= eps or max(z for r,z in points)-min(z for r,z in points) <= eps:
        raise ValueError('Profil nie tworzy bryly: potrzebuje niezerowej szerokosci i wysokosci.')
    closed = math.dist(points[0], points[-1]) <= eps
    if closed:
        points.pop()
    else:
        points += [(0, points[-1][1]), (0, points[0][1])]
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(points) > 2:
        remove = next((i for i,b in enumerate(points)
                       if math.dist(points[i-1],b) <= eps
                       or (abs(cross(points[i-1],b,points[(i+1)%len(points)])) <= eps
                           and (b[0]-points[i-1][0])*(points[(i+1)%len(points)][0]-b[0])
                           +(b[1]-points[i-1][1])*(points[(i+1)%len(points)][1]-b[1]) >= 0)), None)
        if remove is None: break
        points.pop(remove)
    def on(a,b,c):
        return abs(cross(a,b,c)) <= eps and min(a[0],b[0])-eps <= c[0] <= max(a[0],b[0])+eps and min(a[1],b[1])-eps <= c[1] <= max(a[1],b[1])+eps
    edges = list(zip(points, points[1:]+points[:1]))
    for i,(a,b) in enumerate(edges):
        for j,(c,d) in enumerate(edges[i+1:], i+1):
            if j == i+1 or (i == 0 and j == len(edges)-1): continue
            if cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0 or any((on(a,b,c),on(a,b,d),on(c,d,a),on(c,d,b))):
                raise ValueError('Profil przecina sam siebie. Podaj punkty kolejno wzdluz obrysu [promien, Z].')
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)
    if abs(area) <= eps:
        raise ValueError('Profil ma zerowe pole przekroju.')
    return points if area > 0 else list(reversed(points))


def polygon_outline(points):
    if math.dist(points[0],points[-1])<1e-10:points=points[:-1]
    shift=1-min(p[0] for p in points)
    contour=lathe_profile([[x+shift,y] for x,y in points]+[[points[0][0]+shift,points[0][1]]])
    return [(x-shift,y) for x,y in contour]


def validate_scene(value):
    if isinstance(value,dict) and isinstance(value.get('parts'),list):
        for p in value['parts']:
            if isinstance(p,dict) and p.get('kind')=='person':p.setdefault('hair_style','short')
    check(value, SCHEMA)
    mats = [m['name'] for m in value['materials']]
    if len(set(mats)) != len(mats):
        raise ValueError('Powtorzona nazwa materialu.')
    known = {}
    vertices = triangles = objects = 0
    for p in value['parts']:
        kind, name = p['kind'], p['name']
        if name in known:
            raise ValueError('Powtorzona nazwa czesci: ' + name)
        for field in ('material', 'cap_material', 'leaf_material', 'bulb_material', 'skin_material', 'hair_material', 'top_material', 'trouser_material', 'shoe_material', 'accent_material', 'eye_material'):
            if field in p and p[field] not in mats:
                raise ValueError('Nieznany material: ' + p[field])
        v, t, count = 0, 0, 1
        if kind == 'mesh':
            for face in p['faces']:
                if max(face) >= len(p['vertices']) or len(set(face)) != len(face):
                    raise ValueError('Sciana siatki ma nieprawidlowe indeksy.')
                origin = p['vertices'][face[0]]
                vectors = [[p['vertices'][i][a] - origin[a] for a in range(3)] for i in face[1:]]
                def area(a, b):
                    return sum((a[(k+1)%3]*b[(k+2)%3]-a[(k+2)%3]*b[(k+1)%3])**2 for k in range(3))
                if not any(area(vectors[0], b) > 1e-20 for b in vectors[1:]):
                    raise ValueError('Sciana siatki ma zerowe pole.')
            v, t = len(p['vertices']), sum(len(f) - 2 for f in p['faces'])
        elif kind == 'tube':
            if len(p['points']) != len(p['radii']) or any(a == b for a, b in zip(p['points'], p['points'][1:])):
                raise ValueError('Rura wymaga osobnego promienia dla kazdego roznego punktu.')
            v = len(p['points']) * p['sides']; t = 2 * v
        elif kind == 'lathe':
            contour = lathe_profile(p['profile'])
            v = len(contour) * round_sides(p['sides']); t = 2 * v
        elif kind == 'loft':
            if any(a['center'] == b['center'] for a,b in zip(p['sections'],p['sections'][1:])):
                raise ValueError('Loft wymaga roznych kolejnych srodkow przekrojow.')
            v = ((len(p['sections'])-1)*6+1)*p['sides']; t = 2*v
        elif kind == 'extrusion':
            outline=polygon_outline(p['outline'])
            levels=p['levels']
            if levels[-1]['z']<=levels[0]['z'] or any(b['z']<a['z'] or b==a for a,b in zip(levels,levels[1:])):
                raise ValueError('Ekstruzja wymaga poziomow od dolu do gory; uskok moze powtorzyc Z przy innej skali.')
            v=len(outline)*len(levels);t=2*v
        elif kind == 'person':
            v, t, count = 180000, 360000, 8
        elif kind == 'ellipsoid':
            v, t = 2562, 5120
        elif kind == 'box':
            v, t = 8, 12
        elif kind == 'oak':
            if not p['trunk_radius'] < p['crown_radius'] < p['height'] or p['trunk_radius'] > p['height'] / 4:
                raise ValueError('Dab wymaga korony szerszej od pnia i proporcjonalnej wysokosci.')
            v, t, count = 85000, 140000, 2
        elif kind == 'garland':
            if p['top'] <= p['bottom'] or p['bulb_radius'] >= p['radius'] / 2:
                raise ValueError('Lampki wymagaja rosnacej wysokosci i mniejszych zarowek.')
            v, t, count = 1600 + p['bulbs'] * 642, 3200 + p['bulbs'] * 1280, 2
        elif kind == 'copies':
            source = known.get(p['source'])
            if not source or source[0] in ('oak', 'garland', 'copies', 'person'):
                raise ValueError('Kopie wymagaja wczesniejszej podstawowej czesci.')
            count = len(p['offsets']); v, t = source[1] * count, source[2] * count
        known[name] = (kind, v, t)
        vertices += v; triangles += t; objects += count
    if vertices > 200000 or triangles > 400000 or objects > 256:
        raise ValueError('Plan przekracza laczny limit geometrii. Zmniejsz liczbe czesci lub kopii.')
    return value


def parse_scene(text):
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 60000:
        raise ValueError('Oczekiwano kompletnego planu JSON do 60 KB.')
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('Powtorzone pole JSON: ' + k)
            result[k] = v
        return result
    return validate_scene(json.loads(text, object_pairs_hook=unique))
