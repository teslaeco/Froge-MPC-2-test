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


PARTS = [
    part('ellipsoid', {'material': NAME, 'center': VEC, 'radii': SIZE}),
    part('box', {'material': NAME, 'center': VEC, 'size': SIZE, 'rotation': VEC}),
    part('tube', {'material': NAME, 'points': array(VEC, 2, 128),
                  'radii': array(number(0.0001, 100), 2, 128),
                  'sides': {'type': 'integer', 'minimum': 3, 'maximum': 32}}),
    part('lathe', {'material': NAME, 'center': VEC,
                   'profile': array(array(number(0, 100), 2, 2), 2, 64),
                   'sides': {'type': 'integer', 'minimum': 6, 'maximum': 48}}),
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
                              'pattern': {'type': 'string', 'enum': ['plain', 'bark', 'wood', 'leaf', 'stone', 'fabric', 'metal']},
                              'roughness': number(0, 1), 'metallic': number(0, 1),
                              'emission': number(0, 5)}), 1, 8),
    'parts': array({'anyOf': PARTS}, 1, 80),
})

PROMPT = '''Design the user's requested 3D asset as a compact Froge scene JSON, version 1.
Return only the JSON object matching the provided schema. No Python or explanations.
All geometry is built by tested Blender tools. Choose the parts and parameters yourself.
Use metres, Z up, finite dimensions, shared materials and recognizable silhouettes.
Available parts: ellipsoid (radii are half dimensions), box (size is full dimensions,
rotation in radians), tube (one radius per distinct point), lathe (profile pairs are
[radius,z], nondecreasing z, around Z), mesh (vertices and indexed polygon faces),
copies (translate a previously named primitive), oak and garland.
Use oak for oak trees: it builds a branching trunk, roots and thousands of lobed leaves.
height includes the crown; center is the base. Set leaf_material and bark material.
Garland wraps a wire around Z from bottom to top relative to center, with exact bulb
count. Radius is the outer wire radius; use bulb_material with emission > 0 for lights.
Use lathe, custom mesh, tubes, boxes and ellipsoids for other objects, including rockets,
furniture and figurines. Copies may reference only previous primitive parts, not oak,
garland or copies. Mesh faces must use existing, distinct vertex indices.
All names must be unique within their category; material references must exist.
Keep JSON short: aim for 4-20 parts, under 1200 output tokens. Use procedural parts and
copies instead of listing repetitive geometry. Match every requested feature; never
substitute an oak or example for a different requested object. Do not request input files.
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
    elif kind == 'string':
        if not isinstance(value, str) or not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 100):
            raise ValueError(path + ': nieprawidlowy tekst.')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(path + ': niedozwolona wartosc.')


def validate_scene(value):
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
        for field in ('material', 'leaf_material', 'bulb_material'):
            if field in p and p[field] not in mats:
                raise ValueError('Nieznany material: ' + p[field])
        v, t, count = 0, 0, 1
        if kind == 'mesh':
            for face in p['faces']:
                if max(face) >= len(p['vertices']) or len(set(face)) != len(face):
                    raise ValueError('Sciana siatki ma nieprawidlowe indeksy.')
                origin = p['vertices'][face[0]]
                # Reject collinear polygons before Blender can silently discard them.
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
            if not any(r > 0 for r, z in p['profile']) or p['profile'][-1][1] <= p['profile'][0][1] or any(b[1] < a[1] for a, b in zip(p['profile'], p['profile'][1:])):
                raise ValueError('Profil wymaga dodatniego promienia i rosnacej wysokosci Z.')
            v = len(p['profile']) * p['sides'] + 2; t = 2 * v
        elif kind == 'ellipsoid':
            v, t = 162, 320
        elif kind == 'box':
            v, t = 8, 12
        elif kind == 'oak':
            if not p['trunk_radius'] < p['crown_radius'] < p['height'] or p['trunk_radius'] > p['height'] / 4:
                raise ValueError('Dab wymaga korony szerszej od pnia i proporcjonalnej wysokosci.')
            v, t, count = 85000, 140000, 2
        elif kind == 'garland':
            if p['top'] <= p['bottom'] or p['bulb_radius'] >= p['radius'] / 2:
                raise ValueError('Lampki wymagaja rosnacej wysokosci i mniejszych zarowek.')
            v, t, count = 1600 + p['bulbs'] * 162, 3200 + p['bulbs'] * 320, 2
        elif kind == 'copies':
            source = known.get(p['source'])
            if not source or source[0] in ('oak', 'garland', 'copies'):
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
