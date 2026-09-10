"""Sample measured photo colour onto skin vertices, preserving portable COLOR_0.

The original anatomical UV atlas remains; no photo plane or second face is added.
This transfers illuminated colour, not a lighting-free albedo reconstruction.
Eye pixels and unobserved outer skin are excluded and feathered into the atlas.
"""
import numpy as np
from photo_face import smooth


def project(anchors, destinations, triangles, points):
    # Piecewise barycentric transfer stays inside measured facial triangles.
    # A global spline extrapolated the background onto the unobserved temple.
    out=np.zeros((len(points),2));valid=np.zeros(len(points),dtype=bool)
    for triangle in triangles:
        a,b,c=anchors[triangle]
        low=np.minimum(np.minimum(a,b),c)-1e-8;high=np.maximum(np.maximum(a,b),c)+1e-8
        ids=np.where(np.all((points>=low)&(points<=high),axis=1))[0]
        if not len(ids):continue
        matrix=np.array([b-a,c-a]).T
        if abs(np.linalg.det(matrix))<1e-12:continue
        uv=(points[ids]-a)@np.linalg.inv(matrix).T
        inside=(uv[:,0]>=-1e-6)&(uv[:,1]>=-1e-6)&(uv.sum(axis=1)<=1+1e-6)
        ids=ids[inside];uv=uv[inside]
        da,db,dc=destinations[triangle]
        out[ids]=da+uv[:,0,None]*(db-da)+uv[:,1,None]*(dc-da)
        valid[ids]=True
    return out,valid


def sample(pixels, uv):
    height,width=pixels.shape[:2]
    xy=np.clip(uv,0,1)*[width-1,height-1]
    x,y=np.floor(xy).astype(int).T
    dx,dy=(xy-np.floor(xy)).T
    xx=np.minimum(x+1,width-1);yy=np.minimum(y+1,height-1)
    return (pixels[y,x]*(1-dx)[:,None]*(1-dy)[:,None]+
        pixels[y,xx]*dx[:,None]*(1-dy)[:,None]+
        pixels[yy,x]*(1-dx)[:,None]*dy[:,None]+pixels[yy,xx]*dx[:,None]*dy[:,None])


def linear(rgb):
    return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)


def srgb(rgb):
    return np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)


