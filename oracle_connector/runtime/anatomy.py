"""Trusted adult anatomy and UVs derived from MakeHuman's CC0 system assets.

Fixed bundled data only: no model-supplied paths, downloads, code, or imports.
See assets/SOURCES.md for source URLs, licenses and preparation instructions.
"""
from functools import lru_cache
import gzip
import json
import math
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ASSETS = Path(__file__).resolve().parent / 'assets'

@lru_cache(maxsize=1)
def anatomy_data():
    return json.loads(gzip.decompress((ASSETS / 'anatomy.json.gz').read_bytes()))


def blend_shape(presentation):
    return {'masculine':0., 'androgynous':.5, 'feminine':1.}[presentation]


def landmark(name, presentation):
    data=anatomy_data()['landmarks'];t=blend_shape(presentation)
    return Vector(data['male'][name]).lerp(Vector(data['female'][name]), t)


def skin_atlas(material, presentation, eye_material):
    """Bake skin tint + eye colors into one packed, exportable 2048px atlas."""
    if material.get('anatomical_atlas'):
        return
    source='female-skin.png' if presentation=='feminine' else 'male-skin.png'
    image=bpy.data.images.load(str(ASSETS/source), check_existing=False)
    n=image.size[0];patch_size=n//8
    pixels=np.asarray(image.pixels[:], dtype=np.float32).reshape(n,n,4).copy()
    rgb=np.array(material.diffuse_color[:3], dtype=np.float32)
    valid=(pixels[:,:,0]>.15)&(pixels[:,:,1]>.08)&(pixels[:,:,0]>pixels[:,:,1]*1.12)
    median=np.maximum(np.median(pixels[:,:,:3][valid],axis=0), .1)
    pixels[:,:,:3]=np.clip(pixels[:,:,:3]*(rgb/median),0,1)
    # This lower-left square is outside every retained head/hand UV polygon.
    y,x=np.mgrid[-1:1:complex(patch_size),-1:1:complex(patch_size)];radius=np.sqrt(x*x+y*y)
    angle=np.arctan2(y,x)
    iris=np.array(eye_material.diffuse_color[:3])
    if iris.mean()>.5:iris=np.array([.15,.085,.035])
    stripes=.8+.14*np.sin(angle*71+radius*31)+.1*np.sin(angle*109-radius*43)
    patch=np.ones((patch_size,patch_size,4),dtype=np.float32)
    patch[:,:,:3]=np.array([.90,.88,.84])
    patch[:,:,:3]=np.where((radius<.43)[:,:,None],iris*stripes[:,:,None],patch[:,:,:3])
    patch[:,:,:3]=np.where(((radius>.39)&(radius<.45))[:,:,None],iris*.33,patch[:,:,:3])
    patch[:,:,:3]=np.where((radius<.18)[:,:,None],.006,patch[:,:,:3])
    pixels[:patch_size,:patch_size]=patch
    image.pixels.foreach_set(pixels.reshape(-1));image.update();image.file_format='PNG';image.pack()
    image['anatomical_atlas']=True
    nodes=material.node_tree.nodes;links=material.node_tree.links;shader=nodes.get('Principled BSDF')
    old_images=[]
    for node in list(nodes):
        if node.type=='TEX_IMAGE':
            if node.image:old_images.append(node.image)
            nodes.remove(node)
    for old in old_images:
        if old.users==0:bpy.data.images.remove(old)
    node=nodes.new('ShaderNodeTexImage');node.image=image
    links.new(node.outputs['Color'],shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value=.60
    shader.inputs['Metallic'].default_value=0
    material['anatomical_atlas']=True


def base_part(name, presentation, material, mesh_object):
    data=anatomy_data()['parts'][name];t=blend_shape(presentation)
    verts=[tuple(Vector(a).lerp(Vector(b),t)) for a,b in zip(data['shapes']['male'],data['shapes']['female'])]
    obj=mesh_object('anatomical-'+name,verts,data['faces'],material)
    layer=obj.data.uv_layers.new(name='UVMap')
    for polygon,uvs in zip(obj.data.polygons,data['uv']):
        polygon.use_smooth=True
        for loop,uv in zip(polygon.loop_indices,uvs):layer.data[loop].uv=uv
    return obj


def subdivide(obj, levels):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('anatomical-surface','SUBSURF');mod.levels=levels
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for face in obj.data.polygons:face.use_smooth=True


def trim(obj, origin, direction):
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=origin,plane_no=direction,clear_inner=True,clear_outer=False)
    boundary=[e for e in bm.edges if e.is_boundary and all(abs((v.co-origin).dot(direction))<1e-5 for v in e.verts)]
    if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()


