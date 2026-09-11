"""Long straight centre-part hair with a recessed scalp channel and grouped strands.

Authored reference styling, not an identity reconstruction. Front is -Y.
Portable normal texture and mesh strands; build_bob retains its existing API.
"""
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def build_bob(head_obj, mesh_object, sampler=None, supplied_material=None):
    vv = [v.co for v in head_obj.data.vertices]
    crown = max(v.z for v in vv)
    dz = crown - 1.8
    skull = [v for v in vv if v.z > 1.72 + dz]
    width = max(abs(v.x) for v in skull) if skull else .080
    rx = max(.090, min(.106, width + .009))
    cy, ry = -.047, .111
    top, equator = 1.806 + dz, 1.690 + dz
    n, rows = 160, 32
    skull_surface = BVHTree.FromPolygons(vv, [p.vertices[:] for p in head_obj.data.polygons])
    verts, faces = [], []

    def smooth(t):
        t = max(0., min(1., t))
        return t * t * (3. - 2. * t)

    def part_x(y):
        return .0003 * math.sin((y + .14) * 8.)

    def endpoint(theta):
        a = abs(theta)
        line = 1.761 - .028 * min(1., (a / .58)**2)
        line += .00060*math.sin(theta*79.) + .00028*math.sin(theta*157.+.4)
        transition = smooth((a - .50) / .48)
        # Long, graduated tips end at the upper hip, retaining natural taper.
        hem = 1.037 + .038 * math.cos(theta * 2.)
        hem += .009 * math.sin(theta * 19. + .5) + .006 * math.sin(theta * 43.) + .004*math.sin(theta*71.)
        return line * (1 - transition) + hem * transition + dz

    def point(theta, s):
        lower = endpoint(theta)
        z = top + (lower - top) * s
        up = (z - equator) / (top - equator)
        if up > 0:
            radial = math.sqrt(max(0., 1. - up * up))
        else:
            down = (equator - z) / max(.01, equator - lower)
            radial = 1. + .042 * math.sin(math.pi * down * .82) - .075 * down ** 5
        angle = theta + .065 * math.sin(theta) * smooth(s)
        flow = angle * 106. + 2.4 * math.sin(s * 2.7 + angle)
        relief = (.00012 * math.sin(flow) + .00020 * math.sin(angle * 29. + 1.7 * s))
        relief *= smooth(s * 7.) * (.55 + .45 * smooth((equator + .06 - z) / .09))
        p = Vector(((rx * radial + relief) * math.sin(angle) + .000 * (1. - s) ** 2,
                    cy - (ry * radial + relief) * math.cos(angle) + .003 * (1. - s) ** 2,
                    z))
        # Two long front curtains rest in front of the shoulders and dress.
        lower = smooth((1.66 + dz - z) / .23)
        front_curtain = 1. - smooth((abs(theta) - 1.57) / .53)
        fullness = .032 * math.exp(-((z - 1.34 - dz) / .23)**2) + .014 * lower
        p.x += math.sin(angle) * fullness * lower
        p.y -= .151 * lower * front_curtain
        p.y += .020 * lower * (1. - front_curtain)
        p.x += .0012 * math.sin((1.7-z)*13.+theta*3.) * lower
        # Clear the ear cartilage without changing the front hairline.
        p.x += math.sin(angle)*.008*math.exp(-((z-1.665-dz)/.051)**2)*abs(math.sin(angle))**8

        if z > 1.545 + dz:
            origin = Vector((0, cy, equator - .015))
            direction = (p - origin).normalized()
            hit, _, _, _ = skull_surface.ray_cast(origin, direction)
            if hit is not None and (hit - origin).length + .003 > (p - origin).length:
                p = hit + direction * .003
        # The export contains a physical depression beneath the scalp ribbon.
        if p.z > 1.752 + dz and -.158 < p.y < -.018:
            channel = math.exp(-((p.x - part_x(p.y)) / .0037) ** 2)
            p.z -= .0027 * channel * smooth((p.z - 1.752 - dz) / .012)
        return tuple(p)

    if sampler is not None:
        sampler['point'] = point
    verts.append((.000, cy + .003, top - .001))
    for j in range(1, rows + 1):
        s = (j / rows) ** 1.65
        for i in range(n):
            verts.append(point(-math.pi + 2 * math.pi * i / n, s))
    for i in range(n):
        faces.append((0, 1 + (i + 1) % n, 1 + i))
    for j in range(rows - 1):
        start, nxt = 1 + j * n, 1 + (j + 1) * n
        for i in range(n):
            k = (i + 1) % n
            faces.append((start + i, start + k, nxt + k, nxt + i))

    def material(name, color, roughness):
        if supplied_material is not None:return supplied_material
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1)
        m.use_nodes = True
        shader = m.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color, 1)
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Metallic'].default_value = 0.
        shader.inputs['IOR'].default_value = 1.28
        if 'Specular IOR Level' in shader.inputs:
            shader.inputs['Specular IOR Level'].default_value = .07
        if 'Coat Weight' in shader.inputs:
            shader.inputs['Coat Weight'].default_value = 0.
        return m

    palettes = [material('Black hair strand group %d' % i, color, roughness)
                for i, (color, roughness) in enumerate([
                    ((.0032, .0030, .0033), .68),
                    ((.0048, .0044, .0048), .63),
                    ((.0026, .0024, .0027), .73)])]
    bob = mesh_object('long-centre-part-black-hair', verts, faces, palettes[0])
    # UV follows each root-to-tip flow line; normal texture survives GLB export.
    uv=bob.data.uv_layers.new(name='HairFlow')
    for poly in bob.data.polygons:
        indices=list(poly.vertices)
        us=[((i-1)%n)/n for i in indices if i>0]
        seam=(max(us)-min(us)>.5) if us else False
        for loop,idx in zip(poly.loop_indices,indices):
            if idx==0:
                u=sum(q+1 if seam and q<.5 else q for q in us)/len(us);v=0.
            else:
                u=((idx-1)%n)/n
                if seam and u<.5:u+=1
                v=((idx-1)//n+1)/rows
            uv.data[loop].uv=(u,1-v)
    from portrait_hair_surface import add_strand_normal
    add_strand_normal(bob,palettes)
    for m in palettes[1:]:
        bob.data.materials.append(m)
    for f in bob.data.polygons:
        centre = sum((bob.data.vertices[i].co for i in f.vertices), Vector()) / len(f.vertices)
        theta = math.atan2(centre.x, cy - centre.y)
        group = math.sin(theta * 17. + 1.7 * (top - centre.z) / .25)
        f.material_index = 0
        f.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(bob.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(bob.data)
    bm.free()
    bpy.context.view_layer.objects.active = bob
    subdiv = bob.modifiers.new('Soft grouped strand contour', 'SUBSURF')
    subdiv.levels = subdiv.render_levels = 1
    bpy.ops.object.modifier_apply(modifier=subdiv.name)
    # Subdivision can shrink a correctly ray-fitted shell through the cheek.
    # Give the frontal curtain 2 mm of clearance against the final skin mesh.
    for vertex in bob.data.vertices:
        p=vertex.co
        if 1.58+dz<p.z<1.725+dz and .045<abs(p.x)<.095 and p.y<-.10:
            hit,normal,_,_=skull_surface.ray_cast(Vector((p.x,-.32,p.z)),Vector((0,1,0)))
            if hit is not None and p.y>hit.y-.0025:
                p.y=hit.y-.0025
    bob.data.update()
    solid = bob.modifiers.new('Fine tapered long hair tips', 'SOLIDIFY')
    solid.thickness = .0014
    solid.use_rim_only = True
    solid.offset = -1.
    bpy.ops.object.modifier_apply(modifier=solid.name)

    # A narrow skin ribbon is projected onto the recessed surface. It remains
    # visible in GLB viewers without displacement, alpha, or texture support.
    surface = BVHTree.FromPolygons([v.co for v in bob.data.vertices],
                                  [p.vertices[:] for p in bob.data.polygons])
    scalp_vertices, scalp_faces = [], []
    for j in range(40):
        t = j / 39.
        y = -.153 + .128 * t
        half_width = .00072 * (.55 + .45 * math.sin(math.pi * t))
        pair = []
        for side in (-1, 1):
            x = part_x(y) + side * half_width
            hit, _, _, _ = surface.ray_cast(Vector((x, y, top + .06)), Vector((0, 0, -1)))
            if hit is not None and hit.z > 1.755 + dz:
                pair.append((hit.x, hit.y, hit.z + .00022))
        if len(pair) == 2:
            start = len(scalp_vertices)
            scalp_vertices.extend(pair)
            if start:
                scalp_faces.append((start - 2, start - 1, start + 1, start))
    objects = [bob]
    # Sparse actual filaments break the long silhouette and soften the hairline.
    # Four-sided microtubes taper to fine points; no curves/alpha shaders required.
    strand_verts=[];strand_faces=[]
    filament_mat=material('Fine black silhouette filaments',(.0028,.0025,.0027),.54)
    def filament(theta,start,end,count,radius,offset):
        chain=[]
        for j in range(count):
            t=j/(count-1);q=start+(end-start)*t
            a=theta+.003*math.sin(t*6.2+theta*9.)
            p=Vector(point(a,q))
            near,normal,_,_=surface.find_nearest(p)
            if normal is None:normal=Vector((math.sin(a),-math.cos(a),.15)).normalized()
            radial=Vector((p.x,p.y-cy,0))
            if normal.dot(radial)<0:normal=-normal
            p+=normal*(offset*(.30+.70*math.sin(math.pi*t))+.00015)
            chain.append((p,normal))
        base=len(strand_verts)
        for j,(p,normal) in enumerate(chain):
            tangent=(chain[min(j+1,count-1)][0]-chain[max(0,j-1)][0]).normalized()
            across=tangent.cross(normal).normalized()
            if across.length<.1:across=Vector((1,0,0))
            other=tangent.cross(across).normalized()
            t=j/(count-1);r=radius*(.25+.75*math.sin(math.pi*t)**.45)*(1-.92*t**8)
            for k in range(4):strand_verts.append(tuple(p+r*(math.cos(k*math.pi/2)*across+math.sin(k*math.pi/2)*other)))
        for j in range(count-1):
            for k in range(4):strand_faces.append((base+j*4+k,base+j*4+(k+1)%4,base+(j+1)*4+(k+1)%4,base+(j+1)*4+k))
    for i in range(180):
        theta=-math.pi+2*math.pi*(i+.31)/180
        if abs(theta)<.55:continue
        filament(theta,.10+.04*math.sin(i*3.4),1.005+.012*(.5+.5*math.sin(i*5.3)),26,.00012,.00065)
    for i in range(36):
        theta=-.49+.98*(i+.31)/36
        if abs(theta)<.035:continue
        filament(theta,.80,1.025+.018*(.5+.5*math.sin(i*2.9)),7,.00010,.00012)
    filaments=mesh_object('fine-tapered-hair-filaments',strand_verts,strand_faces,filament_mat)
    for f in filaments.data.polygons:f.use_smooth=True
    objects.append(filaments)
    if scalp_faces:
        scalp = mesh_object('visible-centre-part-scalp', scalp_vertices, scalp_faces,
                            material('Warm scalp in hair part', (.22, .105, .057), .64))
        for f in scalp.data.polygons:
            f.use_smooth = True
        objects.append(scalp)
    bob['authored_reference'] = 'long straight black hair with recessed centre part and fine grouped strands'
    bob['hair_not_identity_claim'] = True
    return objects