def add_skin_microstructure(material, atlas_size):
    """Authored, portable pore relief; not recovered photographic geometry."""
    import bpy
    nodes=material.node_tree.nodes;links=material.node_tree.links
    shader=nodes.get('Principled BSDF')
    from reference_quality import procedural_edge
    size=procedural_edge(1024)
    rng=np.random.default_rng(47021)
    noise=rng.normal(0,1,(size,size)).astype(np.float32)
    soft=(noise+np.roll(noise,1,0)+np.roll(noise,-1,0)+np.roll(noise,1,1)+np.roll(noise,-1,1))/5
    nx=(soft-np.roll(soft,1,1))*.16
    ny=(soft-np.roll(soft,1,0))*.16
    rgba=np.ones((size,size,4),dtype=np.float32)
    rgba[:,:,:3]=np.stack(((nx+1)*.5,(ny+1)*.5,np.sqrt(np.maximum(.01,1-nx*nx-ny*ny))*.5+.5),axis=-1)
    # Preserve the atlas' reserved eyeball square, even if this material is
    # reused elsewhere; eye material and measured fit are otherwise untouched.
    rgba[:size//8,:size//8,:3]=(.5,.5,1.)
    image=bpy.data.images.new('couture-inferred-skin-pore-normal',width=size,height=size,alpha=False)
    image['detail_origin']='authored_procedural_native'
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
    tex=nodes.new('ShaderNodeTexImage');tex.name='Portable skin pore normal';tex.image=image
    # The first exported comparison made the pores read as coarse orange
    # peel. Keep relief below the level of the photographed skin shading.
    normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.085
    links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    rgba[:,:,:3]=np.clip(.52+soft[:,:,None]*.018,.47,.57)
    rgba[:size//8,:size//8,:3]=.22
    image=bpy.data.images.new('couture-inferred-skin-roughness',width=size,height=size,alpha=False)
    image['detail_origin']='authored_procedural_native'
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
    tex=nodes.new('ShaderNodeTexImage');tex.name='Portable skin roughness';tex.image=image
    links.new(tex.outputs['Color'],shader.inputs['Roughness'])
    shader.inputs['IOR'].default_value=1.40
    shader.inputs['Specular IOR Level'].default_value=.32
    material['skin_microstructure']='authored deterministic pore normal and varied roughness; not measured'


def apply(fit, head, coordinates):
    import bpy
    attr=head.data.color_attributes.get('CosmeticTint')
    if attr is None:
        raise ValueError('Brakuje powierzchni koloru twarzy.')
    reference=bpy.data.images.load(str(fit.image_path),check_existing=False)
    # Analysis is bounded; the separately loaded garment texture keeps its source resolution.
    from reference_quality import fit_dimensions
    size=fit_dimensions(*reference.size,1600)
    if tuple(reference.size)!=size:reference.scale(*size)
    buffer=np.empty(size[0]*size[1]*4,dtype=np.float32)
    reference.pixels.foreach_get(buffer)
    source_pixels=buffer.reshape(size[1],size[0],4)[:,:,:3]
    ref_uv=np.asarray(fit.observation['points'])[:468,:2].copy();ref_uv[:,1]=1-ref_uv[:,1]
    query=coordinates[:,[0,2]].copy()
    # A turned head exposes one cheek much more fully. In the foreshortened
    # half, landmarks may lie on background/hair. Mirror the observed half's
    # colour; record this inference instead of projecting those hidden pixels.
    left_span=abs(ref_uv[1,0]-ref_uv[234,0])
    right_span=abs(ref_uv[454,0]-ref_uv[1,0])
    mirror_colour=max(left_span,right_span)>1.35*max(min(left_span,right_span),.001)
    if mirror_colour:
        query[:,0]=np.abs(query[:,0])*(1 if right_span>left_span else -1)
    projected,valid=project(np.asarray(fit.template['surface_xz']),ref_uv,
        np.asarray(fit.template['projection_triangles']),query)
    rgb=sample(source_pixels,projected)
    atlas=next(n.image for n in head.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    pixels=np.asarray(atlas.pixels[:],dtype=np.float32).reshape(atlas.size[1],atlas.size[0],4)[:,:,:3]
    uv=np.zeros((len(coordinates),2));counts=np.zeros(len(coordinates))
    for loop in head.data.loops:
        uv[loop.vertex_index]+=head.data.uv_layers['UVMap'].data[loop.index].uv
        counts[loop.vertex_index]+=1
    uv/=np.maximum(counts,1)[:,None]
    base=sample(pixels,uv)
    # The photo contains illumination and highlights, not diffuse albedo. A
    # median of the upper cheek amplified green/blue up to 2x and washed out
    # the shared atlas; COLOR_0 <= 1 then could not restore the intended tone.
    # Use lower/middle cheek luminance ranks, omitting lips/eyes/silhouette,
    # with an explicitly inferred diffuse exposure (not inverse rendering).
    x,y,z=coordinates.T
    cheek=valid&(y<-.085)&(np.abs(x)>.028)&(np.abs(x)<.055)&(z>1.613)&(z<1.665)
    photo_exposure=1.;photo_balance=np.ones(3)
    if head.get('photo_skin_midtone_calibration') and np.count_nonzero(cheek)>=32:
        cheek_rgb=linear(rgb[cheek])
        luminance=cheek_rgb@np.array([.2126,.7152,.0722])
        low,high=np.percentile(luminance,[20,45])
        midtones=cheek_rgb[(luminance>=low)&(luminance<=high)]
        observed=np.median(midtones,axis=0)
        planned=np.maximum(np.median(linear(base[cheek]),axis=0),.008)
        from reference_surfaces import has_guide
        # This reference's studio comparison remained too pale. Its darker
        # inferred exposure is shared by head, neck and both hands; other
        # photographs retain the previous calibration.
        diffuse_scale=.34 if has_guide(fit) else .65
        if has_guide(fit):photo_balance=np.array([1.,.90,.80])
        photo_exposure=diffuse_scale
        # Bound the requested reduction in paleness: this correction must
        # never brighten any atlas channel or exceed a 70% linear reduction.
        gain=np.clip(observed*diffuse_scale*photo_balance/planned,.30,.90)
        rgba=np.asarray(atlas.pixels[:],dtype=np.float32).reshape(atlas.size[1],atlas.size[0],4).copy()
        corrected=srgb(np.clip(linear(pixels)*gain,0,1))
        # anatomy.skin_atlas reserves this lower-left square for the eyeballs.
        patch_height,patch_width=atlas.size[1]//8,atlas.size[0]//8
        corrected[:patch_height,:patch_width]=pixels[:patch_height,:patch_width]
        rgba[:,:,:3]=corrected
        atlas.pixels.foreach_set(rgba.reshape(-1));atlas.update();atlas.pack()
        if has_guide(fit):
            add_skin_microstructure(head.data.materials[0],atlas.size[:])
        pixels=corrected
        base=sample(pixels,uv)
        fit.report.update(photo_skin_atlas_calibrated=True,
                          photo_skin_atlas_linear_gain=gain.tolist(),
                          photo_skin_measured_midtone_srgb=srgb(observed).tolist(),
                          photo_skin_midtone_luminance_percentiles=[20,45],
                          photo_skin_diffuse_exposure_inferred=diffuse_scale,
                          photo_skin_warm_balance_inferred=photo_balance.tolist(),
                          photo_skin_microstructure_inferred=bool(has_guide(fit)),
                          photo_unobserved_skin_colour_inferred=True)
    # glTF vertex colours must remain in [0,1]. Extremely bright photographed
    # specular highlights cannot brighten the diffuse atlas beyond white.
    tint=np.clip(linear(rgb)*photo_exposure*photo_balance/np.maximum(linear(base),.008),.003,1)
    mask=(1-smooth(-.085,-.04,y))*(1-smooth(.062,.078,np.abs(x)))
    mask*=smooth(1.550,1.586,z)*(1-smooth(1.725,1.749,z))
    mask*=valid
    oval=[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,
          152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109,10]
    boundary=np.asarray(fit.template['surface_xz'])[oval]
    edge_distance=np.full(len(query),np.inf)
    for a,b in zip(boundary[:-1],boundary[1:]):
        segment=b-a
        t=np.clip((query-a)@segment/max(np.dot(segment,segment),1e-12),0,1)
        edge_distance=np.minimum(edge_distance,np.linalg.norm(query-a-t[:,None]*segment,axis=1))
    mask*=smooth(.002,.011,edge_distance)
    for center in (-.03235,.03235):
        eye=np.sqrt(((x-center)/.0195)**2+((z-1.679)/.0070)**2)
        mask*=smooth(.85,1.18,eye)
    original=np.asarray([tuple(v.color[:3]) for v in attr.data])
    colors=np.c_[original*(1-mask[:,None])+tint*mask[:,None],np.ones(len(coordinates))]
    attr.data.foreach_set('color',colors.astype(np.float32).reshape(-1))
    head['photo_color_source_sha256']=fit.source_sha256
    head['photo_color_method']='measured photo sampled on skin; eye pixels excluded; illumination retained'
    fit.report.update(photo_color_vertices=int(np.sum(mask>.5)),photo_colour_applied=True,
                      photo_lighting_removed=False,photo_eye_pixels_excluded=True,
                      photo_hidden_colour_mirrored=bool(mirror_colour))
    bpy.data.images.remove(reference)
