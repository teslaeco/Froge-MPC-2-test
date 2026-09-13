"""Versioned, data-only modeling contract shared by the planner and Blender.

No Python, expressions, file paths or dynamic attribute lookup are executed.
The same schema sent to the model is checked again before and inside Blender.
"""
import json
import math
import re
import unicodedata
try:
    from .reference_reconstruction import POLICY as RECONSTRUCTION_POLICY
except ImportError:  # Blender runs scripts with the renderer directory on sys.path.
    from reference_reconstruction import POLICY as RECONSTRUCTION_POLICY
from copy import deepcopy


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


FACE = record({key:number(-1,1) for key in ('nose_width','nose_projection','mouth_width','lip_fullness','jaw_width','chin_height','cheek_fullness')})
EYE_STATES = record({'left':choice('present','empty_socket'),
                     'right':choice('present','empty_socket'),
                     'evidence':{'type':'string','minLength':0,'maxLength':400}})
PORTRAIT_FIELDS = {'presentation':choice('masculine','feminine','androgynous'),
                   'hair_style':choice('short','buzz','bald','shoulder_length','long_wavy','straight_bob','curly','ponytail'),
                   'headwear':choice('none','cap','beanie'), 'face':FACE,
                   'eyewear':choice('none','sunglasses'),
                   'makeup':choice('none','soft_glam')}


COUTURE_FIELDS = {
    'center':VEC, 'height':number(1.2,2.2), 'build':choice('slim','average'),
    **{key+'_material':NAME for key in ('skin','hair','dress','crystal','accent','shoe','eye','nail')},
    'face':FACE, 'head_rotation':array(number(-.35,.35),3,3), 'makeup':choice('none','soft_glam'),
    'garment_offset':number(.001,.018), 'garment_thickness':number(.001,.006),
    'hem_radius':number(.22,.45), 'updo':{'type':'boolean'}, 'hair_ornament':{'type':'boolean'},'cape':{'type':'boolean'},
    'fan':record({'enabled':{'type':'boolean'},'radius':number(.20,.43),
                  'panels':{'type':'integer','minimum':8,'maximum':18},
                  'rotors':{'type':'integer','minimum':4,'maximum':18},'spread':number(1.5,2.6)}),
    'observed_features':array(NAME,1,16),'reconstructed_features':array(NAME,1,16),
}