def head(p, material, eye_material, hair_material, mesh_object, ellipsoid):
    presentation=p['presentation'];skin_atlas(material,presentation,eye_material)
    obj=base_part('head',presentation,material,mesh_object)
    trim(obj,Vector((0,0,1.465)),Vector((0,0,1)))
    # Smooth the neck flare while masking the entire anterior chin/jaw.
    def step(a,b,value):
        t=max(0.,min(1.,(value-a)/(b-a)));return t*t*(3-2*t)
    for vertex in obj.data.vertices:
        v=vertex.co
        if v.z<1.615:
            protect=step(1.535,1.555,v.z)*(1-step(-.105,-.065,v.y))
            weight=(1-step(1.570,1.615,v.z))*(1-protect)
            radial=math.sqrt((v.x/.055)**2+((v.y+.020)/.060)**2)
            if radial>1:
                scale=1-weight*(1-1/radial)
                v.x*=scale;v.y=(v.y+.020)*scale-.020
        # The hidden base sits inside the shirt; never poke through its front.
        base_weight=1-step(1.485,1.535,v.z)
        v.x*=1-.08*base_weight
        v.y=(v.y+.010)*(1-.24*base_weight)-.010
    subdivide(obj,1)
    parts=[obj]
    hair_shader=hair_material.node_tree.nodes.get('Principled BSDF')
    hair_shader.inputs['Metallic'].default_value=0
    hair_shader.inputs['Roughness'].default_value=.85
    # A separate smooth eye surface shares the packed atlas, not its skin roughness.
    eye_surface=material
    if len(bpy.data.materials)<8:
        eye_surface=material.copy();eye_surface.name='anatomical-eyes'
        eye_surface.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.22
    for side in ('l','r'):
        center=landmark(side+'-eye',presentation)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,radius=1,location=center)
        eye=bpy.context.object;eye.name='anatomical-eye-'+side;eye.scale=(.0147,.0152,.0143)
        eye.data.materials.append(eye_surface)
        uv=eye.data.uv_layers.active
        for polygon in eye.data.polygons:
            polygon.use_smooth=True
            for loop in polygon.loop_indices:
                v=eye.data.vertices[eye.data.loops[loop].vertex_index].co
                uv.data[loop].uv=((v.x*.49+.5)*.125,(v.z*.49+.5)*.125)
        parts.append(eye)
    # Thin eyebrow ribbons follow the actual brow surface; no floating tubes.
    surface=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[p.vertices[:] for p in obj.data.polygons])
    rng=np.random.default_rng(1107)
    from portrait_shape import brow_height
    for side in (-1,1):
        vertices=[];faces=[]
        eye_z=landmark(('l' if side==1 else 'r')+'-eye',presentation).z
        for i in range(150):
            t=(i+rng.random())/150
            x=side*(.012+.043*t)
            z=brow_height(t,eye_z,p.get('makeup')=='soft_glam')
            z+=rng.uniform(-1,1)*(.0030 if p.get('makeup')=='soft_glam' else .0017)*math.sin(math.pi*t)**.32*(1-.5*t)
            length=rng.uniform(.0018,.0035)*(1-.35*t)
            dx=side*length*(.20+.7*t);dz=length*(.85-.7*t)
            width=rng.uniform(.00010,.00022)*(1-.45*t)
            ids=[]
            for xx,zz in ((x-width,z),(x+width,z),(x+dx,z+dz)):
                point,normal,_,_=surface.ray_cast(Vector((xx,-.5,zz)),Vector((0,1,0)))
                if point is None:break
                ids.append(len(vertices));vertices.append(tuple(point+normal*.00035))
            if len(ids)==3:faces.append(ids)
        brow=mesh_object('eyebrow-fibres',vertices,faces,eye_material)
        for face in brow.data.polygons:face.use_smooth=True
        parts.append(brow)
    if p['headwear']=='none' and p.get('hair_style')=='bald':return parts
    buzz=p.get('hair_style')=='buzz' and p['headwear']=='none'
    if buzz:
        paint_buzz(obj,material,hair_material)
        parts.append(stubble(obj,hair_material,mesh_object))
        return parts
    # Hair and hats both follow the actual cranium, preserving the forehead.
    skull=obj.data;selected=[]
    def hairline(v):
        if p.get('hair_style')=='swept_updo':
            front=max(0,min(1,(-v.y-.015)/.11))
            # Couture reference has a side part and a soft central point, not a
            # symmetric helmet rim. Keep the bounded scalp coverage while
            # exposing one temple more strongly for the swept direction.
            side_part=.004*math.exp(-((v.x+.034)/.018)**2)*front
            opposite_sweep=.004*math.exp(-((v.x-.041)/.024)**2)*front
            centre_point=.0015*math.exp(-((v.x-.006)/.020)**2)
            # Sub-millimetre asymmetric root variation softens the perfect
            # moulded edge without cutting teeth or isolated scalp islands.
            root_variation=front*(.00045*math.sin(v.x*270+.4)+.00025*math.sin(v.x*470+1.7))
            return 1.690+.059*front-.033*min(1,(abs(v.x)/.082)**2)*front+side_part-opposite_sweep-centre_point+root_variation
        return 1.713+.036*max(0,min(1,(-v.y-.015)/.11))
    if p['headwear']=='none':
        vertices=[];faces=[]
        # Clip every intersected polygon at the hairline, avoiding a sawtooth rim.
        for face in skull.polygons:
            if abs(face.center.x)>.081 and face.center.z<(1.685 if p.get('hair_style')=='swept_updo' else 1.752):continue
            contour=[skull.vertices[i].co.copy() for i in face.vertices]
            clipped=[]
            for a,b in zip(contour,contour[1:]+contour[:1]):
                fa=a.z-hairline(a);fb=b.z-hairline(b)
                if fa>=0:clipped.append(a)
                if (fa>=0)!=(fb>=0):clipped.append(a.lerp(b,fa/(fa-fb)))
            if len(clipped)<3:continue
            face_ids=[]
            for v in clipped:
                out=(v-Vector((0,-.025,1.70))).normalized()
                groove=.00055*math.sin(math.atan2(v.y+.025,v.x)*130+v.z*35) if p.get('hair_style')=='shoulder_length' else 0
                vertices.append(tuple(v+out*(.002+groove)));face_ids.append(len(vertices)-1)
            faces.append(face_ids)
        hair=mesh_object('fitted-none',vertices,faces,hair_material)
        bm=bmesh.new();bm.from_mesh(hair.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hair.data);bm.free()

    else:
        selected=[face for face in skull.polygons if face.center.z>1.733]
        ids=sorted({i for f in selected for i in f.vertices});mapping={i:n for n,i in enumerate(ids)}
        verts=[]
        for i in ids:
            v=skull.vertices[i].co.copy();out=v-Vector((0,-.025,1.70));v+=out.normalized()*.008
            if p['headwear']=='beanie':v.z+=max(0,v.z-1.735)*.12
            verts.append(tuple(v))
        hair=mesh_object('fitted-'+p['headwear'],verts,[[mapping[i] for i in f.vertices] for f in selected],hair_material)
    for face in hair.data.polygons:face.use_smooth=True
    if p['headwear']!='none':
        bm=bmesh.new();bm.from_mesh(hair.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,1.749),plane_no=(0,0,1),clear_inner=True)
        boundary={v for edge in bm.edges if edge.is_boundary for v in edge.verts}
        for v in boundary:v.co.z=1.749
        ring=sorted([v.co.copy() for v in boundary],key=lambda v:math.atan2(v.y+.025,v.x))
        bm.to_mesh(hair.data);bm.free()
        if p['headwear']=='beanie' and ring:
            vertices=[]
            for dz in (0,.016):
                for v in ring:
                    out=Vector((v.x,v.y+.025,0)).normalized()*.003
                    vertices.append(tuple(v+out+Vector((0,0,dz))))
            n=len(ring)
            cuff=mesh_object('beanie-cuff',vertices,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],hair_material)
            for face in cuff.data.polygons:face.use_smooth=True
            parts.append(cuff)
    bpy.context.view_layer.objects.active=hair
    shell=hair.modifiers.new('headwear-thickness','SOLIDIFY');shell.thickness=.001 if p['headwear']=='none' else .006
    bpy.ops.object.modifier_apply(modifier=shell.name)
    parts.append(hair)
    if p['headwear']=='none' and p.get('hair_style')=='shoulder_length':
        parts.append(flowing_hair(obj,hair_material,mesh_object))
    return parts


