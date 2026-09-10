"""Photo-guided UVs for visible couture surfaces; hidden areas are inferred.

The reference pixels retain photographed lighting. They are not recovered
physical albedo. A guide is bound to its exact image, never another upload.
"""
import math

EMERALD_SHA256='638bee0231879a1eb2118c065ba5b052534fc4c1affaa59dbc4da83191295997'
FAN_ARC=((33,779),(119,714),(215,655),(310,611),(410,599),(512,615),
         (599,661),(676,718),(723,787),(769,862),(804,921))

def has_guide(fit):
    return fit is not None and (getattr(fit,'source_sha256',None)==EMERALD_SHA256 or
        (getattr(fit,'source_sha256',None) is not None and
         getattr(fit,'guide_verified_sha256',None)==fit.source_sha256))

def portrait_pose(fit):
    """Match measured eye-line roll; pitch/yaw remain authored 3D estimates."""
    if not has_guide(fit):return None
    observation=fit.observation
    left,right=observation['points'][468],observation['points'][473]
    dx=(right[0]-left[0])*observation['width']
    dy=(right[1]-left[1])*observation['height']
    roll=max(-.32,min(.32,.90*math.atan2(dy,dx)))
    return (-.18,roll,-.12)

def quad_uv(u,v,corners):
    u=max(0.,min(1.,u));v=max(0.,min(1.,v))
    a,b,c,d=corners
    xy=[a[k]*(1-u)*(1-v)+b[k]*u*(1-v)+c[k]*u*v+d[k]*(1-u)*v for k in (0,1)]
    return (xy[0]/1229,1-xy[1]/1536)

def garment_uv(point,hem,width):
    if not .85<=width<=1.15:raise ValueError('Reference surface requires the body width factor, not strand width')
    try:from couture_geometry import profile
    except ModuleNotFoundError:from .couture_geometry import profile
    x,y,z=point;rx,_,_=profile(z,hem,width)
    u=min(1,abs(x)/max(rx,.001))
    # The fan hides the left bodice. Mirror the visible right panel there,
    # explicitly keeping that continuation distinct from observed detail.
    if z>=1.10:
        return quad_uv(u,(z-1.10)/.33,((633,1280),(870,1242),(913,998),(745,1048)))
    # Continue the photographed lower edge into the unobserved lower dress.
    # A triangle-centre material cutoff at z=.80 left a sawtooth seam.
    # Preserve the observed waist-to-hip scale; only the hidden lower dress
    # extends the final photographed row rather than stretching the belt.
    return quad_uv(u,(z-.80)/.30,((574,1527),(966,1527),(875,1354),(644,1343)))

def fan_uv(point,radius,spread):
    x,_,z=point;a=math.atan2(x,z)
    f=max(0.,min(10.,(a/spread+.5)*10));i=min(9,int(f));t=f-i
    edge=tuple(FAN_ARC[i][k]*(1-t)+FAN_ARC[i+1][k]*t for k in (0,1))
    r=max(0.,min(1.,math.hypot(x,z)/(radius*1.025)))
    # The clean point is above the photographed fingers: no painted hand,
    # rotor or background can be duplicated on the model's actual fan leaves.
    xy=(399*(1-r)+edge[0]*r,937*(1-r)+edge[1]*r)
    return (xy[0]/1229,1-xy[1]/1536)

def material(fit):
    if not has_guide(fit):return None
    import bpy
    name='reference-surface-'+fit.source_sha256[:12]
    existing=bpy.data.materials.get(name)
    if existing:return existing
    image=bpy.data.images.load(str(fit.image_path),check_existing=False)
    image.name='original-couture-reference';image['reference_surface']=True
    image['source_sha256']=fit.source_sha256;image.pack()
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value=.06
    shader.inputs['Roughness'].default_value=.52
    shader.inputs['Specular IOR Level'].default_value=.14
    shader.inputs['Coat Weight'].default_value=.04
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image
    uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='ReferenceSurfaceUV'
    mat.node_tree.links.new(uv.outputs['UV'],texture.inputs['Vector'])
    mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    mat['reference_surface_sha256']=fit.source_sha256
    mat['contains_photographed_lighting']=True
    return mat

def bind(obj,mat,mapping,select=None):
    if mat is None:return
    layer=obj.data.uv_layers.get('ReferenceSurfaceUV') or obj.data.uv_layers.new(name='ReferenceSurfaceUV')
    if mat not in list(obj.data.materials):obj.data.materials.append(mat)
    slot=list(obj.data.materials).index(mat);mapped=0
    for face in obj.data.polygons:
        if select is not None and not select(face):continue
        for loop in face.loop_indices:
            uv=mapping(obj.data.vertices[obj.data.loops[loop].vertex_index].co)
            if not all(math.isfinite(v) and 0<=v<=1 for v in uv):
                raise ValueError('Photo guide UV outside its source image')
            layer.data[loop].uv=uv
        face.material_index=slot;mapped+=1
    obj['reference_surface_faces']=mapped
    obj['reference_surface_sha256']=mat['reference_surface_sha256']
    obj['reference_surface_inferred_hidden_regions']=True