PARTS = [
    part('surface_grid', {'material':NAME, 'control_grid':array(array(VEC,2,16),2,16),
                         'samples':{'type':'integer','minimum':1,'maximum':4},
                         'thickness':number(0,.1)}),
    part('contour_loft', {'material':NAME, 'rings':array(array(VEC,4,64),2,24),
                         'samples':{'type':'integer','minimum':1,'maximum':4},
                         'caps':{'type':'boolean'}}),
    part('reference_character',COUTURE_FIELDS),
    part('rotor',{'material':NAME,'accent_material':NAME,'center':VEC,'radius':number(.005,2),
                  'depth':number(.001,.2),'blades':{'type':'integer','minimum':3,'maximum':16}}),
    part('radial_copies',{'source':NAME,'center':VEC,'count':{'type':'integer','minimum':2,'maximum':32},
                         'radius':number(.001,20),'start_angle':number(-6.284,6.284),'arc_angle':number(-6.284,6.284)}),
    part('portrait', {'center':VEC,'scale':number(.5,2),'rotation':VEC,
                      'skin_material':NAME,'hair_material':NAME,'eye_material':NAME,
                      'eye_states':EYE_STATES,**PORTRAIT_FIELDS}),
    part('anatomical_hand', {'wrist':VEC,'direction':VEC,'palm_normal':VEC,
                            'side':choice('left','right'),'presentation':PORTRAIT_FIELDS['presentation'],
                            'scale':number(.5,2),'curl':number(0,1.8),'nail_length':number(0,.004),
                            'skin_material':NAME,'nail_material':NAME}),
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
                    'body_shape': choice('natural', 'curvy'),
                    'clothing_fit': choice('fitted', 'regular', 'oversized'),
                    'presentation': choice('masculine', 'feminine', 'androgynous'),
                    'outfit': choice('streetwear', 'casual', 'formal', 'tshirt', 'sweatshirt', 'hoodie','crop_skirt','puffer_crop','black_crop'),
                    'hair_style': PORTRAIT_FIELDS['hair_style'],
                    'face':FACE,'makeup':choice('none','soft_glam'),'nail_material':NAME,
                    'eyewear':choice('none','sunglasses'),
                    'shirt_graphic': choice('none', 'LA'),
                    'headwear': choice('none', 'cap', 'beanie'),
                    'pose': choice('standing', 'performing','sitting'),
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
REFERENCE_VIEW = record({
    'photo_index':{'type':'integer','minimum':0,'maximum':3},
    'position':VEC,'target':VEC,'up':VEC,
    'projection':choice('orthographic','perspective'),
    'vertical_span':number(.001,100), 'fov':number(.15,2.5),
    'regions':array(record({'part':NAME,'polygon':array(array(number(0,1),2,2),3,64)}),1,80),
})
SCHEMA = record({
    'version': {'type': 'integer', 'enum': [1,2]}, 'name': NAME,
    'subject_type': choice('object','animal','person','portrait'),
    'materials': array(record({'name': NAME, 'rgb': COLOR,
                              'pattern': {'type': 'string', 'enum': ['plain', 'bark', 'wood', 'leaf', 'stone', 'fabric', 'cotton', 'denim', 'metal', 'windows', 'skin','satin','crystal']},
                              'roughness': number(0, 1), 'metallic': number(0, 1),
                              'emission': number(0, 5)}), 1, 8),
    'parts': array({'anyOf': PARTS}, 1, 80),
    'reference_views':array(REFERENCE_VIEW,0,4),
})

PROMPT = '''Design the user's requested 3D asset as a compact Froge scene JSON, version 2.
REFERENCE ANATOMY: for deliberately skeletal or hybrid faces use portrait with
eye_states {left: present|empty_socket, right: present|empty_socket, evidence: text}.
Sides are the CHARACTER'S anatomical sides, NOT the viewer's: in a frontal image
viewer-right is anatomical left. Default both present, evidence empty string.
Declare an empty_socket only when explicitly visible or requested and describe
that evidence. Occlusion, closed eyelids or failed edits are NOT missing eyes.
The base omits ONLY the declared globe, brow and lashes. It does NOT reconstruct
a skull: sculpt the orbital cavity, bone, nose, dental arches and continuous seam
with edit_model after the base build. An empty socket is recessed space, never
a black eyeball. Ordinary faces retain two eyes and lashes on both sides.
Human face-landmark warping is disabled for this explicit nonhuman anatomy;
reference texture projection remains available. Fit silhouette and each living
feature from the actual image; do not force human eyelids/iris landmarks onto bone.
REFERENCE-CONDITIONED CONSTRUCTION: identify each visible component and its silhouette,
depth, orientation and material from the actual uploaded images. Choose tools that
match that evidence. The presence of a human does not imply a preset outfit.
For custom clothing, hair sections, organic shells, animals, furniture or product
panels, surface_grid is a rectangular grid of XYZ control points in metres, with
2..16 rows and columns, samples 1..4 per interval, thickness 0..0.1 m. It makes an
interpolated surface; use positive physical thickness for a garment/panel shell.
contour_loft joins 2..24 freeform closed rings of equal 4..64 XYZ points; samples
1..4 interpolates along AND around rings; caps closes the ends. Start each ring at
the corresponding landmark and keep winding consistent. Unlike elliptical loft,
each ring may be asymmetric. Keep control grids regular, nondegenerate and modest.
These tools support new shapes, not just known reference templates. A dense grid
does not create missing detail: use controls to match the observed geometry.
PHOTO TEXTURES: reference_views is [] without images. With images, estimate a camera
and select visible subject regions for each useful photo. photo_index is ZERO-based.
position/target/up are world coordinates; local front is -Y, Z is up. For orthographic
views vertical_span is the full image height in world metres. For perspective views,
fov is the vertical field of view in radians. Both fields must be supplied.
Each region binds one existing part name to a simple polygon of normalized image
coordinates (x right, y down, origin top left). Trace only pixels belonging to that
part; exclude background, fingers over a prop, face over a collar and other occluders.
Use separate part names and image polygons for clothing, hair, props and anatomy.
The renderer projects original pixels only onto visible, camera-facing mesh faces
inside the selected region, with depth testing. Other faces keep their material.
Infer camera and geometry together; inaccurate camera estimates misalign textures.
Reference projection is photographed colour, not de-lit PBR or verified identity.
Never cover the entire scene with an image plane. Preserve hidden volume and use
other supplied views for its observed sides; unseen surfaces remain inferred.
MATERIAL CLOSURE: declare at most 8 materials, then use their exact names in
every material and *_material field. A color description is not a declaration.
For example eye_material "eyes_grey_green" requires a material with exactly
that name. Check every reference, including eyes, nails, shoes and trim. Share
compatible materials when needed; never leave an undeclared ninth material.
Material rgb values are display/sRGB colors; keep the reference palette. Colored
cloth and crystal panels must not be replaced by silver metal. Metals are trim.
COUTURE REFERENCE: for a standing adult woman in a fitted floor-length crystalline
gown, reference_character is an OPTIONAL approximation: continuous bodice/skirt, conformal thin inlays,
collar, sleeves, legs, anatomical portrait/hands, updo and optional mechanical
pleated fan. Never put a sweatshirt, T-shirt, trousers or padded armor beneath it.
Set cape true only for a visible/requested drape attached to the shoulders.
garment_offset is actual radial clearance .001-.018 m (normally .004);
garment_thickness .001-.006 m (normally .002, never more than the offset).
Choose seven face proportions and head_rotation from the image, soft_glam makeup
when visible. This is a parameterised anatomical face, not identity recovery.
dress_material pattern satin; crystal_material pattern crystal; skin nonmetallic.
The fan has actual panels and small rotors on the rim. Set enabled false unless
requested/visible. Count the visible panels and rotors; do not invent extras.
Estimate its radius relative to the face and torso rather than oversizing it.
observed_features describes visible evidence;
reconstructed_features identifies the unseen back, legs, feet and lower hem.
This operation only supports this gown and standing pose; use person or portrait
+ anatomical_hand and custom garments for other outfits and poses.
rotor has its axis along Y; radial_copies creates linked copies around an XZ arc
with angles measured from +Z towards +X. Use compact repeated operations.
GROUP SCENES: up to THREE distinct people are supported, each with its own
anatomical portrait, two anatomical hands, face parameters, hairstyle and clothes.
Do not average different reference people into one face. A group photograph is
a composition reference, not additional views of a single person. Keep named
subjects consistent across photos. Use the label attached to each image.
The geometry allowance scales per portrait; NEVER remove facial anatomy to fit
a group. For requests for both a group and individual copies, build the group
once; individual variants belong in separate jobs, not duplicates in this scene.
Use straight_bob for chin/shoulder-length straight hair, curly for ringlets,
ponytail for tied-back hair. Match the visible hairstyle instead of making all
women long-haired. Preserve reference skin color and proportions. If makeup or
manicure is requested, soft_glam and the nail material must visibly implement it.
FASHION GARMENTS: person outfit crop_skirt builds a fitted sleeveless high-neck
top, short pleated skirt and tall boots; puffer_crop builds a black crop top,
open padded vest in top_material and fitted trousers; black_crop builds a crop
top, shorts and an open jacket in top_material. Use pose sitting for a seated
person with bent knees, or standing. These choices preserve photo clothing
better than substituting an ordinary T-shirt and trousers. At most 3 people.
Return only the JSON object matching the provided schema. No Python or explanations.
All geometry is built by tested Blender tools. Choose the parts and parameters yourself.
Set subject_type from the requested subject and photos: person for any full human
figure (including seated), portrait for a human head/bust, animal or object otherwise.
MANDATORY HUMAN DETAIL FLOOR: use person, or use portrait + two anatomical_hand parts
for a custom pose. Never approximate a human face, nose, mouth, eye or fingers using
balls, boxes, tubes or low-resolution custom meshes. Such plans are rejected.
For a seated figure use lofts/custom parts for the posed body, clothing and boots,
then portrait for the head and anatomical_hand for each exposed hand. Preserve the
seated pose from the photo; do not substitute a standing person.
Portrait center is the midpoint between eyes in world metres; scale 1 is adult size.
Local face points -Y; rotation is XYZ radians around the eye midpoint. Face contains
seven bounded [-1,1] proportions: nose_width, nose_projection, mouth_width,
lip_fullness, jaw_width, chin_height, cheek_fullness. Zero is neutral adult anatomy.
Choose them from visible reference proportions, never claim biometric reconstruction.
Use long_wavy for long detailed wavy hair, soft_glam makeup only when requested.
Anatomical_hand wrist attaches to the sleeve, direction points from wrist to middle
knuckle, palm_normal points OUT OF THE BACK of the hand, transverse to direction.
side is the person's anatomical left/right. Scale 1 is an adult hand; curl is radians
0 to 1.8; nail_length 0 to .004 m. Every hand has five connected fingers and five
surface-fitted nails. nail_material sets their color; use a separate nonmetallic
rose/nude material for a requested manicure and a skin-like material otherwise.
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
Use person for adult human figurines, rappers and singers: it uses a licensed anatomical adult base
with connected nose/lips/eyelids/ears, UV skin texture, five-finger hands, fitted headwear,
layered clothing with seams, pockets, compression folds, ribbed cuffs and detailed sneakers. Use a separate skin material with pattern skin, matte
fabric for clothes and a separate eye material (dark iris color or neutral white).
Use cotton for jersey/tees and denim for jeans: both export real packed albedo and normal maps.
Select outfit tshirt for short sleeves and bare anatomical forearms, sweatshirt for a
crewneck without hood, hoodie for an explicitly requested hood, formal for a jacket.
Do not add a hood, cap, beanie or necklace unless explicitly requested. Being a singer
or rapper does not imply jewelry or headwear: default headwear none, necklace false.
For an adult woman/singer use presentation feminine; if no hairstyle is specified,
choose shoulder_length and build average. Never default every woman to slim.
Use body_shape curvy for requested fuller bust/hips/glutes or an hourglass silhouette;
natural otherwise. Build controls general body mass, not gender or bust size.
Choose clothing_fit fitted for close-fitting clothes, oversized for loose/oversize,
regular otherwise. Preserve explicitly requested short/bald hair
or other body build. A microphone request sets microphone true and pose performing.
Clothes must have pattern cotton (tees/sweatshirts) or denim (jeans), metallic 0,
roughness .8-.95 and emission 0. Do not use glossy plain material for normal fabric.
A classic rapper may wear a loose
white cotton tshirt, dark denim trousers and sneakers with hair_style buzz and headwear none.
Use hair_style buzz for close cropped hair, short for short hair, bald for no hair, shoulder_length for layered wavy shoulder-length hair. Use shirt_graphic LA only when the user requests LA lettering; otherwise none. T-shirts hang untucked over the trousers with draped fabric folds.
Choose the person's palette, build, presentation, clothing, pose, headwear and accessories
to match the description. Add separate requested props using other operations. Person
faces are generic anatomical adults, not guaranteed likenesses of named real people.
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
For simple assets aim for 4-20 parts. Use procedural parts and
copies instead of listing repetitive geometry. Up to 40 parts / 3000 tokens are appropriate
when a complex asset needs them; do not sacrifice the silhouette or requested details
just to minimize part count. Match every requested feature; never
substitute an oak or example for a different requested object. Do not request input files.
Materials are exported as PBR and packed UV textures; emission makes visible luminous
surfaces, not physical illumination of other meshes in every viewer.'''


PROMPT += RECONSTRUCTION_POLICY


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
    # Drop duplicate or redundant straight-line vertices introduced by caps.
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
    # Translate the XY outline into the nonnegative radial validation domain;
    # validation concerns its planar simplicity, not its eventual interpretation.
    if math.dist(points[0],points[-1])<1e-10:points=points[:-1]
    shift=1-min(p[0] for p in points)
    contour=lathe_profile([[x+shift,y] for x,y in points]+[[points[0][0]+shift,points[0][1]]])
    return [(x-shift,y) for x,y in contour]


MATERIAL_FIELDS = ('material','cap_material','leaf_material','bulb_material',
                   'skin_material','hair_material','top_material','trouser_material',
                   'shoe_material','accent_material','eye_material','nail_material',
                   'dress_material','crystal_material')


class MaterialReferenceError(ValueError):
    """Structurally valid scene with unresolved material references."""
    def __init__(self, scene, missing):
        self.scene=deepcopy(scene)
        self.missing=deepcopy(missing)
        super().__init__('Nieznany material: '+', '.join(missing))


def material_repair_schema(scene):
    """Fixed palette slots make every returned binding resolve by construction."""
    fields=SCHEMA['properties']['materials']['items']['properties']
    names=sorted({p[field] for p in scene['parts'] for field in MATERIAL_FIELDS if field in p})
    return record({'slots':array(record({k:v for k,v in fields.items() if k!='name'}),8,8),
                   'bindings':record({name:{'type':'integer','minimum':0,'maximum':7} for name in names})})


def apply_material_repair(original, text, prompt=None):
    repair=load_scene_json(text)
    check(repair,material_repair_schema(original),'material_repair')
    bindings=repair['bindings'];slot_names={}
    # Keep existing names where possible; names can select procedural textures.
    for material in original['materials']:
        if material['name'] in bindings:
            slot_names.setdefault(bindings[material['name']],material['name'])
    for name,index in bindings.items():slot_names.setdefault(index,name)
    scene=deepcopy(original)
    scene['materials']=[{'name':slot_names[i],**repair['slots'][i]} for i in sorted(slot_names)]
    for part in scene['parts']:
        for field in MATERIAL_FIELDS:
            if field in part:part[field]=slot_names[bindings[part[field]]]
    scene=parse_scene(json.dumps(scene),prompt)
    return scene,{'kind':'bounded-material-palette-repair',
        'bindings':{name:slot_names[i] for name,i in bindings.items()},
        'material_count':len(scene['materials']),'geometry_from_original_plan':True,
        'colors_independently_verified':False}


def validate_scene(value):
    # Backward-compatible input normalization only; no unknown fields accepted.
    if isinstance(value,dict) and isinstance(value.get('parts'),list):
        value.setdefault('reference_views',[])
        value.setdefault('subject_type','person' if any(isinstance(p,dict) and p.get('kind') in ('person','reference_character') for p in value['parts']) else 'object')
        for p in value['parts']:
            if isinstance(p,dict) and p.get('kind')=='portrait':
                p.setdefault('eye_states',{'left':'present','right':'present','evidence':''})
            if isinstance(p,dict) and p.get('kind') in ('person','portrait'):p.setdefault('eyewear','none')
            if isinstance(p,dict) and p.get('kind')=='person':
                p.setdefault('hair_style','shoulder_length' if p.get('presentation')=='feminine' else 'short');p.setdefault('shirt_graphic','none')
                p.setdefault('body_shape','natural');p.setdefault('clothing_fit','regular')
                p.setdefault('face',{key:0. for key in FACE['properties']});p.setdefault('makeup','none');p.setdefault('nail_material',p.get('skin_material'))
    check(value, SCHEMA)
    for p in value['parts']:
        states=p.get('eye_states',{})
        if 'empty_socket' in (states.get('left'),states.get('right')) and len(states.get('evidence','').strip()) < 16:
            raise ValueError('Pusty oczodol wymaga opisu celowej anatomii z referencji (eye_states.evidence, co najmniej 16 znakow).')
    mats = [m['name'] for m in value['materials']]
    if len(set(mats)) != len(mats):
        raise ValueError('Powtorzona nazwa materialu.')
    missing={}
    for p in value['parts']:
        for field in MATERIAL_FIELDS:
            if field in p and p[field] not in mats:
                missing.setdefault(p[field],[]).append(p['name']+'.'+field)
    if missing:raise MaterialReferenceError(value,missing)
    known = {}
    vertices = triangles = objects = 0
    for p in value['parts']:
        kind, name = p['kind'], p['name']
        if name in known:
            raise ValueError('Powtorzona nazwa czesci: ' + name)
        v, t, count = 0, 0, 1
        if kind in ('surface_grid','contour_loft'):
            try:from freeform_geometry import dimensions
            except ModuleNotFoundError:from .freeform_geometry import dimensions
            v,t=dimensions(p)
        elif kind == 'mesh':
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
        elif kind == 'reference_character':
            if p['garment_thickness']>p['garment_offset']:
                raise ValueError('Suknia: grubosc nie moze przekraczac odstepu od ciala.')
            v,t,count=300000,600000,80
        elif kind == 'rotor':
            v,t,count=48+p['blades']*12,92+p['blades']*20,1
        elif kind == 'person':
            if p['pose']=='sitting' and p['outfit'] not in ('crop_skirt','puffer_crop','black_crop'):
                raise ValueError('Poza sitting wymaga stroju crop_skirt, puffer_crop lub black_crop. Dla innego stroju uzyj osobnego portrait, dwoch anatomical_hand i korpusu w zadanej pozie; nie zastepuj jej staniem.')
            v, t, count = 300000, 600000, 80
        elif kind == 'portrait':
            v,t,count=110000,210000,12
        elif kind == 'anatomical_hand':
            a,b=p['direction'],p['palm_normal']
            if sum(x*x for x in a)<1e-6 or sum(x*x for x in b)<1e-6 or sum((a[(k+1)%3]*b[(k+2)%3]-a[(k+2)%3]*b[(k+1)%3])**2 for k in range(3))<1e-6:
                raise ValueError('Dlon wymaga kierunku i poprzecznej normalnej.')
            v,t,count=12000,24000,6
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
        elif kind in ('copies','radial_copies'):
            source = known.get(p['source'])
            if not source or source[0] in ('oak', 'garland', 'copies', 'person','portrait','anatomical_hand','reference_character','radial_copies'):
                raise ValueError('Kopie wymagaja wczesniejszej podstawowej czesci.')
            count = len(p['offsets']) if kind=='copies' else p['count']; v, t = source[1] * count, source[2] * count
        known[name] = (kind, v, t)
        vertices += v; triangles += t; objects += count
    try:from projection_math import camera_basis
    except ModuleNotFoundError:from .projection_math import camera_basis
    for view in value['reference_views']:
        camera_basis(view)
        for region in view['regions']:
            if region['part'] not in known:raise ValueError('Referencja wskazuje nieznana czesc: '+region['part'])
            polygon_outline(region['polygon'])
    heads=sum(p['kind'] in ('person','portrait','reference_character') for p in value['parts'])
    if heads > 3:
        raise ValueError('Scena obsluguje maksymalnie 3 szczegolowe postacie. Zbuduj grupe raz; osobne warianty wymagaja kolejnych zlecen, bez duplikowania grupy.')
    allowance=max(1,heads)
    vertex_limit=(320000 if heads else 250000)*allowance
    triangle_limit=(640000 if heads else 500000)*allowance
    if vertices > vertex_limit or triangles > triangle_limit or objects > 256:
        raise ValueError('Plan przekracza budzet sceny: do 320000 wierzcholkow i 640000 trojkatow na postac, maksymalnie 3 postacie. Zachowaj twarze i dlonie; uprosc tlo i usun zbedne kopie.')
    enforce_portrait_floor(value)
    return value


def human_prompt(prompt):
    text=''.join(c for c in unicodedata.normalize('NFKD',(prompt or '').lower()) if not unicodedata.combining(c)).replace('ł','l')
    text=re.split(r'\b(?:dla|for)\b',text,maxsplit=1)[0]
    return bool(re.search(r'\b(kobiet\w*|dziewczyn\w*|mezczyzn\w*|chlopak\w*|czlowiek\w*|wokalist\w*|raper\w*|modelk\w*|portret\w*|woman|girl|man|human|person|portrait|cardi)\b',text))


def enforce_portrait_floor(scene, prompt=None):
    parts=scene['parts'];people=[p for p in parts if p['kind'] in ('person','reference_character')];heads=[p for p in parts if p['kind']=='portrait'];hands=[p for p in parts if p['kind']=='anatomical_hand']
    required=human_prompt(prompt) or scene['subject_type'] in ('person','portrait') or bool(people or heads or hands)
    if not required:return
    if not people and not heads:raise ValueError('Standard postaci: uzyj person albo portrait i anatomical_hand. Twarz z prostych bryl jest odrzucona.')
    if not people and scene['subject_type']!='portrait' and (len(hands)!=2*len(heads) or sum(p['side']=='left' for p in hands)!=len(heads)):
        raise ValueError('Standard postaci: pelna postac wymaga jednej lewej i jednej prawej anatomicznej dloni na kazda twarz.')
    for p in parts:
        if p['kind'] in ('person','portrait','anatomical_hand','reference_character'):continue
        if re.search(r'\b(face|nose|lips?|eyes?|fingers?|twarz|nos|usta|palce)\b',p['name'].lower()):
            raise ValueError('Standard postaci: rysy twarzy i palce musza byc czescia anatomii, nie dodatkowymi prostymi brylami.')


def apply_person_intent(scene, prompt):
    """Preserve explicit single-subject requirements after the AI plan is validated.

    This does not reconstruct identity. Mixed-person scenes remain planner-owned.
    A known subject resolves presentation only, never invents facial geometry.
    """
    people=[p for p in scene['parts'] if p['kind']=='person']
    if len(people)!=1 or not prompt:return scene
    text=''.join(c for c in unicodedata.normalize('NFKD',prompt.lower()) if not unicodedata.combining(c)).replace('ł','l')
    p=people[0]
    female=bool(re.search(r'\b(kobiet\w*|kobieca|kobiecej|wokalistk\w*|raperk\w*|dziewczyn\w*|woman|female|feminine)\b',text))
    male=bool(re.search(r'\b(mezczyzn\w*|meska|meskiej|chlopak\w*|man|male|masculine)\b',text))
    # Cardi B is an adult woman; the prior generic rapper default contradicted her.
    known_woman=bool(re.search(r'\bcardi\s*b\b',text))
    requested='feminine' if (female or known_woman) and not male else 'masculine' if male and not female else None
    if requested:
        previous=p['presentation'];p['presentation']=requested
        if previous!=requested and requested=='feminine' and not re.search(r'\b(krotk\w*|short|buzz|bald|lys\w*)\b',text):
            p['hair_style']='shoulder_length'
    if re.search(r'\b(curvy|hourglass|klepsydr\w*|kragl\w*|pelniejsz\w*|szerokie biodra)\b',text):p['body_shape']='curvy'
    if re.search(r'\b(dopasowan\w*|obcisl\w*|fitted|close-fitting)\b',text):p['clothing_fit']='fitted'
    elif re.search(r'\b(oversiz\w*|luzn\w*|loose)\b',text):p['clothing_fit']='oversized'
    return validate_scene(scene)


def load_scene_json(text):
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 256000:
        raise ValueError('Oczekiwano kompletnego planu JSON do 256 kB.')
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('Powtorzone pole JSON: ' + k)
            result[k] = v
        return result
    return json.loads(text, object_pairs_hook=unique)


def parse_scene(text, prompt=None):
    scene=apply_person_intent(validate_scene(load_scene_json(text)),prompt)
    enforce_portrait_floor(scene,prompt)
    return scene
