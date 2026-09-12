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


def hair_lock(name,head,points,material,width=.012,depth=.010,wave=.012,
              turns=2.0,seed=0,steps=80,sides=12):
    """World-space guide, scalp object, Blender material -> one UV mesh object.

    Width/depth are radii in scene units. Only the root is snapped to the scalp;
    the remaining shape follows the supplied guide with tapered spatial waves.
    Crown clearance is corrected locally without flattening the whole lock.
    """
    if head.type!='MESH' or len(head.data.polygons)==0:
        raise ValueError('hair_lock wymaga rzeczywistej siatki glowy.')
    if not 3<=len(points)<=32:raise ValueError('hair_lock: 3–32 punkty prowadnicy.')
    if not all(math.isfinite(v) for v in (width,depth,wave,turns)) or not (0<width<=1 and 0<depth<=1 and 0<=wave<=1 and 0<=turns<=12):
        raise ValueError('hair_lock: nieprawidlowe wymiary pasma.')
    steps=max(16,min(160,int(steps)));sides=max(8,min(20,int(sides)))
    guide=[Vector(p) for p in points]
    if any(not all(math.isfinite(v) for v in p) for p in guide):
        raise ValueError('hair_lock: nieprawidlowy punkt prowadnicy.')
    tree=scalp_tree(head)
    root,normal,_,_=tree.find_nearest(guide[0])
    if root is None:raise ValueError('hair_lock: nie znaleziono skory glowy.')
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
        if tangent.length<1e-8:raise ValueError('hair_lock: powtarzajace sie punkty.')
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
    obj['hair_volume_closed']=True;obj['hair_guide_inferred']=True
    return obj
