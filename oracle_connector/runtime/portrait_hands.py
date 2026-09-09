"""Connected five-finger hands and curved nail plates from bundled CC0 anatomy."""
import math
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
import anatomy


def build_hand(p, skin, nail, mesh_object):
    if nail is skin:
        import bpy
        name=skin.name+'-natural-nails';existing=bpy.data.materials.get(name)
        if existing is None:
            existing=skin.copy();existing.name=name
            shader=existing.node_tree.nodes.get('Principled BSDF')
            for link in list(shader.inputs['Base Color'].links):existing.node_tree.links.remove(link)
            shader.inputs['Base Color'].default_value=tuple(min(1,v*1.1) for v in skin.diffuse_color[:3])+(1,)
            shader.inputs['Roughness'].default_value=.35
        nail=existing
    side = 1 if p['side'] == 'left' else -1
    prefix = 'l' if side == 1 else 'r'
    presentation = p['presentation']
    obj = anatomy.base_part(p['side'], presentation, skin, mesh_object)
    obj.name = 'anatomical-hand-' + p['side']
    source = anatomy.landmark(prefix+'-hand', presentation)
    joints = [[anatomy.landmark(prefix+f'-finger-{k}-{j}', presentation)
               for j in range(1, 5)] for k in range(1, 6)]
    axis = (joints[2][0]-source).normalized()
    across = (joints[1][0]-joints[4][0]).normalized()
    dorsal = -axis.cross(across).normalized()*side
    anatomy.trim(obj, source-axis*.026, axis)
    surface = BVHTree.FromPolygons([v.co for v in obj.data.vertices], [f.vertices[:] for f in obj.data.polygons])
    target_axis = Vector(p['direction']).normalized()
    rotation = axis.rotation_difference(target_axis)
    current = rotation@dorsal
    current = (current-target_axis*current.dot(target_axis)).normalized()
    target = Vector(p['palm_normal']); target -= target_axis*target.dot(target_axis)
    if target.length < .05:raise ValueError('Hand normal must be transverse to its direction')
    target.normalize()
    angle = math.atan2(target_axis.dot(current.cross(target)), current.dot(target))
    rotation = Quaternion(target_axis, angle)@rotation
    wrist = Vector(p['wrist']); scale = p.get('scale', 1.); curl = p.get('curl', .15)
    roots = [j[0] for j in joints]
    axes = [(j[3]-j[0]).normalized() for j in joints]
    lengths = [(j[3]-j[0]).length for j in joints]

    def pose(point, finger=None):
        point = Vector(point); candidates = []
        for k in range(5):
            delta = point-roots[k]; along = delta.dot(axes[k])
            distance = (delta-axes[k]*max(0., min(lengths[k], along))).length
            candidates.append((distance, k, along))
        distance, k, along = min(candidates) if finger is None else candidates[finger]
        if along > 0 and distance < (.025 if k == 0 else .018):
            bend = curl*(.4 if k == 0 else 1.+.08*(k-2))
            if bend > 1e-5:
                radius = lengths[k]/bend; theta = min(along/radius, bend*1.15)
                inward = -dorsal; inward = (inward-axes[k]*inward.dot(axes[k])).normalized()
                point += axes[k]*(radius*math.sin(theta)-along) + inward*(radius*(1-math.cos(theta)))
        return wrist+rotation@((point-source)*scale)

    plates = []
    for k, js in enumerate(joints):
        along = (js[3]-js[2]).normalized()
        normal = (dorsal-along*dorsal.dot(along)).normalized(); transverse = along.cross(normal).normalized()
        center = js[2].lerp(js[3], .66)
        center_hit, _, _, _ = surface.ray_cast(center+normal*.04, -normal, .08)
        if center_hit is None:raise ValueError('Nail could not be fitted to its anatomical finger')
        half_length = min(.013, (js[3]-js[2]).length*.43)+p.get('nail_length', .001)*.5
        half_width = [.0057, .0048, .0051, .0047, .0038][k]
        vertices = []; faces = []; rings = 12; sides = 20
        for layer in (0, 1):
            for ring in range(rings+1):
                t = -1+2*ring/rings; width = half_width*max(.015, (1-t*t)**.45)*(1-.12*max(t, 0))
                for j in range(sides+1):
                    u = -1+2*j/sides; q = center+along*(t*half_length)+transverse*(u*width)
                    q = center_hit+along*(t*half_length)+transverse*(u*width)
                    q += normal*(.00020+layer*.00032+.0007*(1-u*u)-.00025*t*t)
                    vertices.append(tuple(pose(q, k)))
        count = (rings+1)*(sides+1)
        for r in range(rings):
            for j in range(sides):
                a = r*(sides+1)+j; b = a+sides+1
                faces.extend([(a, b, b+1, a+1), (count+a, count+a+1, count+b+1, count+b)])
        border = list(range(sides+1))+[r*(sides+1)+sides for r in range(1,rings+1)]+[rings*(sides+1)+j for j in range(sides-1,-1,-1)]+[r*(sides+1) for r in range(rings-1,0,-1)]
        for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+count,a+count))
        plate = mesh_object(f'anatomical-nail-{p["side"]}-{k+1}', vertices, faces, nail)
        plate['anatomical_nail'] = True; plate['finger_index'] = k+1
        for f in plate.data.polygons:f.use_smooth=True
        plates.append(plate)
    for vertex in obj.data.vertices:vertex.co=pose(vertex.co)
    anatomy.subdivide(obj, 1)
    obj['anatomical_hand'] = True; obj['finger_count'] = 5; obj['quality_revision'] = 1
    return [obj, *plates]
