"""Trusted Blender implementations of the data-only scene operations."""
import math
import random

import bpy
from mathutils import Vector
from detailed_geometry import loft, revolve, person, extrusion


def build_scene(scene, make_material, mesh_object, tube, ellipsoid, join_meshes, reference_folder=None):
    from portrait import build_portrait
    from portrait_hands import build_hand
    from photo_face import load_fit
    import json
    from reference_quality import requested_edge
    bpy.context.scene['material_max_edge'] = requested_edge(reference_folder) if reference_folder else 2048
    face_fit, fit_report = load_fit(reference_folder, scene['parts'])
    bpy.context.scene['photo_face_fit'] = json.dumps(fit_report)
    bpy.context.scene['expected_heads']=sum(p['kind'] in ('person','portrait','reference_character') for p in scene['parts'])
    bpy.context.scene['anatomy_intent']=json.dumps({p['name']:p.get('eye_states',
        {'left':'present','right':'present','evidence':''}) for p in scene['parts']
        if p['kind'] in ('person','portrait','reference_character')})
    bpy.context.scene['expected_hands']=sum(2 if p['kind'] in ('person','reference_character') else 1 if p['kind']=='anatomical_hand' else 0 for p in scene['parts'])
    bpy.context.scene['reference_couture']=any(p['kind']=='reference_character' for p in scene['parts'])
    materials, objects = {}, {}
    for m in scene['materials']:
        material = make_material(m['name'], m['rgb'], m['pattern'], m['roughness'], m['metallic'])
        shader = material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Emission Color'].default_value = (*m['rgb'], 1)
        shader.inputs['Emission Strength'].default_value = m['emission']
        materials[m['name']] = material

    def oak(p):
        rng = random.Random(p['seed'])
        base = Vector(p['center'])
        h, cr, tr = p['height'], p['crown_radius'], p['trunk_radius']
        bark, leaves = materials[p['material']], materials[p['leaf_material']]
        wood = []
        def branch(label, points, radii, sides=10):
            obj = tube(label, [tuple(base + Vector(v)) for v in points], radii, bark, sides)
            wood.append(obj)
        trunk = [(0.08*h*math.sin(i*.31)*(i/8), .035*h*math.sin(i*.9), .75*h*i/8) for i in range(9)]
        branch('trunk', trunk, [tr*(1.4-.13*i) for i in range(9)], 20)
        for i in range(7):
            angle = i*math.tau/7
            branch('root', [(math.cos(angle)*tr*.4, math.sin(angle)*tr*.4, tr*1.6),
                            (math.cos(angle)*tr*1.8, math.sin(angle)*tr*1.8, tr*.24),
                            (math.cos(angle)*tr*3, math.sin(angle)*tr*3, .005)], [tr*.4, tr*.25, tr*.025])
        clusters = []
        for i in range(12):
            angle = i*2.3999632297
            start = Vector(trunk[3 + i % 3])
            tip = Vector((cr*.76*math.cos(angle), cr*.76*math.sin(angle), h*(.58+.028*i)))
            mid = start.lerp(tip, .5) + Vector((0, 0, -.06*h))
            branch('bough', [start, mid, tip], [tr*.43, tr*.25, tr*.065], 12)
            for j in range(4):
                a = angle + (j-1.5)*.47
                end = tip + Vector((cr*.20*math.cos(a), cr*.20*math.sin(a), h*(j-1.5)*.018))
                bend = tip.lerp(end, .5) + Vector((0, 0, .025*h))
                branch('twig', [tip, bend, end], [tr*.062, tr*.025, tr*.005], 6)
                clusters.append((end, cr*.26))
        clusters += [(Vector((.04*h, 0, h*.9)), cr*.28), (Vector((0,0,h*.69)), cr*.45)]
        verts, faces, coordinates = [], [], []
        # Lobed oak leaf outline. Each leaf is explicit geometry with its own UVs.
        outline = [(0, 0)]
        for sign, steps in [(1, range(1, 10)), (-1, range(9, 0, -1))]:
            if sign == -1:
                outline.append((1, 0))
            for k in steps:
                t = k/10
                width = math.sin(math.pi*t)*(.34+.12*math.cos(t*10*math.pi))
                outline.append((t, sign*width))
        for center, spread in clusters:
            for _ in range(50):
                direction = Vector((rng.uniform(-1,1), rng.uniform(-1,1), rng.uniform(-.5,.7))).normalized()
                position = center + direction * spread * rng.random()**(1/3)
                position.z = min(h*.99, max(h*.4, position.z))
                axis = Vector((rng.uniform(-1,1), rng.uniform(-1,1), rng.uniform(-.6,.8))).normalized()
                other = axis.cross(Vector((0,0,1)))
                if other.length < .01:
                    other = Vector((1,0,0))
                other.normalize()
                length = cr*rng.uniform(.13,.20)
                start = len(verts)
                verts.append(tuple(base+position+axis*(length*.5)+Vector((0,0,length*.045))))
                coordinates.append((.5,.5))
                for u, v in outline:
                    verts.append(tuple(base+position+axis*(u*length)+other*(v*length)))
                    coordinates.append((v+.5,u))
                for j in range(len(outline)):
                    faces.append((start, start+1+j, start+1+(j+1)%len(outline)))
        crown = mesh_object(p['name']+'-leaves', verts, faces, leaves)
        uv = crown.data.uv_layers.new(name='UVMap')
        for loop in crown.data.loops:
            uv.data[loop.index].uv = coordinates[loop.vertex_index]
        trunk_obj = join_meshes(wood, p['name']+'-wood')
        return [trunk_obj, crown]

    for p in scene['parts']:
        if face_fit is not None and p['name'] == face_fit.part_name:
            p = {**p, '_photo_fit': face_fit}
        kind, name = p['kind'], p['name']
        material = materials.get(p.get('material'))
        if kind=='reference_character':
            from couture import reference_character
            objects[name]=reference_character(p,materials,mesh_object,tube,ellipsoid,join_meshes)
            continue
        if kind=='rotor':
            from couture import rotor
            objects[name]=[rotor(p,material,materials[p['accent_material']],mesh_object)]
            continue
        if kind=='radial_copies':
            from couture_geometry import radial_positions
            source=objects[p['source']][0];copies=[]
            for i,center in enumerate(radial_positions(p['count'],p['radius'],p['start_angle'],p['arc_angle'],p['center'])):
                obj=source.copy();obj.name=name+'-%d'%i;obj.location=center
                bpy.context.collection.objects.link(obj);copies.append(obj)
            objects[name]=copies
            continue
        if kind=='portrait':
            objects[name]=build_portrait(p,materials,mesh_object,ellipsoid)
            continue
        if kind=='anatomical_hand':
            objects[name]=build_hand(p,materials[p['skin_material']],materials[p['nail_material']],mesh_object)
            continue
        if kind == 'oak':
            objects[name] = oak(p)
            continue
        if kind == 'person':
            objects[name] = person(p, materials, mesh_object, tube, ellipsoid, join_meshes)
            continue
        if kind == 'garland':
            base = Vector(p['center'])
            def point(t):
                angle = t*p['turns']*math.tau
                radius = p['radius']*(1-.35*t)
                return base + Vector((radius*math.cos(angle), radius*math.sin(angle), p['bottom']+(p['top']-p['bottom'])*t))
            points = [tuple(point(i/159)) for i in range(160)]
            wire = tube(name+'-wire', points, [max(.001, p['bulb_radius']*.15)]*160, material, 8)
            bulbs = []
            for i in range(p['bulbs']):
                center = point((i+.5)/p['bulbs'])
                center.z -= p['bulb_radius']*.8
                bulbs.append(ellipsoid(name+'-bulb-%02d'%(i+1), center,
                                       (p['bulb_radius'],)*2+(p['bulb_radius']*1.35,), materials[p['bulb_material']], subdivisions=3))
            light = join_meshes(bulbs, name+'-bulbs')
            light['bulb_count'] = p['bulbs']
            objects[name] = [wire, light]
            continue
        if kind == 'ellipsoid':
            obj = ellipsoid(name, p['center'], p['radii'], material)
        elif kind == 'box':
            bpy.ops.mesh.primitive_cube_add(size=1, location=p['center'])
            obj = bpy.context.object
            obj.name, obj.scale, obj.rotation_euler = name, p['size'], p['rotation']
            obj.data.materials.append(material)
        elif kind == 'tube':
            obj = tube(name, p['points'], p['radii'], material, p['sides'])
        elif kind in ('surface_grid','contour_loft'):
            from freeform_geometry import build
            obj = build(p, material, mesh_object)
        elif kind == 'mesh':
            obj = mesh_object(name, p['vertices'], p['faces'], material)
        elif kind == 'loft':
            obj = loft(name, p['sections'], p['sides'], material, mesh_object)
        elif kind == 'extrusion':
            obj = extrusion(p, material, materials[p['cap_material']], mesh_object)
        elif kind == 'lathe':
            obj = revolve(name, p['profile'], p['center'], p['sides'], material, mesh_object)
        elif kind == 'copies':
            source = objects[p['source']][0]
            copies = []
            for i, offset in enumerate(p['offsets']):
                obj = source.copy()
                obj.name = name+'-%d'%i
                obj.location = source.location + Vector(offset)
                bpy.context.collection.objects.link(obj)
                copies.append(obj)
            objects[name] = copies
            continue
        else:
            raise ValueError('Unsupported scene part')
        objects[name] = [obj]
    if face_fit is not None:
        fit_report.update(face_fit.report)
        bpy.context.scene['photo_face_fit']=json.dumps(fit_report)
    from photo_projection import apply_projections
    projection_report=apply_projections(scene.get('reference_views',[]),objects,reference_folder)
    bpy.context.scene['photo_projection']=json.dumps(projection_report)
    return objects
