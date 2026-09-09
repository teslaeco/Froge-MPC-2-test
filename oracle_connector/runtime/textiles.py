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
