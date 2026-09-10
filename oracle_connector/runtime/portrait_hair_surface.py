"""Deterministic strand normal texture for standard glTF materials.
Created procedurally from numeric waves; no source photograph is modified.
"""
import math
import numpy as np
import bpy


def surface_lock(name, samples, width, depth, material, mesh_object):
    """Closed oval lock, with a stable surface frame and tapered buried ends.

    samples are (position, outward normal) pairs in the same coordinate frame.
    Unlike a flat ribbon this has curved highlights and a real underside.
    """
    from mathutils import Vector
    import bmesh
    if len(samples)<4:
        raise ValueError('A hair lock needs at least four surface samples')
    vertices=[];faces=[];sides=12;count=len(samples)
    for i,(point,normal) in enumerate(samples):
        point=Vector(point);normal=Vector(normal).normalized()
        tangent=Vector(samples[min(count-1,i+1)][0])-Vector(samples[max(0,i-1)][0])
        tangent.normalize()
        normal=(normal-tangent*normal.dot(tangent)).normalized()
        across=tangent.cross(normal).normalized()
        t=i/(count-1);taper=.025+.975*max(0,math.sin(math.pi*t))**.48
        # Most of the underside is buried into its supporting surface. The
        # crest is irregular across its width, avoiding identical satin tubes.
        local_depth=depth*(1-.38*t*t)
        centre=point+normal*(local_depth*.14*taper-.00035)
        for k in range(sides):
            a=math.tau*k/sides
            ripple=1+.10*math.sin(a*3+t*6.7)+.035*math.sin(a*7-t*11)
            vertices.append(tuple(centre+across*(width*taper*math.cos(a))+normal*(local_depth*taper*math.sin(a)*ripple)))
            if i:
                j=(k+1)%sides
                faces.append(((i-1)*sides+k,(i-1)*sides+j,i*sides+j,i*sides+k))
    faces.extend((tuple(reversed(range(sides))),tuple((count-1)*sides+k for k in range(sides))))
    obj=mesh_object(name,vertices,faces,material)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()
    uv=obj.data.uv_layers.new(name='LockStrandFlow')
    for face in obj.data.polygons:
        face.use_smooth=True
        ks=[i%sides for i in face.vertices];seam=max(ks)-min(ks)>sides/2
        for loop,i in zip(face.loop_indices,face.vertices):
            k=i%sides
            uv.data[loop].uv=((sides if seam and k==0 else k)/sides,(i//sides)/(count-1))
    obj['closed_surface_lock']=True
    obj['groom_revision']='root-swept-rounded-rolls-r5'
    return obj

def add_strand_normal(obj, palettes):
    cached=bpy.data.images.get('procedural-fine-hair-strands-normal')
    if cached is not None:
        for mat in palettes:
            nodes=mat.node_tree.nodes;links=mat.node_tree.links
            if nodes.get('Portable fine strand texture'):continue
            tex=nodes.new('ShaderNodeTexImage');tex.name='Portable fine strand texture';tex.image=cached
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.40
            links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
        return
    w,h=2048,1024
    u=np.arange(w,dtype=np.float32)[None,:]/w
    v=np.arange(h,dtype=np.float32)[:,None]/h
    phase=2*np.pi*(.055*np.sin(v*4.8)+.018*np.sin(v*13.6))
    fine=.36*np.sin(2*np.pi*137*u+phase)+.22*np.sin(2*np.pi*263*u+phase*.68+.5)
    fine+=.12*np.sin(2*np.pi*61*u+phase*1.45+1.2)
    nx=fine
    ny=.018*np.sin(2*np.pi*193*u+phase)*np.cos(v*4.8)
    nz=np.sqrt(np.maximum(.01,1-nx*nx-ny*ny))
    rgba=np.stack(((nx+1)*.5,(ny+1)*.5,(nz+1)*.5,np.ones((h,w),dtype=np.float32)),axis=-1)
    image=bpy.data.images.new('procedural-fine-hair-strands-normal',width=w,height=h,alpha=False)
    image['strand_detail']=True
    image.colorspace_settings.name='Non-Color'
    image.pixels.foreach_set(rgba.astype(np.float32).ravel())
    image.update();image.pack()
    for mat in palettes:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        tex=nodes.new('ShaderNodeTexImage');tex.name='Portable fine strand texture';tex.image=image
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.40
        links.new(tex.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
        nodes.get('Principled BSDF').inputs['Roughness'].default_value=.57
    obj['fine_strands']='Portable tangent-space normal texture plus sparse real tapered filaments'


def add_strand_colour(palettes):
    """Packed root-to-tip strand colour; no painted studio highlights.

    The same UV flow drives albedo and the existing normal map, keeping fine
    strands readable in ordinary GLB viewers without hair-specific shaders.
    """
    w,h=2048,1024
    u=np.arange(w,dtype=np.float32)[None,:]/w
    v=np.arange(h,dtype=np.float32)[:,None]/h
    phase=2*np.pi*(.055*np.sin(v*4.8)+.018*np.sin(v*13.6))
    grain=.20*np.sin(2*np.pi*137*u+phase)+.13*np.sin(2*np.pi*263*u+phase*.68+.5)
    grain+=.085*np.sin(2*np.pi*61*u+phase*1.45+1.2)
    grain+=.08*np.sin(2*np.pi*29*u+.4*np.sin(v*9))
    # Darker buried roots and separate pigment fibres, with no baked shine.
    root=.73+.27*np.minimum(1,v*6)
    shade=np.clip((.82+grain)*root,.30,1.18)
    for mat in palettes:
        name=mat.name+'-strand-albedo';image=bpy.data.images.get(name)
        if image is None:
            rgb=np.array(mat.diffuse_color[:3],dtype=np.float32)
            rgba=np.ones((h,w,4),dtype=np.float32)
            rgba[:,:,:3]=np.clip(shade[:,:,None]*rgb[None,None,:],0,1)
            image=bpy.data.images.new(name,width=w,height=h,alpha=False)
            image['strand_detail']=True
            image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        tex=nodes.new('ShaderNodeTexImage');tex.name='Portable strand albedo';tex.image=image
        links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
        rough_name=mat.name+'-strand-roughness'
        rough=bpy.data.images.get(rough_name)
        if rough is None:
            rough=bpy.data.images.new(rough_name,width=w,height=h,alpha=False)
            rough.colorspace_settings.name='Non-Color'
            rgba=np.ones((h,w,4),dtype=np.float32)
            # Coherent but unequal fibre bands interrupt the broad crown
            # highlight; darker roots remain pigment, not painted shadows.
            band=.028*np.sin(2*np.pi*11*u+.65*np.sin(v*5.3))
            rgba[:,:,:3]=np.clip(.49-grain[:,:,None]*.34+band[:,:,None],.32,.65)
            rough.pixels.foreach_set(rgba.ravel());rough.update();rough.pack()
        texture=nodes.new('ShaderNodeTexImage');texture.name='Portable strand roughness';texture.image=rough
        links.new(texture.outputs['Color'],nodes.get('Principled BSDF').inputs['Roughness'])