def hand(side, wrist, direction, presentation, material, mesh_object, raised=False):
    name='left' if side==1 else 'right';prefix='l' if side==1 else 'r'
    obj=base_part(name,presentation,material,mesh_object)
    source=landmark(prefix+'-hand',presentation)
    axis=(landmark(prefix+'-finger-3-1',presentation)-source).normalized()
    trim(obj,source-axis*.025,axis)
    if raised:
        # Bend four fingers continuously around a small handle; thumb stays opposed.
        across=(landmark(prefix+'-finger-2-1',presentation)-landmark(prefix+'-finger-5-1',presentation)).normalized()
        inward=axis.cross(across).normalized()*side
        roots=[landmark(prefix+f'-finger-{k}-1',presentation) for k in range(2,6)]
        finger_axes=[(landmark(prefix+f'-finger-{k}-4',presentation)-r).normalized() for k,r in zip(range(2,6),roots)]
        thumb_root=landmark(prefix+'-finger-1-1',presentation)
        thumb_tip=landmark(prefix+'-finger-1-4',presentation)
        thumb_axis=(thumb_tip-thumb_root).normalized()
        target=roots[0]+inward*.023-thumb_root
        thumb_rotation=thumb_axis.rotation_difference(target.normalized())
        for vertex in obj.data.vertices:
            td=vertex.co-thumb_root;along=td.dot(thumb_axis)
            if along>0 and (td-thumb_axis*along).length<.024:
                transformed=thumb_root+(thumb_rotation@td)*min(1,target.length/(thumb_tip-thumb_root).length)
                vertex.co=vertex.co.lerp(transformed,min(1,along/.024))
                continue
            index=min(range(4),key=lambda i:(vertex.co-roots[i]-finger_axes[i]*(vertex.co-roots[i]).dot(finger_axes[i])).length)
            root=roots[index];finger_axis=finger_axes[index]
            delta=vertex.co-root;t=delta.dot(finger_axis)
            if t>0 and (delta-finger_axis*t).length<.017:
                radius=.021;theta=min(t/radius,3.05)
                vertex.co+=axis*(radius*math.sin(theta))-finger_axis*t+inward*(radius*(1-math.cos(theta)))
    rotation=axis.rotation_difference(Vector(direction).normalized())
    if raised:
        # Resolve wrist roll as well as direction: the microphone points upward.
        from mathutils import Quaternion
        target_axis=Vector(direction).normalized()
        current=rotation@across;current-=target_axis*current.dot(target_axis);current.normalize()
        target=Vector((0,0,1));target-=target_axis*target.dot(target_axis);target.normalize()
        angle=math.atan2(target_axis.dot(current.cross(target)),current.dot(target))
        rotation=Quaternion(target_axis,angle)@rotation
    for vertex in obj.data.vertices:vertex.co=Vector(wrist)+rotation@(vertex.co-source)
    if raised:
        grip=(roots[0]+roots[-1])*.5+inward*.024+axis*.010
        obj['grip_center']=list(Vector(wrist)+rotation@(grip-source))
        obj['grip_axis']=list((rotation@across).normalized())
    subdivide(obj,1)
    return obj


