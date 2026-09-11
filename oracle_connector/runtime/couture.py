"""Dedicated fitted couture. Never wraps a sweatshirt/trouser character.

The portrait remains a parameterised CC0 face, not a recovered identity.
Hidden garment/body areas are explicitly marked as reconstructed.
"""
import math
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
from detailed_geometry import loft
from portrait import build_portrait, portrait_transforms
from portrait_hands import build_hand, fit_grip_wrist
import anatomy
import couture_geometry as geometry


def rotor(p, material, accent, mesh_object):
    vv,ff,slots=geometry.rotor(p['radius'],p['depth'],p['blades'])
    obj=mesh_object(p['name'],vv,ff,material)
    obj.location=p['center'];obj.data.materials.append(accent)
    for face,index in zip(obj.data.polygons,slots):face.material_index=index
    obj['froge_role']='reusable-rotor';obj['blade_count']=p['blades']
    return obj


def reference_character(p, materials, mesh_object, tube, ellipsoid, join_meshes):
    skin,hair,dress,crystal,metal,shoe,eyes,nails=[materials[p[k+'_material']] for k in
        ('skin','hair','dress','crystal','accent','shoe','eye','nail')]
    # Broad crystal planes need restrained white reflections so their emerald
    # colour survives the studio lights and GLB viewers. Reuse the shared gem.
    gem_shader=crystal.node_tree.nodes.get('Principled BSDF')
    gem_shader.inputs['Coat Weight'].default_value=.26
    gem_shader.inputs['Specular IOR Level'].default_value=.28
    from textiles import crystal_facets,couture_uv
    import reference_surfaces as photo_surface
    reference_material=photo_surface.material(p.get('_photo_fit'))
    garment_reference=reference_material
    if reference_material:
        garment_reference=reference_material.copy();garment_reference.name+='-restrained-cloth'
        nodes=garment_reference.node_tree.nodes;links=garment_reference.node_tree.links
        texture=next(n for n in nodes if n.type=='TEX_IMAGE')
        colour=nodes.new('ShaderNodeVertexColor');colour.layer_name='ReferenceClothTone'
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        links.new(texture.outputs['Color'],mix.inputs[1]);links.new(colour.outputs['Color'],mix.inputs[2])
        links.new(mix.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    reference_pose=photo_surface.portrait_pose(p.get('_photo_fit'))
    if reference_pose is not None:p={**p,'head_rotation':reference_pose}
    crystal_facets(crystal)
    # Crystal detail uses its own coordinates even when a second, original-
    # photograph UV layer is present on the same joined object.
    gem_uv=crystal.node_tree.nodes.new('ShaderNodeUVMap');gem_uv.uv_map='CoutureSurfaceDetail'
    for node in crystal.node_tree.nodes:
        if node.type=='TEX_IMAGE':crystal.node_tree.links.new(gem_uv.outputs['UV'],node.inputs['Vector'])
    parts=[];hand_jobs=[];width={'slim':.94,'average':1.}[p['build']]
    fan_pivot=Vector((-.165,-.243,1.275))
    offset,thickness=p['garment_offset'],p['garment_thickness']
    def add(obj,role):
        obj['froge_role']=role;parts.append(obj);return obj
    def line(name,points,radii,material,sides=10):
        return add(tube(p['name']+'-'+name,points,radii,material,sides),name)
    def shaped(name,stations,material,sides=48):
        return add(loft(p['name']+'-'+name,[{'center':a[:3],'radii':a[3:]} for a in stations],sides,material,mesh_object),name)
    body=skin.copy();body.name=p['name']+'-body-skin'
    body.node_tree.nodes.clear()
    shader=body.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=body.node_tree.nodes.new('ShaderNodeOutputMaterial')
    body.node_tree.links.new(shader.outputs['BSDF'],out.inputs['Surface'])
    shader.inputs['Base Color'].default_value=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in skin.diffuse_color[:3])+(1,)
    shader.inputs['Roughness'].default_value=.55
    # The body and the dress share the same profile. Their separation is an
    # actual radial clearance, not a fixed plane in front of the torso.
    stations=[]
    for z in (.84,.94,1.03,1.10,1.19,1.30,1.39,1.45):
        rx,ry,cy=geometry.profile(z,p['hem_radius'],width)
        stations.append((0,cy,z,rx-.001,ry-.001))
    torso=shaped('body-under-gown',stations,body)
    for vertex in torso.data.vertices:
        vertex.co=geometry.contain_under_gown(vertex.co,p['hem_radius'],width,offset,thickness)
    torso['contained_by_gown']=True
    torso['gown_envelope']=[p['hem_radius'],width,offset,thickness]
    # The portrait already contains a complete neck down to the garment. A
    # second tall cylinder used to stick out behind it above the collar.
    shaped('neck',[(0,.006,1.39,.054,.049),(0,-.005,1.455,.046,.042)],body,48)
    vv,ff=geometry.gown(p['hem_radius'],width,offset,thickness)
    gown=add(mesh_object(p['name']+'-fitted-gown',vv,ff,dress),'fitted-gown')
    for face in gown.data.polygons:face.use_smooth=True
    gown['garment_offset_m']=offset;gown['garment_thickness_m']=thickness
    # Conformal triangular gemstone inlays follow every profile change. A
    # Coarser tessellation frees budget for the groom; a 4–6 mm offset keeps
    # the short triangle interiors clear at the body's profile transitions.
    vv,ff,slots=geometry.garment_inlays(p['hem_radius'],width,offset)
    inlay=add(mesh_object(p['name']+'-conformal-facets',vv,ff,crystal),'conformal-facets')
    inlay.data.materials.append(dress);inlay.data.materials.append(metal)
    for face,index in zip(inlay.data.polygons,slots):
        face.material_index=index;face.use_smooth=True
    piping=[tube('couture-silver-seam',path,[.00062]*len(path),metal,6)
            for path in geometry.garment_seams(p['hem_radius'],width,offset)]
    seams=add(join_meshes(piping,p['name']+'-couture-seams'),'couture-seams')
    seams['seam_count']=len(piping);seams['radius_m']=.00062
    if p['cape']:
        vv,ff=geometry.cape_surface(p['hem_radius'],width,offset=offset)
        reverse=dress.copy();reverse.name=p['name']+'-inferred-teal-cloth-reverse'
        reverse_rgb=tuple(.75*a+.25*b for a,b in zip(dress.diffuse_color[:3],crystal.diffuse_color[:3]))
        reverse.diffuse_color=(*reverse_rgb,1)
        shader=reverse.node_tree.nodes.get('Principled BSDF')
        for socket in ('Base Color','Roughness','Metallic'):
            for link in list(shader.inputs[socket].links):reverse.node_tree.links.remove(link)
        shader.inputs['Base Color'].default_value=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in reverse_rgb)+(1,)
        shader.inputs['Roughness'].default_value=.52
        shader.inputs['Metallic'].default_value=.03
        shader.inputs['Specular IOR Level'].default_value=.20
        shader.inputs['Coat Weight'].default_value=.02
        cape=add(mesh_object(p['name']+'-shoulder-drape',vv,ff,reverse),'shoulder-drape')
        cape['drape_geometry_revision']=2;cape['unobserved_back_reconstructed']=True
        for face in cape.data.polygons:face.use_smooth=True
        solid=cape.modifiers.new('Thin cloth drape','SOLIDIFY');solid.thickness=thickness
        bpy.context.view_layer.objects.active=cape;bpy.ops.object.modifier_apply(modifier=solid.name)
        # Continue the visible dress's thin seam language onto the inferred
        # reverse. These are attached paths, not photographed back details.
        for u in (.17,.5,.83):
            path=[]
            for j in range(53):
                t=j/52;x,y,z=geometry.cape_point(t,u,p['hem_radius'],width,offset=offset)
                path.append((x,y+.0018,z))
            seam=line('reconstructed-back-seam',path,[.00065]*len(path),metal,6)
            seam['unobserved_back_reconstructed']=True
        # Visible shoulder cape: radial cloth folds fall in front of the
        # upper arm, rather than leaving a featureless black sleeve exposed.
        nr=45;nc=33
        cv,cf=geometry.cape_surface(p['hem_radius'],width,side=True,rows=nr,cols=nc,offset=offset)
        uv=[]
        for j in range(nr):
            t=j/(nr-1)
            for k in range(nc):
                u=k/(nc-1)
                uv.append(photo_surface.quad_uv(u,1-t,((1094,1490),(1214,1477),(1054,949),(1008,932))))
        side_cape=add(mesh_object(p['name']+'-visible-pleated-cape',cv,cf,dress),'visible-pleated-cape')
        side_cape['drape_geometry_revision']=2
        for face in side_cape.data.polygons:face.use_smooth=True
        if reference_material:
            layer=side_cape.data.uv_layers.new(name='ReferenceSurfaceUV')
            side_cape.data.materials[0]=reference_material
            for loop in side_cape.data.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
            side_cape['reference_surface_faces']=len(cf)
            side_cape['reference_surface_sha256']=reference_material['reference_surface_sha256']
            side_cape['reference_surface_inferred_hidden_regions']=True
        solid=side_cape.modifiers.new('Real folded cloth thickness','SOLIDIFY');solid.thickness=thickness
        bpy.context.view_layer.objects.active=side_cape;bpy.ops.object.modifier_apply(modifier=solid.name)
    for band,z in enumerate((1.075,1.092,1.109,1.126)):
        points=[]
        for i in range(97):
            angle=math.tau*i/96;front=max(0,-math.sin(angle))**3
            # The ribbons converge at the clasp and sweep over the hips,
            # retaining clearance on the actual curved dress surface.
            height=z+front*((1.103-z)*.55+.010*math.cos(angle)*(1 if band%2 else -1))
            points.append(geometry.gown_point(height,angle,p['hem_radius'],width,offset+.003))
        line('waist-metal-ribbon',points,[.0018]*97,metal,8)
    clasp_outline=[(0,-.028),(.021,-.003),(.015,.014),(0,.031),(-.015,.014),(-.021,-.003)]
    vv,ff=geometry.cut_jewel(clasp_outline,.010)
    clasp=add(mesh_object(p['name']+'-waist-gem',vv,ff,crystal),'waist-gem');clasp.location=(0,-.092,1.103)
    line('waist-gem-rim',[(x,-.092,z+1.103) for x,z in clasp_outline+clasp_outline[:1]],[.0008]*7,metal,6)
    for side in (-1,1):
        # Full separate legs, ankles and shoes continue behind the opaque gown.
        leg=shaped('leg',[(side*.078,0,.94,.065,.073),(side*.084,-.006,.53,.043,.049),
                      (side*.091,.009,.35,.045,.045),(side*.105,-.008,.10,.027,.031)],body,48)
        for vertex in leg.data.vertices:
            vertex.co=geometry.contain_under_gown(vertex.co,p['hem_radius'],width,offset,thickness)
        leg['contained_by_gown']=True
        leg['gown_envelope']=[p['hem_radius'],width,offset,thickness]
        add(ellipsoid(p['name']+'-shoe',(side*.105,-.061,.048),(.035,.103,.031),shoe,3),'reconstructed-shoe')
        shaped('shoe-heel',[(side*.105,.008,.006,.013,.014),(side*.105,.008,.052,.014,.014)],shoe,24)
        shoulder=Vector((side*.169*width,0,1.390))
        elbow=Vector((side*.240,.012,1.210))
        holding=(side==-1 and p['fan']['enabled'])
        if holding:elbow=Vector((-.260,-.080,1.062))
        # The hanging hand must sit in front of the shoulder drape. The old
        # wrist lay behind it, clipping the thumb into the skirt and hiding
        # three fingers. Its unseen reference pose is an authored estimate.
        wrist=Vector((-.227,-.295,1.202) if holding else (side*.268,-.118,1.020))
        direction=Vector((.65,0,.76)).normalized() if holding else Vector((.05,-.10,-1)).normalized()
        hand_plan={'side':'right' if side==-1 else 'left','wrist':list(wrist),
            'direction':list(direction),'palm_normal':[0,-1,0] if holding else [.45,-.89,0],'presentation':'feminine',
            'scale':.93,'curl':.92 if holding else .18,'nail_length':.0025}
        if holding:
            hand_plan.update(finger_curls=[.50,.48,.55,.62,.72],grip_contacts=[
                [-.180,-.237,1.270],[-.146,-.258,1.302],[-.146,-.250,1.279],
                [-.151,-.250,1.256],[-.155,-.253,1.233]])
            hand_plan=fit_grip_wrist(hand_plan);wrist=Vector(hand_plan['wrist'])
            hand_plan['forearm_direction']=list((wrist-elbow).normalized())
        else:
            hand_plan['finger_curls']=[.55,.22,.40,.52,.62]
            hand_plan['forearm_direction']=list((wrist-elbow).normalized())
        # Build sleeves after fitting so the wrist, skin and cuff stay joined.
        sleeve_start=shoulder
        if not holding:
            # The reference exposes the upper arm between the bodice and
            # shoulder cape. This is real skin, with a clean sleeve boundary.
            upper=shaped('exposed-upper-arm',[(*shoulder,.046,.049),
                (*shoulder.lerp(elbow,.25),.044,.043),
                (*shoulder.lerp(elbow,.60),.034,.035)],body,40)
            upper['authored_reference_armhole']=True
            sleeve_start=shoulder.lerp(elbow,.43)
        shaped('fitted-sleeve',[(*sleeve_start,.046 if not holding else .051,.047 if not holding else .054),(*shoulder.lerp(elbow,.65),.039,.040),
              (*elbow,.033,.034),(*elbow.lerp(wrist,.48),.035,.032),(*wrist,.027,.024)],dress)
        hand_jobs.append((hand_plan,holding))
        # A thin crystal shard stays close to the anatomical shoulder. Its
        # narrow closed walls use silver; the broad faces remain gemstone.
        vv,ff,slots=geometry.shoulder_plate(side,thickness)
        plate=add(mesh_object(p['name']+'-shoulder-inlay',vv,ff,crystal),'shoulder-inlay')
        plate.data.materials.append(metal)
        for face,index in zip(plate.data.polygons,slots):face.material_index=index
        # The thin shell's side material is almost invisible head-on. Give
        # the exposed perimeter a real narrow jewellery edge and a crease.
        edge=[tuple(Vector(v)+Vector((0,-.001,0))) for v in vv[:4]]
        line('shoulder-silver-edge',edge+edge[:1],[.00085]*5,metal,6)
        line('shoulder-fold', [edge[0],edge[2]],[.00055]*2,metal,6)
    eye_mid=(anatomy.landmark('l-eye','feminine')+anatomy.landmark('r-eye','feminine'))*.5
    portrait_plan={**p,'presentation':'feminine','hair_style':'swept_updo' if p['updo'] else 'shoulder_length',
        'headwear':'none','eyewear':'none','center':[0,eye_mid.y,1.64],
        'rotation':p['head_rotation'],'scale':1.,'makeup_rgb':tuple(crystal.diffuse_color[:3])}
    head_parts=build_portrait(portrait_plan,materials,mesh_object,ellipsoid);parts+=head_parts
    # Fit the collar to the actual transformed neck. A fixed ellipse centred
    # behind the neck intersected the skin and exposed a jagged lower boundary.
    from mathutils.bvhtree import BVHTree
    head_obj=next(o for o in head_parts if o.get('anatomical_head'))
    neck_surface=BVHTree.FromPolygons([head_obj.matrix_world@v.co for v in head_obj.data.vertices],
                                    [f.vertices[:] for f in head_obj.data.polygons])
    vv=[];ff=[];rows=13;cols=49
    # A tailored collar follows a smooth ellipse at each height. Copying
    # every individual ray distance produced a crumpled, lumpy rigid rim.
    collar_sections=[]
    for row in range(rows):
        t=row/(rows-1);z=1.419+.110*t;origin=Vector((0,-.017,z));hits=[]
        for i in range(64):
            a=math.tau*i/64;direction=Vector((math.cos(a),math.sin(a),0))
            hit,_,_,_=neck_surface.ray_cast(origin,direction,.14)
            if hit is not None:hits.append(hit)
        if hits:
            cx=(min(v.x for v in hits)+max(v.x for v in hits))*.5
            cy=(min(v.y for v in hits)+max(v.y for v in hits))*.5
            rx=max(.040,(max(v.x for v in hits)-min(v.x for v in hits))*.5+.003)
            ry=max(.037,(max(v.y for v in hits)-min(v.y for v in hits))*.5+.003)
            clearance=max(1.,max(math.hypot((v.x-cx)/rx,(v.y-cy)/ry) for v in hits))
            collar_sections.append((cx,cy,rx*clearance,ry*clearance))
        else:collar_sections.append((0,-.017,.068-.020*t,.062-.016*t))
    for row in range(rows):
        t=row/(rows-1)
        for i in range(cols):
            # A broad front opening and lower anterior rim avoid a rigid ring
            # extending beneath the chin when fitting against jaw geometry.
            opening=.38+.12*t
            a=-math.pi/2+opening+(math.tau-2*opening)*i/(cols-1)
            front=max(0,-math.sin(a))**3
            z=1.419+(.110-.008*front)*t
            cx,cy,rx,ry=collar_sections[row]
            vv.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
            if row and i:
                a,b,c,d=(row-1)*cols+i-1,(row-1)*cols+i,row*cols+i,row*cols+i-1
                ff.extend(((a,b,c),(a,c,d)))
    collar=add(mesh_object(p['name']+'-standing-collar',vv,ff,crystal),'standing-collar')
    collar['neck_clearance_metres']=.003
    for face in collar.data.polygons:face.use_smooth=True
    colour=collar.data.color_attributes.new(name='CollarSapphireTint',type='FLOAT_COLOR',domain='CORNER')
    for face in collar.data.polygons:
        band=(face.index//2)%(cols-1)
        tint=(.12,.10,.60) if band%12<6 else (.10,.25,.46)
        for loop in face.loop_indices:colour.data[loop].color=(*tint,1)
    collar.data.color_attributes.active_color=colour;collar['facet_tint_required']=True
    modifier=collar.modifiers.new('Fitted collar thickness','SOLIDIFY');modifier.thickness=thickness
    bpy.context.view_layer.objects.active=collar;bpy.ops.object.modifier_apply(modifier=modifier.name)
    rim=[vv[(rows-1)*cols+i] for i in range(cols)]
    line('collar-rim',rim,[.00085]*cols,metal,6)
    for column in (0,cols-1):
        edge=[tuple(Vector(vv[row*cols+column])+Vector((0,-.0005,0))) for row in range(rows)]
        line('collar-front-edge',edge,[.00075]*rows,metal,6)
    # Narrow diagonal silver inlays follow the fitted collar vertices instead
    # of a flat rectangle hovering in front of the neck.
    for side in (-1,1):
        panel=[]
        for row in range(rows):
            column=2+(rows-1-row)*.42
            if side<0:column=cols-1-column
            index=int(column);v=Vector(vv[row*cols+index]).lerp(Vector(vv[row*cols+index+1]),column-index)
            out=Vector((v.x,v.y+.017,0)).normalized()
            panel.append(tuple(v+out*.0012))
        line('collar-diagonal-inlay',panel,[.0012]*rows,metal,6)
    head_accessory_start=len(parts)
    # Shape the existing fitted scalp into one swept volume. The old separate
    # crown plus thick parallel tubes looked like a rigid hat above the head.
    if p['updo']:
        from mathutils.bvhtree import BVHTree
        from portrait_hair_surface import add_strand_normal, add_strand_colour, surface_lock
        scalp=next(o for o in head_parts if o.name.startswith('fitted-none'))
        groom_skull=BVHTree.FromPolygons([v.co for v in head_obj.data.vertices],
                                       [f.vertices[:] for f in head_obj.data.polygons])
        groom_origin=Vector((0,-.025,1.70));groom_clearance_count=0
        for vertex in scalp.data.vertices:
            v=vertex.co;t=max(0,min(1,(v.z-1.705)/.095))
            # A diagonal raised crown roll follows the requested updo. The Gaussian
            # displacement changes the silhouette without a second cap or the
            # old tower of identical tubes.
            crown=t*t
            diagonal=v.x+.028+.22*(v.y+.045)
            roll=math.exp(-(diagonal/.060)**2)*max(0,min(1,(-v.y+.055)/.13))*crown
            root_blend=max(0,min(1,(v.z-1.744)/.036));root_blend=root_blend*root_blend*(3-2*root_blend)
            puff=math.exp(-((v.z-1.769)/.038)**2-((v.x-.010)/.055)**2)*max(0,min(1,(-v.y+.025)/.10))*root_blend
            v.z+=.014*crown+.028*puff
            v.x+=.005*puff
            v.y-=.002*crown+.009*puff
            # A tucked root band leads into an elevated rearward sweep. This
            # breaks the formerly straight vertical front of the helmet cap.
            groom_front=max(0,min(1,(-v.y-.010)/.10))
            groom_root=math.exp(-((v.z-1.755)/.010)**2)*groom_front
            groom_crest=math.exp(-((v.z-1.784)/.022)**2-((v.x-.010)/.060)**2)*groom_front
            v.y+=.002*groom_root-.006*groom_crest
            v.z+=.011*groom_crest
            # Broad asymmetric furrows break the cap highlight while keeping
            # a single continuous supporting volume underneath every lock.
            angle=math.atan2(v.x,-v.y-.025)
            relief=.0009*math.sin(angle*13-8*crown)*root_blend
            v.y-=relief*max(0,math.cos(angle));v.z+=relief*crown
            # Enforce support clearance against the actual fitted skull.
            # Recessing roots must never expose skin through the hair shell.
            groom_ray=v-groom_origin
            groom_hit,_,_,_=groom_skull.ray_cast(groom_origin,groom_ray.normalized())
            if groom_hit is not None and groom_ray.length<(groom_hit-groom_origin).length+.0018:
                v[:]=groom_hit+groom_ray.normalized()*.0018;groom_clearance_count+=1
        scalp.data.update();scalp['froge_role']='swept-updo'
        scalp['root_clearance_corrected_vertices']=groom_clearance_count
        scalp['groom_revision']='raised-swept-crest-r11'
        uv=scalp.data.uv_layers.new(name='SweptHairFlow')
        for face in scalp.data.polygons:
            values=[]
            for idx in face.vertices:
                v=scalp.data.vertices[idx].co
                a=math.atan2(v.x,-v.y-.025)
                ray=(v-Vector((0,-.025,1.70))).normalized()
                polar=math.acos(max(-1,min(1,ray.z)))
                t=max(0,min(1,(1.55-polar)/1.31))
                # Inverse of the real lock sweep: fine strands travel along
                # the locks instead of forming a crossing herringbone pattern.
                sweep=.88-.56*max(0,math.cos(a))**4
                values.append(((a-sweep*math.sin(t*math.pi*.72))/math.tau+.5,t))
            seam=max(u for u,v in values)-min(u for u,v in values)>.5
            for loop,(u,v) in zip(face.loop_indices,values):uv.data[loop].uv=(u+1 if seam and u<.5 else u,v)
        # Two warm brown values and curved lock sections give broad, directed
        # highlights. Both materials export ordinary glTF strand normal maps.
        source_rgb=tuple(hair.get('couture_original_rgb',hair.diffuse_color[:3]))
        hair['couture_original_rgb']=source_rgb
        groom_reference=photo_surface.has_guide(p.get('_photo_fit'))
        # This pipeline deliberately stores display/sRGB in diffuse_color.
        # Brighter brown is an authored correction for this reference only,
        # not an encoding repair or a measured lighting-free pigment.
        lock_material=hair.copy();lock_material.name=p['name']+'-warm-hair-locks'
        lock_rgb=(.090,.054,.035) if groom_reference else tuple(min(.9,c*1.72) for c in source_rgb)
        lock_material.diffuse_color=(*lock_rgb,1)
        lock_shader=lock_material.node_tree.nodes.get('Principled BSDF')
        lock_shader.inputs['Base Color'].default_value=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in lock_rgb)+(1,)
        lock_shader.inputs['Roughness'].default_value=.43
        lock_shader.inputs['Specular IOR Level'].default_value=.12
        lock_shader.inputs['Anisotropic'].default_value=.42
        add_strand_normal(scalp,[hair,lock_material])
        shader=hair.node_tree.nodes.get('Principled BSDF')
        base_rgb=(.071,.042,.029) if groom_reference else tuple(min(.9,c*1.67) for c in source_rgb)
        hair.diffuse_color=(*base_rgb,1)
        shader.inputs['Base Color'].default_value=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in base_rgb)+(1,)
        shader.inputs['Roughness'].default_value=.59
        shader.inputs['Specular IOR Level'].default_value=.15
        shader.inputs['Anisotropic'].default_value=.42
        lock_shader.inputs['Roughness'].default_value=.56
        lock_shader.inputs['Specular IOR Level'].default_value=.18
        lock_shader.inputs['Anisotropic'].default_value=.48
        for mat,strength in ((hair,.34),(lock_material,.38)):
            node=mat.node_tree.nodes.get('Principled BSDF')
            node.inputs['Metallic'].default_value=0
            node.inputs['Coat Weight'].default_value=0
            node.inputs['IOR'].default_value=1.48
            for node in mat.node_tree.nodes:
                if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=strength
        add_strand_colour([hair,lock_material])
        scalp['hair_pigment_authored_reference']=bool(groom_reference)
        bun_centre=Vector((.004,.071,1.703));bun_radii=Vector((.051,.039,.072))
        bun=add(ellipsoid(p['name']+'-updo-back',bun_centre,bun_radii,hair,4),'updo-volume')
        # Overlapping diagonal rolls replace the perfectly spherical bun.
        # Surface samples use the same ellipsoid as the underlying volume.
        bun_folds=[]
        for i in range(15):
            phase=math.tau*i/15;samples=[]
            for j in range(38):
                t=j/37;a=-1.47+2.94*t;turn=phase+.70*math.sin(a)
                unit=Vector((math.sin(turn)*math.cos(a),math.cos(turn)*math.cos(a),math.sin(a)))
                point=bun_centre+Vector(tuple(unit[k]*bun_radii[k] for k in range(3)))
                normal=Vector(tuple(unit[k]/bun_radii[k] for k in range(3))).normalized()
                samples.append((point,normal))
            bun_folds.append(surface_lock('updo-fold',samples,.008,.0028,lock_material,mesh_object))
        add(join_meshes(bun_folds,p['name']+'-updo-folds'),'updo-folds')
        # Fine surface-following filaments supplement the exported normal map.
        # They are less than 0.5 mm across and cannot form a separate hair shell.
        surface=BVHTree.FromPolygons([v.co for v in scalp.data.vertices],[f.vertices[:] for f in scalp.data.polygons])
        origin=Vector((0,-.025,1.70));dz=Vector((0,0,1.64-eye_mid.z))
        roots={};detail_surface=None
        def trace(phase,t):
            if phase not in roots:
                # Find the actual lower scalp border instead of starting on
                # a fixed latitude above it. Ends stay embedded at the roots.
                roots[phase]=1.25
                for k in range(101):
                    polar=2.35-1.75*k/100
                    direction=Vector((math.sin(phase)*math.sin(polar),-math.cos(phase)*math.sin(polar),math.cos(polar)))
                    hit,_,_,_=surface.ray_cast(origin,direction)
                    if hit is not None:
                        roots[phase]=polar-.012;break
            # Frontal fibres continue over the crown instead of all ending
            # on its near slope, which made the tips form scalloped curls.
            groom_tip=.20+.07*math.sin(phase)-.32*max(0,math.cos(phase))**4
            polar=roots[phase]*(1-t)+groom_tip*t
            sweep=.88-.56*max(0,math.cos(phase))**4
            # Frontal roots first rise almost straight back; the turn gathers
            # gradually into the crown instead of diagonal parallel ropes.
            a=phase+sweep*math.sin(t*math.pi*.72)+.032*math.sin(phase*3.1)*math.sin(math.pi*t)**2
            direction=Vector((math.sin(a)*math.sin(polar),-math.cos(a)*math.sin(polar),math.cos(polar)))
            hit,normal,_,_=surface.ray_cast(origin,direction)
            if hit is None:return None
            if (hit-origin).dot(normal)<0:normal=-normal
            if detail_surface is not None:
                outer,outer_normal,_,_=detail_surface.ray_cast(hit+normal*.025,-normal,.030)
                if outer is not None:
                    hit=outer;normal=outer_normal
                    if (hit-origin).dot(normal)<0:normal=-normal
            return hit+dz,normal
        # Closed flattened locks follow the cranium instead of round wires or
        # disconnected flat ribbons. Endpoints are tapered into the base.
        locks=[]
        # Broad, unequal lifted rolls give the front its rounded structure.
        # They remain buried at both ends; fine strands are ray-fitted to the
        # completed rolls below, rather than hovering above the old scalp.
        for roll_index in range(11):
            roll_phase=-1.0+roll_index*.183+.041*math.sin(roll_index*1.9)
            roll_end=.95+.025*math.sin(roll_index*1.43+.2)
            roll_samples=[sample for j in range(46) if (sample:=trace(roll_phase,roll_end*j/45)) is not None]
            if len(roll_samples)>8:
                roll_width=.0074+.0022*math.sin(roll_index*1.37+.4)
                roll_depth=.0035+.0015*math.sin(roll_index*1.11+.6)
                locks.append(surface_lock('rounded-front-roll',roll_samples,roll_width,roll_depth,lock_material,mesh_object))
        for i in range(36):
            phase=math.tau*(i+.31)/36+.033*math.sin(i*1.7)
            end=.87+.13*(.5+.5*math.sin(i*2.17+.6))
            samples=[sample for j in range(46) if (sample:=trace(phase,end*j/45)) is not None]
            if len(samples)>8:
                front=max(0,math.cos(phase))**3
                # Uneven shallow sections retain strand relief without the
                # repeated swollen ropes seen in the previous actual export.
                depth=(.0008+.0009*front)*(.82+.20*math.sin(i*1.73+.4))
                lock_width=.0051+.0021*math.sin(i*2.4)+.0008*math.sin(i*4.13+.7)
                locks.append(surface_lock('swept-updo-lock',samples,lock_width,depth,lock_material,mesh_object))
        if locks:
            obj=add(join_meshes(locks,p['name']+'-swept-updo-locks'),'updo-locks');obj['lock_count']=len(locks)
            obj['groom_revision']='asymmetric-reference-crest-r10'
            # Filaments must rest on the finished locks, not float at a
            # constant offset above the old smooth scalp underneath them.
            verts=[v.co.copy() for v in scalp.data.vertices]
            faces=[f.vertices[:] for f in scalp.data.polygons]
            base=len(verts)
            verts.extend(v.co-dz for v in obj.data.vertices)
            faces.extend(tuple(base+i for i in f.vertices) for f in obj.data.polygons)
            detail_surface=BVHTree.FromPolygons(verts,faces)
        strands=[]
        for i in range(204):
            phase=math.tau*(i+.37)/204+.009*math.sin(i*2.17);points=[]
            for j in range(38):
                t=j/37;sample=trace(phase,t)
                if sample is not None:
                    hit,normal=sample
                    lift=.00010+.00020*max(0,math.sin(math.pi*t))**.7
                    points.append(tuple(hit+normal*lift))
            if len(points)>2:
                radii=[.000025+.000060*max(0,math.sin(math.pi*j/(len(points)-1)))**.6 for j in range(len(points))]
                strands.append(tube('fine-updo-filament',points,radii,lock_material,4))
        if strands:add(join_meshes(strands,p['name']+'-fine-updo-filaments'),'updo-filaments')
        baby_hairs=[]
        for i in range(83):
            phase=-1.40+2.8*i/82+.008*math.sin(i*2.7)
            samples=[sample for j in range(30) if (sample:=trace(phase,j/100)) is not None]
            if len(samples)<3:continue
            root,normal=samples[0];end=samples[min(5,len(samples)-1)][0]
            tangent=(end-root).normalized();length=.002+.002*(.5+.5*math.sin(i*2.1))
            start=root-tangent*length;points=[]
            for j in range(12):
                t=j/11
                points.append(tuple(start.lerp(end,t)+normal*(.0003+.0011*math.sin(math.pi*t))))
            baby_hairs.append(tube('hairline-wisp',points,[.0001+.000025*math.sin(math.pi*j/11) for j in range(12)],hair,4))
        if baby_hairs:add(join_meshes(baby_hairs,p['name']+'-hairline-wisps'),'hairline-wisps')
    # Gemstone earrings and hair ornament are fully three-dimensional.
    for side in (-1,1):
        line('earring-chain',[(side*.076,-.018,1.61),(side*.084,-.022,1.584)],[.0012,.0012],metal,8)
        outline=[(-.013,-.020),(.013,-.020),(0,.029)]
        vv,ff=geometry.cut_jewel(outline,.006)
        gem=add(mesh_object(p['name']+'-earring',vv,ff,crystal),'earring');gem.location=(side*.084,-.024,1.561)
        edges=[]
        for a,b in zip(outline,outline[1:]+outline[:1]):
            edges.append(tube('earring-rim',[(a[0]+side*.084,-.024,a[1]+1.561),(b[0]+side*.084,-.024,b[1]+1.561)],[.00055]*2,metal,6))
        add(join_meshes(edges,p['name']+'-earring-rim'),'earring-rim')
    if p['hair_ornament']:
        ornaments=[((.044,-.071,1.755),[(-.043,-.010),(.018,.052),(.033,.050),(-.006,-.012)]),
                   ((.062,-.066,1.745),[(-.029,.019),(.034,-.005),(.024,-.041)]),
                   ((.078,-.049,1.743),[(-.020,.018),(.018,-.004),(.012,-.045)])]
        edges=[]
        for centre,outline in ornaments:
            vv,ff=geometry.cut_jewel(outline,.008)
            obj=add(mesh_object(p['name']+'-hair-jewel',vv,ff,crystal),'hair-ornament');obj.location=centre
            for face in ff[:len(outline)]:
                for a,b in zip(face,face[1:]+face[:1]):
                    edges.append(tube('jewel-facet-rim',[tuple(Vector(centre)+Vector(vv[i])) for i in (a,b)],[.00042]*2,metal,5))
        add(join_meshes(edges,p['name']+'-hair-jewel-rims'),'hair-ornament-rims')
    bpy.context.view_layer.update()
    _,head_turn,_=portrait_transforms(portrait_plan)
    for obj in parts[head_accessory_start:]:obj.matrix_world=head_turn@obj.matrix_world
    if p['fan']['enabled']:
        f=p['fan'];pivot=fan_pivot
        handle=line('fan-grip-handle',[tuple(pivot+Vector((0,0,z))) for z in (-.053,-.012,.030)],
                    [.0075,.009,.006],shoe,16)
        handle['fan_grip_handle']=True
        chain=[tuple(pivot+Vector((.010+.009*t,-.012,.006-.173*t))) for t in (0,.2,.4,.6,.8,1)]
        line('fan-pendant-chain',chain,[.0006]*len(chain),metal,6)
        vv,ff=geometry.cut_jewel([(-.010,0),(0,.026),(.010,0),(0,-.024)],.008)
        pendant=add(mesh_object(p['name']+'-fan-pendant',vv,ff,crystal),'fan-pendant')
        pendant.location=Vector(chain[-1])+Vector((0,0,-.018))
        # Use the existing dark finish for the narrow open frames; broad white
        # specular reflections made the previous housings look chrome plated.
        dark_shader=shoe.node_tree.nodes.get('Principled BSDF')
        dark_shader.inputs['Specular IOR Level'].default_value=.10
        dark_shader.inputs['Roughness'].default_value=.48
        rotor_radius=geometry.fan_rotor_radius(f['radius'],f['spread'],f['rotors'])
        hole_radius=rotor_radius*1.12
        # Full closed crystal leaves end below the window strip. Narrow solid
        # tips rise between housings; no Boolean can delete the fan's filling.
        panel_radius=(f['radius']*.91-hole_radius-f['radius']*.010)/1.025
        vv,ff,slots=geometry.fan(panel_radius,f['panels'],f['spread'],thickness)
        fan=add(mesh_object(p['name']+'-pleated-fan',vv,ff,dress),'pleated-fan')
        fan.location=pivot;fan.data.materials.append(crystal);fan.data.materials.append(metal)
        for face,index in zip(fan.data.polygons,slots):face.material_index=index
        photo_surface.bind(fan,reference_material,
            lambda co:photo_surface.fan_uv(co,panel_radius,f['spread']))
        # Standard GLB corner colours give each real crystal plane its own
        # emerald/cyan/blue value. Shared materials keep the export budget.
        tint=fan.data.color_attributes.new(name='GemFacetTint',type='FLOAT_COLOR',domain='CORNER')
        palette=((.10,1.,.23),(.12,.94,1.),(.09,.30,1.),(.16,1.,.52))
        faces_per_leaf=len(ff)//f['panels']
        for face in fan.data.polygons:
            leaf,facet=divmod(face.index,faces_per_leaf)
            # Coherent long emerald/cyan leaves, with dark alternating facets.
            # Colour boundaries follow geometry instead of random triangles.
            rgb=palette[(leaf+(1 if facet%4==3 else 0))%len(palette)]
            shade=(.36,.86,1.,.54)[facet%4]
            for loop in face.loop_indices:
                tint.data[loop].color=(1,1,1,1) if reference_material else tuple(c*shade for c in rgb)+(1,)
        fan.data.color_attributes.active_color=tint;fan['facet_tint_required']=True
        # Only the scalloped outside edge is metal. Internal triangles read
        # through their actual plane normals and colour, without a wire lattice.
        outlines=[]
        for i in range(f['panels']):
            start=i*24
            points=[tuple(pivot+Vector(vv[start+j])+Vector((0,-.0003,0))) for j in (9,10,11)]
            outlines.append(tube('fan-outer-edge',points,[.00048]*3,metal,6))
        if outlines:
            edges=add(join_meshes(outlines,p['name']+'-fan-outer-rim'),'fan-outer-rim')
            edges['edge_count']=2*len(outlines)
        fan['panel_count']=f['panels'];fan['rotor_count']=f['rotors']
        for i in range(f['panels']+1):
            a=-f['spread']/2+f['spread']*i/f['panels']
            tip=pivot+Vector((f['radius']*.970*math.sin(a),-.0007,f['radius']*.970*math.cos(a)))
            line('fan-rib',[tuple(pivot),tuple(tip)],[.0010,.00055],metal,8)
        margin=f['spread']/(2*f['rotors'])
        centers=geometry.radial_positions(f['rotors'],f['radius']*.91,-f['spread']/2+margin,
                                          f['spread']-2*margin,tuple(pivot+Vector((0,-.012,0))))
        # The deeper gemstone folds must not swallow the turbine blades.
        # Mount every turbine against its own actual front-facing facet.
        fan_surface=BVHTree.FromPolygons([v.co for v in fan.data.vertices],[face.vertices[:] for face in fan.data.polygons])
        for i,centre in enumerate(centers):
            x,y,z=Vector(centre)-pivot
            hit,_,_,_=fan_surface.ray_cast(Vector((x,-.10,z)),Vector((0,1,0)))
            if hit is not None:centers[i]=(centre[0],pivot.y+hit.y-.006,centre[2])
        surrounds=[];step=(f['spread']-2*margin)/(f['rotors']-1)
        for i in range(f['rotors']):
            angle=-f['spread']/2+margin+step*i
            wv,wf=geometry.window_surround(f['radius'],angle,step/2,hole_radius,thickness)
            surround=mesh_object('fan-fitted-window-surround',wv,wf,crystal);surround.location=pivot
            surrounds.append(surround)
        fan=join_meshes([fan,*surrounds],p['name']+'-pleated-fan')
        # New shards have no inherited colour layer. Joining must not leave
        # their default alpha at zero in the exported COLOR_0 attribute.
        for colour in fan.data.color_attributes.active_color.data:
            if colour.color[3]<.5:colour.color=(1,1,1,1)
        window_surface=BVHTree.FromPolygons([v.co for v in fan.data.vertices],[face.vertices[:] for face in fan.data.polygons])
        for centre in centers:
            local=Vector(centre)-pivot
            if window_surface.ray_cast(Vector((local.x,-.10,local.z)),Vector((0,1,0)))[0] is not None:
                raise ValueError('Fan turbine window is still blocked by a panel')
        fan['open_turbine_windows']=len(centers)
        fan['fitted_window_surrounds']=True
        fan['turbine_window_centers']=[v for c in centers for v in Vector(c)-pivot]
        fan['turbine_window_radius']=hole_radius
        contour=[]
        for i in range(f['rotors']):
            angle=-f['spread']/2+margin+step*i
            for da,r in ((-step*.5,.973),(0,.992),(step*.5,.973)):
                point=tuple(pivot+Vector((f['radius']*r*math.sin(angle+da),-.012,
                                         f['radius']*r*math.cos(angle+da))))
                if not contour or (Vector(point)-Vector(contour[-1])).length>1e-7:contour.append(point)
        line('fan-dark-continuous-outline',contour,[.00070]*len(contour),shoe,6)
        template=rotor({'name':p['name']+'-fan-rotor','center':centers[0],
            'radius':rotor_radius,'depth':.008,'blades':6},metal,crystal,mesh_object)
        fv,ff=geometry.turbine_frame(hole_radius,rotor_radius*1.24,.009)
        guard=mesh_object('fan-dark-open-frame',fv,ff,shoe);guard.location=Vector(centers[0])+Vector((0,.0065,0))
        braces=[]
        for j in range(3):
            a=math.tau*j/3
            points=[tuple(Vector(centers[0])+Vector((r*math.sin(a),.004,r*math.cos(a))))
                    for r in (.002,rotor_radius*1.23)]
            braces.append(tube('fan-hub-brace',points,[.0007]*2,shoe,6))
        mount=tube('fan-turbine-mount',[tuple(Vector(centers[0])+Vector((0,d,0))) for d in (.003,.008)],[.0035]*2,metal,12)
        template=join_meshes([template,guard,mount,*braces],p['name']+'-fan-rotor');template['blade_count']=6
        template['open_frame']=True
        add(template,'fan-rotor')
        for i,center in enumerate(centers[1:],1):
            obj=template.copy();obj.name=p['name']+'-fan-rotor-%02d'%i;obj.location=center
            bpy.context.collection.objects.link(obj);add(obj,'fan-rotor')
    # Place contacts against the completed prop surface. This also adapts the
    # grip when panel count/radius/relief changes; guessed coordinates alone
    # left several fingertips hovering beside the handle.
    bpy.context.view_layer.update()
    prop=[o for o in parts if o.get('froge_role') in ('pleated-fan','fan-grip-handle')]
    for hand_plan,holding in hand_jobs:
        if holding:
            vertices=[];faces=[]
            for obj in prop:
                start=len(vertices);vertices.extend(obj.matrix_world@v.co for v in obj.data.vertices)
                faces.extend(tuple(start+i for i in f.vertices) for f in obj.data.polygons)
            grip_surface=BVHTree.FromPolygons(vertices,faces)
            contacts=[]
            for finger,point in enumerate(hand_plan['grip_contacts']):
                hit,normal,_,distance=grip_surface.find_nearest(Vector(point))
                if hit is None or distance>.04:raise ValueError('Fan grip has no nearby prop surface')
                # Distal landmarks sit close to the skin surface, not at the
                # centre of a 4 mm finger cross-section. A 2 mm offset avoids
                # the visible gap revealed by the actual-mesh contact check.
                # The thicker thumb pad needs more clearance than the long
                # fingers. The previous common offset cut it into the fan.
                contacts.append(tuple(hit+normal*(.003 if finger==0 else .002)))
            hand_plan['grip_contacts']=contacts
        built_hand=build_hand(hand_plan,skin,nails,mesh_object)
        parts+=built_hand
        built_hand[0]['couture_pose_revision']='upright-grip-clear-free-hand-r2'
        if holding:
            hand_mesh=built_hand[0]
            hand_surface=BVHTree.FromPolygons([v.co for v in hand_mesh.data.vertices],
                                            [f.vertices[:] for f in hand_mesh.data.polygons])
            wrist=Vector(hand_plan['wrist']);axis=Vector(hand_plan['direction']).normalized()
            normal=Vector((0,-1,0));across=axis.cross(normal).normalized()
            leather=shoe.copy();leather.name=p['name']+'-midnight-fingerless-glove'
            bsdf=leather.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value=(.008,.014,.018,1)
            bsdf.inputs['Metallic'].default_value=0;bsdf.inputs['Roughness'].default_value=.44
            forearm=Vector(hand_plan['forearm_direction']).normalized()
            wrist_swing=axis.rotation_difference(forearm)
            wrist_faces=[]
            for face in hand_mesh.data.polygons:
                delta=sum((hand_mesh.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)-wrist
                if delta.dot(axis)<.030 and delta.length<.070:
                    wrist_faces.append(face.vertices[:])
            wrist_surface=BVHTree.FromPolygons([v.co for v in hand_mesh.data.vertices],wrist_faces)
            shaped('glove-wrist-seam',[(*tuple(wrist-forearm*.031),.029,.026),
                (*tuple(wrist-forearm*.014),.031,.028),(*tuple(wrist),.030,.027)],leather,32)
            # Sample an entire circumferential shell against the actual posed
            # palm. Its distal edge leaves the fingers and their nails bare.
            outer=[];inner=[];rows=25;sides=40
            for j in range(rows):
                t=j/(rows-1)
                for k in range(sides):
                    angle=math.tau*k/sides
                    end=.043+.035*max(0,math.cos(angle))**4
                    along=-.021+(end+.021)*t
                    center=wrist+(Vector(hand_plan['forearm_direction']) if along<0 else axis)*along
                    ray=normal*math.cos(angle)+across*math.sin(angle)
                    if along<0:
                        # Match the wrist bend used by the underlying hand.
                        # A fixed palm frame casts obliquely through the bent
                        # wrist and leaves the thumb-side crescent uncovered.
                        blend=min(1.,-along/.020);blend=blend*blend*(3-2*blend)
                        ray=Quaternion((1,0,0,0)).slerp(wrist_swing,blend)@ray
                    # Bent-wrist rays must not hit a curled finger on the
                    # far side of the palm and stretch leather across it.
                    surface=wrist_surface if along<0 else hand_surface
                    hit,n,_,_=surface.ray_cast(center+ray*.12,-ray,.24)
                    if hit is None:raise ValueError('Fingerless glove cannot wrap the posed palm')
                    if n.dot(ray)<0:n=-n
                    # Extend only the cuff lip into the sleeve; do not alter
                    # the hand or let side rays bridge the finger web spaces.
                    hit-=Vector(hand_plan['forearm_direction'])*(.009*(1-t)**10)
                    outer.append(tuple(hit+n*.0015));inner.append(tuple(hit+n*.0005))
            count=len(outer);faces=[]
            for j in range(rows-1):
                for k in range(sides):
                    a=j*sides+k;b=j*sides+(k+1)%sides;c=b+sides;d=a+sides
                    faces.extend(((a,b,c,d),(count+d,count+c,count+b,count+a)))
            for j in (0,rows-1):
                for k in range(sides):
                    a=j*sides+k;b=j*sides+(k+1)%sides
                    faces.append((a,count+a,count+b,b) if j==0 else (b,count+b,count+a,a))
            glove=add(mesh_object(p['name']+'-fitted-palm-glove',outer+inner,faces,leather),'fitted-palm-glove')
            import bmesh
            bm=bmesh.new();bm.from_mesh(glove.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(glove.data);bm.free()
            for face in glove.data.polygons:face.use_smooth=True
            glove['fitted_to_posed_hand']=True;glove['fingerless_wrap_samples']=count
            glove['actual_shell_thickness_m']=.001
            # Broad unequal triangular facets form one folded metal surface
            # over the leather, following the reference's angular gauntlet.
            panels=[];rim_parts=[]
            def glove_point(along,lateral,lift):
                q=wrist+axis*along+across*lateral
                hit,_,_,_=hand_surface.ray_cast(q+normal*.09,-normal,.18)
                if hit is None:raise ValueError('Glove facet left the palm')
                return hit+normal*lift
            glove_metal=metal.copy();glove_metal.name=p['name']+'-pewter-glove-facets'
            shader=glove_metal.node_tree.nodes.get('Principled BSDF')
            shader.inputs['Base Color'].default_value=(.19,.16,.12,1)
            shader.inputs['Metallic'].default_value=.78;shader.inputs['Roughness'].default_value=.30
            stations=[(-.004,.017),(.016,.021),(.037,.023),(.058,.023),(.077,.020)]
            patch=[]
            for row,(s,w) in enumerate(stations):
                patch.append([(s,-w),(s+.004*math.sin(row*1.7),.002*math.sin(row)),(s,w)])
            for row in range(4):
                for column in range(2):
                    a,b,c,d=patch[row][column],patch[row][column+1],patch[row+1][column+1],patch[row+1][column]
                    for corners in ((a,b,c),(a,c,d)):
                        s=sum(q[0] for q in corners)/3;lateral=sum(q[1] for q in corners)/3
                        corners=[(s+(q[0]-s)*.985,lateral+(q[1]-lateral)*.985) for q in corners]
                        vv=[];ff=[];n=4
                        for edge in range(3):
                            a,b=corners[edge],corners[(edge+1)%3];ids={}
                            for i in range(n+1):
                                for j in range(n+1-i):
                                    u=i/n;v=j/n
                                    along=a[0]*(1-u-v)+b[0]*u+s*v
                                    across_value=a[1]*(1-u-v)+b[1]*u+lateral*v
                                    ids[i,j]=len(vv);vv.append(tuple(glove_point(along,across_value,.0026+.0018*v)))
                            for i in range(n):
                                for j in range(n-i):
                                    ff.append((ids[i,j],ids[i+1,j],ids[i,j+1]))
                                    if j<n-i-1:ff.append((ids[i+1,j],ids[i+1,j+1],ids[i,j+1]))
                        pv,pf=geometry.shell(vv,ff,.00065)
                        panels.append(mesh_object('glove-folded-triangle',pv,pf,glove_metal))
                        rim=[tuple(glove_point(a,b,.0029)) for a,b in corners+corners[:1]]
                        rim_parts.append(tube('glove-silver-hem',rim,[.00022]*4,glove_metal,5))
            panel=add(join_meshes(panels,p['name']+'-glove-facets'),'glove-facet-panels')
            panel['individual_raised_facets']=len(panels);panel['fitted_to_posed_hand']=True
            add(join_meshes(rim_parts,p['name']+'-glove-facet-edges'),'glove-facet-edges')
    # Uniform scale applies to geometry and accessories together.
    for obj in parts:
        if crystal in list(obj.data.materials):
            couture_uv(obj,planar=obj.get('froge_role') not in ('conformal-facets','standing-collar'))
        role=obj.get('froge_role')
        if role in ('fitted-gown','conformal-facets'):
            photo_surface.bind(obj,garment_reference,
                lambda co:photo_surface.garment_uv(co,p['hem_radius'],width),
                lambda face:sum(obj.data.vertices[i].co.y for i in face.vertices)/len(face.vertices)<-.003)
            if garment_reference:
                colour=obj.data.color_attributes.new(name='ReferenceClothTone',type='FLOAT_COLOR',domain='CORNER')
                for face in obj.data.polygons:
                    tint=(.42,.68,.63,1) if obj.data.materials[face.material_index]==garment_reference else (1,1,1,1)
                    for loop in face.loop_indices:colour.data[loop].color=tint
                obj.data.color_attributes.active_color=colour;obj['facet_tint_required']=True
                obj['reference_cloth_tone_authored']=True
        elif role=='shoulder-inlay':
            corners=((860,755),(1190,620),(1015,860),(870,850))
            anchors=[obj.data.vertices[i].co.copy() for i in range(4)]
            def shoulder_uv(co):
                index=min(range(4),key=lambda i:(co.x-anchors[i].x)**2+(co.z-anchors[i].z)**2)
                x,y=corners[index];return (x/1229,1-y/1536)
            photo_surface.bind(obj,reference_material,shoulder_uv,lambda face:face.material_index==0)
        elif role=='standing-collar':
            photo_surface.bind(obj,reference_material,
                lambda co:photo_surface.quad_uv(abs(co.x)/.075,(co.z-1.419)/.110,
                    ((827,709),(869,686),(844,600),(799,628))))
            if reference_material:
                for colour in obj.data.color_attributes.active_color.data:colour.color=(1,1,1,1)
    bpy.context.view_layer.update()
    factor=p['height']/1.88
    transform=Matrix.Translation(p['center'])@Matrix.Scale(factor,4)
    for obj in parts:
        obj.matrix_world=transform@obj.matrix_world
        obj['character']=p['name'];obj['characterStandard']=20
        obj['reference_likeness_verified']=False
        obj['observedFeatures']='; '.join(p['observed_features'])
        obj['reconstructedFeatures']='; '.join(p['reconstructed_features'])
    return parts
