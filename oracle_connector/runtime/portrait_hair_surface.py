"""Deterministic strand normal texture for standard glTF materials.
Created procedurally from numeric waves; no source photograph is modified.
"""
import math
import numpy as np
import bpy

def add_strand_normal(obj, palettes):
    cached=bpy.data.images.get('procedural-fine-hair-strands-normal')
    if cached is not None:
        for mat in palettes:
            nodes=mat.node_tree.nodes;links=mat.node_tree.links
            if nodes.get('Portable fine strand texture'):continue
            tex=nodes.new('ShaderNodeTexImage');tex.name='Portable fine strand texture';tex.image=cached
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.18
            links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
        return
    w,h=1024,512
    u=np.arange(w,dtype=np.float32)[None,:]/w
    v=np.arange(h,dtype=np.float32)[:,None]/h
    phase=2*np.pi*(.21*np.sin(v*4.8)+.065*np.sin(v*13.6))
    fine=.29*np.sin(2*np.pi*193*u+phase)+.16*np.sin(2*np.pi*347*u+phase*.68+.5)
    fine+=.095*np.sin(2*np.pi*79*u+phase*1.45+1.2)
    nx=fine
    ny=.018*np.sin(2*np.pi*193*u+phase)*np.cos(v*4.8)
    nz=np.sqrt(np.maximum(.01,1-nx*nx-ny*ny))
    rgba=np.stack(((nx+1)*.5,(ny+1)*.5,(nz+1)*.5,np.ones((h,w),dtype=np.float32)),axis=-1)
    image=bpy.data.images.new('procedural-fine-hair-strands-normal',width=w,height=h,alpha=False)
    image.colorspace_settings.name='Non-Color'
    image.pixels.foreach_set(rgba.astype(np.float32).ravel())
    image.update();image.pack()
    for mat in palettes:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        tex=nodes.new('ShaderNodeTexImage');tex.name='Portable fine strand texture';tex.image=image
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.18
        links.new(tex.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
        nodes.get('Principled BSDF').inputs['Roughness'].default_value=.43
    obj['fine_strands']='Portable tangent-space normal texture plus sparse real tapered filaments'