def forearm(side, elbow, wrist, presentation, material, mesh_object, include_hand=False, sleeve_axis=None):
    """Repose a licensed forearm with its original skin UVs, bounded at both ends."""
    prefix='l' if side==1 else 'r'
    obj=base_part(('left' if side==1 else 'right')+'-forearm',presentation,material,mesh_object)
    source=landmark(prefix+'-elbow',presentation);end=landmark(prefix+'-hand',presentation)
    axis=(end-source).normalized()
    trim(obj,source-axis*.020,axis)
    if not include_hand:trim(obj,end+axis*.010,-axis)
    target=Vector(wrist)-Vector(elbow);rotation=axis.rotation_difference(target.normalized())
    length=target.length/(end-source).length
    for vertex in obj.data.vertices:
        d=vertex.co-source
        along=d.dot(axis);radial=d-axis*along
        slim=.78+.22*max(0,min(1,along/(end-source).length))
        vertex.co=Vector(elbow)+rotation@(radial*slim+axis*along*length)
    if sleeve_axis is not None:
        opening_axis=Vector(sleeve_axis).normalized()
        trim(obj,Vector(elbow)-opening_axis*.018,opening_axis)
    subdivide(obj,1)
    return obj


def paint_buzz(obj, material, hair_material):
    """Bake clipped stubble into the existing scalp UVs: no raised helmet shell."""
    image=next(n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE')
    n=image.size[0];pixels=np.asarray(image.pixels[:],dtype=np.float32).reshape(n,n,4).copy()
    uv=obj.data.uv_layers.active
    color=np.array(hair_material.diffuse_color[:3])
    for face in obj.data.polygons:
        if max(obj.data.vertices[i].co.z for i in face.vertices)<1.70:continue
        loops=list(face.loop_indices)
        for j in range(1,len(loops)-1):
            tri=[loops[0],loops[j],loops[j+1]]
            coords=np.array([uv.data[i].uv[:] for i in tri])*(n-1)
            a,b,c=coords
            low=np.maximum(np.floor(coords.min(axis=0)).astype(int),0);high=np.minimum(np.ceil(coords.max(axis=0)).astype(int),n-1)
            if np.any(low>high):continue
            xx,yy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1))
            denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(denominator)<1e-7:continue
            w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
            w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
            w2=1-w0-w1;inside=(w0>=-.001)&(w1>=-.001)&(w2>=-.001)
            v=np.array([obj.data.vertices[obj.data.loops[i].vertex_index].co[:] for i in tri])
            positions=w0[:,:,None]*v[0]+w1[:,:,None]*v[1]+w2[:,:,None]*v[2]
            threshold=1.713+.036*np.clip((-positions[:,:,1]-.015)/.11,0,1)
            threshold+=.0018*np.sin(positions[:,:,0]*137)+.001*np.sin(positions[:,:,0]*371)
            fade=np.clip((positions[:,:,2]-threshold)/.009,0,1)
            fade=fade*fade*(3-2*fade)*inside*.65
            fade=np.where((abs(positions[:,:,0])>.081)&(positions[:,:,2]<1.752),0,fade)
            grain=.84+.32*np.mod(np.sin(xx*12.9898+yy*78.233)*43758.5453,1)
            original=pixels[yy,xx,:3]
            pixels[yy,xx,:3]=original*(1-fade[:,:,None])+color*grain[:,:,None]*fade[:,:,None]
    image.pixels.foreach_set(pixels.reshape(-1));image.update();image.pack()


