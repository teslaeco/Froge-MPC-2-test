"""Editable, closed hair volumes fitted to actual scalp geometry.

This helper supplies geometry, not automatic hairstyle reconstruction. The agent
must author reference-specific guide curves and inspect all exported views.
"""
import math
import random
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def scalp_tree(head):
    evaluated=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return BVHTree.FromPolygons(
        [evaluated.matrix_world@v.co for v in evaluated.data.vertices],
        [tuple(p.vertices) for p in evaluated.data.polygons],all_triangles=False)


def hair_root_attachment_evidence(hair, head, root_ring_size=None, root_radius=None):
    """Return structural scalp-attachment evidence for a rooted hair mesh.

    This is deliberately not a visual-likeness score.  It measures the first
    vertex ring that ``hair_lock`` creates and asks whether that ring remains
    geometrically close to the evaluated scalp after object transforms.
    ``passed`` is only true when both the ring centre and at least one ring
    vertex are close enough to intersect/meet the scalp envelope.
    """
    if hair.type!='MESH' or head.type!='MESH':
        raise ValueError('Hair root attachment requires mesh hair and head objects.')
    ring_size=int(root_ring_size or hair.get('hair_root_ring_size',0))
    radius=float(root_radius or hair.get('hair_root_radius',0.0))
    if ring_size<3 or ring_size>len(hair.data.vertices):
        raise ValueError('Hair root attachment requires a valid first-ring size.')
    if not math.isfinite(radius) or radius<=0:
        raise ValueError('Hair root attachment requires a positive finite root radius.')
    tree=scalp_tree(head)
    ring=[hair.matrix_world@hair.data.vertices[i].co for i in range(ring_size)]
    centre=sum(ring,Vector())/len(ring)
    centre_hit,_,_,centre_gap=tree.find_nearest(centre)
    distances=[]
    for point in ring:
        hit,_,_,distance=tree.find_nearest(point)
        if hit is None or distance is None or not math.isfinite(distance):
            raise ValueError('Hair root attachment could not measure the scalp distance.')
        distances.append(float(distance))
    if centre_hit is None or centre_gap is None or not math.isfinite(centre_gap):
        raise ValueError('Hair root attachment could not locate the scalp surface.')
    centre_limit=radius*.25
    ring_limit=radius*.35
    minimum=min(distances)
    return {
        'assessed':True,
        'metric':'root_ring_to_evaluated_scalp_distance',
        'root_ring_vertices':ring_size,
        'root_radius':radius,
        'root_centre_gap':float(centre_gap),
        'root_centre_limit':centre_limit,
        'root_ring_min_gap':minimum,
        'root_ring_min_limit':ring_limit,
        'root_ring_max_gap':max(distances),
        'passed':float(centre_gap)<=centre_limit and minimum<=ring_limit,
        'likeness_assessed':False,
    }


def hair_lock(name,head,points,material,width=.012,depth=.010,wave=.012,
              turns=2.0,seed=0,steps=80,sides=12):
    """World-space guide, scalp object, Blender material -> one UV mesh object.

    Width/depth are radii in scene units. Only the root is snapped to the scalp;
    the remaining shape follows the supplied guide with tapered spatial waves.
    Crown clearance is corrected locally without flattening the whole lock.
    """
    if head.type!='MESH' or len(head.data.polygons)==0:
        raise ValueError('hair_lock requires a real head mesh.')
    if not 3<=len(points)<=32:raise ValueError('hair_lock requires 3–32 guide points.')
    if not all(math.isfinite(v) for v in (width,depth,wave,turns)) or not (0<width<=1 and 0<depth<=1 and 0<=wave<=1 and 0<=turns<=12):
        raise ValueError('hair_lock received invalid lock dimensions.')
    steps=max(16,min(160,int(steps)));sides=max(8,min(20,int(sides)))
    guide=[Vector(p) for p in points]
    if any(not all(math.isfinite(v) for v in p) for p in guide):
        raise ValueError('hair_lock received an invalid guide point.')
    tree=scalp_tree(head)
    root,normal,_,_=tree.find_nearest(guide[0])
    if root is None:raise ValueError('hair_lock could not locate the scalp surface.')
    # Slight overlap buries the root in the scalp; no floating cap.
    guide[0]=root+normal*min(width,depth)*.08
    rng=random.Random(seed);phase=rng.uniform(0,math.tau)
    centres=[];radii=[]
    for i in range(steps+1):
        t=i/steps;q=t*(len(guide)-1);k=min(len(guide)-2,int(q));u=q-k
        a,b,c,d=(guide[max(0,k-1)],guide[k],guide[k+1],guide[min(len(guide)-1,k+2)])
        point=.5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
        envelope=math.sin(math.pi*t)**.7
        point+=Vector((wave*math.sin(math.tau*turns*t+phase),
                       wave*.70*math.cos(math.tau*turns*t+phase),0))*envelope
        taper=.22+.78*math.sin(math.pi*.5*min(1,t/.35))**.5
        taper*=max(.018,(1-t)**.40)
        if i and t<.40:
            hit,n,_,distance=tree.find_nearest(point)
            clearance=max(width,depth)*taper*.78
            if hit is not None and (point-hit).dot(n)<clearance:
                point=hit+n*clearance
        centres.append(point);radii.append(taper)
    vertices=[];faces=[];uvs=[];axis=None
    for i,p in enumerate(centres):
        tangent=centres[min(i+1,steps)]-centres[max(i-1,0)]
        if tangent.length<1e-8:raise ValueError('hair_lock contains repeated guide points.')
        tangent.normalize()
        if axis is None:
            axis=tangent.cross(Vector((0,1,0)))
            if axis.length<1e-5:axis=tangent.cross(Vector((1,0,0)))
        axis=axis-tangent*axis.dot(tangent)
        if axis.length<1e-5:axis=tangent.orthogonal()
        axis.normalize();other=tangent.cross(axis).normalized()
        for j in range(sides):
            angle=j*math.tau/sides
            ridge=1+.035*math.cos(5*angle+i/steps)
            vertices.append(tuple(p+radii[i]*(axis*width*math.cos(angle)*ridge+other*depth*math.sin(angle))))
            uvs.append((j/sides,i/steps))
            if i:
                a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides
                c=i*sides+(j+1)%sides;d=i*sides+j
                faces.append((a,b,c,d))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(steps*sides+j for j in range(sides)))
    mesh=bpy.data.meshes.new(str(name)+' mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(str(name),mesh);bpy.context.collection.objects.link(obj)
    if material:mesh.materials.append(material)
    layer=mesh.uv_layers.new(name='HairFlow')
    for polygon in mesh.polygons:
        polygon.use_smooth=True
        for index in polygon.loop_indices:layer.data[index].uv=uvs[mesh.loops[index].vertex_index]
    obj['hair_root_world']=list(root);obj['hair_root_geometry_fitted']=True
    obj['hair_root_ring_size']=sides;obj['hair_root_radius']=max(width,depth)
    obj['hair_volume_closed']=True;obj['hair_guide_inferred']=True
    return obj
