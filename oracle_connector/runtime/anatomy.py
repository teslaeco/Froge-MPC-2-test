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
    for side in (-1,1):
        vertices=[];faces=[]
        eye_z=landmark(('l' if side==1 else 'r')+'-eye',presentation).z
        for i in range(33):
            t=i/32;x=side*(.012+.042*t);z=eye_z+.021+.005*math.sin(t*math.pi)-.004*t
            half=.0022*math.sin(math.pi*t)**.45+.00015
            for zz in (z-half,z+half):
                point,normal,_,_=surface.ray_cast(Vector((x,-.5,zz)),Vector((0,1,0)))
                vertices.append(tuple(point+normal*.0007) if point else (x,-.14,zz))
            if i:faces.append((i*2-2,i*2-1,i*2+1,i*2))
        brow=mesh_object('eyebrow',vertices,faces,eye_material)
        for face in brow.data.polygons:face.use_smooth=True
        parts.append(brow)
    if p['headwear']=='none' and p.get('hair_style')=='bald':return parts
    buzz=p.get('hair_style')=='buzz' and p['headwear']=='none'
    if buzz:
        paint_buzz(obj,material,hair_material)
        return parts
    # Hair and hats both follow the actual cranium, preserving the forehead.
    skull=obj.data;selected=[]
    def hairline(v):
        return 1.713+.036*max(0,min(1,(-v.y-.015)/.11))
    if p['headwear']=='none':
        vertices=[];faces=[]
        # Clip every intersected polygon at the hairline, avoiding a sawtooth rim.
        for face in skull.polygons:
            if abs(face.center.x)>.081 and face.center.z<1.752:continue
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
                vertices.append(tuple(v+out* .002));face_ids.append(len(vertices)-1)
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
            root=min(roots,key=lambda r:(vertex.co-r-axis*(vertex.co-r).dot(axis)).length)
            delta=vertex.co-root;t=delta.dot(axis)
            if t>0 and (delta-axis*t).length<.022:
                radius=.025;theta=min(t/radius,2.9)
                vertex.co+=axis*(radius*math.sin(theta)-t)+inward*(radius*(1-math.cos(theta)))
    rotation=axis.rotation_difference(Vector(direction).normalized())
    for vertex in obj.data.vertices:vertex.co=Vector(wrist)+rotation@(vertex.co-source)
    if raised:
        grip=(roots[0]+roots[-1])*.5+inward*.024+axis*.010
        obj['grip_center']=list(Vector(wrist)+rotation@(grip-source))
        obj['grip_axis']=list((rotation@across).normalized())
    subdivide(obj,1)
    return obj


def forearm(side, elbow, wrist, presentation, material, mesh_object, include_hand=False):
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
            fade=np.clip((positions[:,:,2]-threshold)/.009,0,1)
            fade=fade*fade*(3-2*fade)*inside
            fade=np.where((abs(positions[:,:,0])>.081)&(positions[:,:,2]<1.752),0,fade)
            grain=.84+.32*np.mod(np.sin(xx*12.9898+yy*78.233)*43758.5453,1)
            original=pixels[yy,xx,:3]
            pixels[yy,xx,:3]=original*(1-fade[:,:,None])+color*grain[:,:,None]*fade[:,:,None]
    image.pixels.foreach_set(pixels.reshape(-1));image.update();image.pack()
