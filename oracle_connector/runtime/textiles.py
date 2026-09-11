"""Fixed generated textile albedos, baked tangent normals, no network or user paths."""
from pathlib import Path
import bpy
import numpy as np

ASSETS=Path(__file__).resolve().parent/'assets'

def apply(material, kind, rgb):
    image=bpy.data.images.load(str(ASSETS/('cotton-jersey-albedo.png' if kind=='cotton' else 'indigo-denim-albedo.png')),check_existing=False)
    image.scale(512,512)
    pixels=np.asarray(image.pixels[:],dtype=np.float32).reshape(512,512,4).copy()
    source=pixels[:,:,:3]
    luminance=source.mean(axis=2)
    # Use the source weave with the explicitly requested clothing palette.
    detail=luminance/max(float(np.median(luminance)),.001)
    detail=np.clip(1+(detail-1)*(.42 if kind=='cotton' else .58),.65,1.32)
    pixels[:,:,:3]=np.clip(detail[:,:,None]*np.asarray(rgb),0,1)
    pixels[:,:,3]=1
    image.pixels.foreach_set(pixels.reshape(-1));image.update();image.file_format='PNG';image.pack()
    image.name=material.name+'-'+kind+'-albedo'
    nodes=material.node_tree.nodes;links=material.node_tree.links
    shader=nodes.get('Principled BSDF');shader.inputs['Metallic'].default_value=0;shader.inputs['Roughness'].default_value=.88 if kind=='cotton' else .83
    node=nodes.new('ShaderNodeTexImage');node.image=image
    links.new(node.outputs['Color'],shader.inputs['Base Color'])
    # A shared normal map per fabric saves image slots when palettes are reused.
    normal_image=bpy.data.images.get('woven-'+kind+'-normal')
    if normal_image is None and len(bpy.data.images)<16:
        height=luminance[::2,::2]
        dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*.45
        dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*.45
        normals=np.stack([-dx,-dy,np.ones_like(dx)],axis=2)
        normals/=np.linalg.norm(normals,axis=2,keepdims=True)
        packed=np.ones((256,256,4),dtype=np.float32);packed[:,:,:3]=normals*.5+.5
        normal_image=bpy.data.images.new('woven-'+kind+'-normal',width=256,height=256,alpha=False)
        normal_image.colorspace_settings.name='Non-Color'
        normal_image.pixels.foreach_set(packed.reshape(-1));normal_image.update();normal_image.file_format='PNG';normal_image.pack()
    if normal_image:
        normal=nodes.new('ShaderNodeTexImage');normal.image=normal_image
        mapping=nodes.new('ShaderNodeNormalMap');mapping.inputs['Strength'].default_value=.35
        links.new(normal.outputs['Color'],mapping.inputs['Color']);links.new(mapping.outputs['Normal'],shader.inputs['Normal'])
    material['textile']=kind


def crystal_facets(material):
    """Packed small-scale crystal planes and veins, shared across couture.

    These are procedural surface details, not a reconstruction of photograph
    pixels. Large silhouettes and seams remain actual separate mesh geometry.
    """
    if material.get('crystal_facets_revision')==1:return
    from reference_quality import procedural_edge
    size=procedural_edge(1024);cols=14;rows=18;rng=np.random.default_rng(20260910)
    grid=np.zeros((rows+1,cols+1,2),dtype=np.float32)
    for j in range(rows+1):
        for i in range(cols+1):
            grid[j,i]=(i/cols,j/rows)
            if 0<i<cols and 0<j<rows:grid[j,i]+=rng.uniform(-.32,.32,2)/(cols,rows)
    base=np.asarray(material.diffuse_color[:3],dtype=np.float32)
    albedo=np.ones((size,size,4),dtype=np.float32);albedo[:,:,:3]=base
    normal=np.ones_like(albedo);normal[:,:,:3]=(.5,.5,1.)
    colours=np.array(((.7,1.1,.80),(.7,.82,1.12),(.60,.48,1.35),(1.,.93,.97)))
    for j in range(rows):
        for i in range(cols):
            corners=[grid[j,i],grid[j,i+1],grid[j+1,i+1],grid[j+1,i]]
            for indices in ((0,1,2),(0,2,3)):
                a,b,c=[corners[k] for k in indices]
                x0,y0=np.maximum(0,np.floor(np.minimum(np.minimum(a,b),c)*size).astype(int))
                x1,y1=np.minimum(size,np.ceil(np.maximum(np.maximum(a,b),c)*size).astype(int)+1)
                yy,xx=np.mgrid[y0:y1,x0:x1];px=(xx+.5)/size;py=(yy+.5)/size
                denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                wa=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/denominator
                wb=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/denominator
                wc=1-wa-wb;inside=(wa>=0)&(wb>=0)&(wc>=0)
                edge=np.minimum(np.minimum(wa,wb),wc)
                vein=np.clip(edge/.018,0,1)
                shade=rng.uniform(.82,1.04)
                rgb=base*(.72+.28*colours[int(rng.integers(4))])*shade
                detail=(.975+.025*np.sin(px*2700+py*590))*(.80+.20*vein)
                patch=albedo[y0:y1,x0:x1,:3];patch[inside]=np.clip((rgb[None,None,:]*detail[:,:,None])[inside],0,1)
                nx,ny=rng.uniform(-.20,.20,2);nz=(1-nx*nx-ny*ny)**.5
                normal[y0:y1,x0:x1,:3][inside]=(np.array((nx,ny,nz))*.5+.5)
    nodes=material.node_tree.nodes;links=material.node_tree.links;shader=nodes.get('Principled BSDF')
    for label,pixels,is_normal in (('microfacet-albedo',albedo,False),('microfacet-normal',normal,True)):
        image=bpy.data.images.new(material.name+'-'+label,width=size,height=size,alpha=False)
        image['detail_origin']='authored_procedural_native'
        if is_normal:image.colorspace_settings.name='Non-Color'
        image.pixels.foreach_set(pixels.ravel());image.update();image.pack()
        tex=nodes.new('ShaderNodeTexImage');tex.name=label;tex.image=image
        if is_normal:
            mapping=nodes.new('ShaderNodeNormalMap');mapping.inputs['Strength'].default_value=.65
            links.new(tex.outputs['Color'],mapping.inputs['Color']);links.new(mapping.outputs['Normal'],shader.inputs['Normal'])
        else:links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    material['crystal_facets_revision']=1


def couture_uv(obj,planar=False):
    """Portable surface coordinates for dress seams and small crystal detail."""
    import math
    # Turbines share a mesh. Repeated instances must not allocate another UV
    # layer (Blender allows only eight); the shared geometry is mapped once.
    if obj.data.uv_layers.get('CoutureSurfaceDetail') is not None:return
    uv=obj.data.uv_layers.new(name='CoutureSurfaceDetail')
    for face in obj.data.polygons:
        values=[]
        for idx in face.vertices:
            x,y,z=obj.data.vertices[idx].co
            values.append((x*2.3+.5,z*2.3) if planar else (math.atan2(y,x)/math.tau+.5,z*1.65))
        seam=not planar and max(u for u,v in values)-min(u for u,v in values)>.5
        for loop,(u,v) in zip(face.loop_indices,values):uv.data[loop].uv=(u+1 if seam and u<.5 else u,v)