def stubble(obj, material, mesh_object):
    """Individual tapered fibres, deterministically sampled on the actual scalp."""
    rng=np.random.default_rng(411);vertices=[];faces=[]
    triangles=[];areas=[]
    for face in obj.data.polygons:
        if face.center.z<1.707:continue
        co=[obj.data.vertices[i].co.copy() for i in face.vertices]
        for j in range(1,len(co)-1):
            a,b,c=co[0],co[j],co[j+1]
            area=(b-a).cross(c-a).length/2
            if area>1e-10:triangles.append((a,b,c));areas.append(area)
    weights=np.asarray(areas);weights/=weights.sum()
    for index in rng.choice(len(triangles),4400,p=weights):
        a,b,c=triangles[index];u,v=rng.random(2)
        if u+v>1:u,v=1-u,1-v
        q=a+(b-a)*u+(c-a)*v
        threshold=1.713+.036*max(0,min(1,(-q.y-.015)/.11))+.0018*math.sin(q.x*137)
        fade=max(0,min(1,(q.z-threshold)/.009))
        if rng.random()>fade or (abs(q.x)>.081 and q.z<1.752):continue
        normal=(q-Vector((0,-.025,1.70))).normalized()
        tangent=normal.cross(Vector((0,0,1)))
        if tangent.length<.01:tangent=Vector((1,0,0))
        tangent.normalize();across=normal.cross(tangent).normalized()
        q+=normal*.00015;tip=q+normal*rng.uniform(.0008,.0018)+tangent*.0007
        radius=rng.uniform(.00016,.00028);base=len(vertices)
        for j in range(3):vertices.append(tuple(q+radius*(tangent*math.cos(j*math.tau/3)+across*math.sin(j*math.tau/3))))
        vertices.append(tuple(tip))
        faces.extend([(base,base+1,base+3),(base+1,base+2,base+3),(base+2,base,base+3)])
    result=mesh_object('fitted-stubble-fibres',vertices,faces,material)
    for face in result.data.polygons:face.use_smooth=True
    return result


def flowing_hair(skull, material, mesh_object):
    """Fine swept locks continue from crown to shoulders, without a blunt fringe."""
    surface=BVHTree.FromPolygons([v.co for v in skull.data.vertices],[f.vertices[:] for f in skull.data.polygons])
    vertices=[];faces=[];rng=np.random.default_rng(1212);center=Vector((0,-.025,1.70))
    rows=28;sides=4;count=160
    for lock in range(count):
        phi=math.tau*(lock+rng.uniform(-.3,.3))/count
        front=math.sin(phi)<-.20
        fringe=front and abs(math.cos(phi))<.70
        sign=1 if math.cos(phi)>=0 else -1
        # Front locks sweep toward their temple before descending beside the jaw.
        finish_phi=(-.62 if sign==1 else math.pi+.62) if front else phi
        delta=math.atan2(math.sin(finish_phi-phi),math.cos(finish_phi-phi))
        phase=rng.uniform(0,math.tau);end=1.445+rng.uniform(-.025,.075)
        path=[];root=None;normal=None
        for row in range(rows+1):
            t=row/rows
            if t<=.5 or fringe:
                k=t if fringe else t/.5
                angle=phi+delta*k*k*(.10 if fringe else 1);theta=.045+k*(1.23+.025*math.sin(phi*11) if fringe else 1.55)
                direction=Vector((math.sin(theta)*math.cos(angle),math.sin(theta)*math.sin(angle),math.cos(theta)))
                point,normal,_,_=surface.ray_cast(center+direction*.5,-direction)
                if point is None:point=center+direction*.11;normal=direction
                q=point+normal*(.004+.002*math.sin(k*math.pi)+.0006*math.sin(k*7+phase))
                root=q.copy()
            else:
                k=(t-.5)/.5
                radius=.106+.022*k+.006*math.sin(k*math.pi*2+phase)*math.sin(k*math.pi)
                angle=finish_phi+.035*math.sin(k*4+phase)
                destination=Vector((radius*math.cos(angle),-.025+(.135+.035*k)*math.sin(angle),end))
                q=root.lerp(destination,k)
                q.x+=.005*math.sin(k*math.pi*2+phase)*math.sin(k*math.pi)
            path.append(q)
        base=len(vertices);width=rng.uniform(.0022,.0042)
        for row,q in enumerate(path):
            t=row/rows;tangent=(path[min(rows,row+1)]-path[max(0,row-1)]).normalized()
            across=Vector((-math.sin(finish_phi),math.cos(finish_phi),0))
            across-=tangent*across.dot(tangent)
            if across.length<.001:across=Vector((1,0,0))
            across.normalize();outward=tangent.cross(across).normalized()
            taper=min(1,(1-t)/.18)*min(1,.4+t/.10)
            for j in range(sides):
                a=j*math.tau/sides
                vertices.append(tuple(q+across*(width*math.cos(a)*max(.025,taper))+outward*(.0012*math.sin(a)*max(.025,taper))))
        for row in range(rows):
            for j in range(sides):
                a=base+row*sides+j;b=base+row*sides+(j+1)%sides
                faces.append((a,b,b+sides,a+sides))
        faces.extend([tuple(reversed([base+j for j in range(sides)])),tuple(base+rows*sides+j for j in range(sides))])
    result=mesh_object('fitted-swept-hair-strands',vertices,faces,material)
    for face in result.data.polygons:face.use_smooth=True
    return result
