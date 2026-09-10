"""Anatomical portrait component with bounded shape controls and portable detail.

The photo planner chooses proportions; this renderer never claims an identity
match. Skin is a generic CC0 atlas, not another person's portrait texture.
"""
import math
import random
import bpy
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
import anatomy
import portrait_shape


def head(p, skin, eyes, hair, mesh_object, ellipsoid):
    photo_fit=p.get('_photo_fit')
    if photo_fit is not None:
        # Calibration uses a neutral, dense feminine head. The photographed
        # residual replaces the seven authored proportions, rather than adding
        # a second deformation on top of an unrelated AI-selected face.
        p={**p,'face':{},'makeup':'soft_glam'}
    style=p.get('hair_style','short'); long=style in ('long_wavy','straight_bob','curly')
    parts=anatomy.head({**p,'hair_style':'bald' if long else 'short' if style=='ponytail' else style},skin,eyes,hair,mesh_object,ellipsoid)
    from portrait_eyes import apply_eye_albedo
    gaze=portrait_shape.measured_gaze(photo_fit.observation,photo_fit.template['observation']) if photo_fit is not None else (0.,0.)
    apply_eye_albedo(parts,eyes.diffuse_color[:3],gaze)
    obj=parts[0]
    obj['photo_skin_midtone_calibration']='makeup_rgb' in p
    # The cosmetic masks need sufficient surface samples around the eyelids and
    # lip border. Subdivide this head only, before sculpting and fitting details.
    if p.get('makeup')=='soft_glam':anatomy.subdivide(obj,1)
    cosmetic_coordinates=[v.co.copy() for v in obj.data.vertices]
    portrait_shape.sculpt(obj,p.get('face',{}))
    from portrait_orbits import relaxed_lid_point
    glam=p.get('makeup')=='soft_glam'
    from reference_surfaces import has_guide
    couture_orbits=photo_fit is not None and has_guide(photo_fit)
    # The reference's upper lid covers more of the iris. Narrow the connected
    # lid mesh before fitting brows/lashes; keep both globes and measured gaze.
    lid_strength=.48 if couture_orbits else .36 if glam else .20
    upper_lid_bias=.12 if couture_orbits else .08 if glam else 0
    for side in ('l','r'):
        center=anatomy.landmark(side+'-eye',p['presentation'])
        for vertex in obj.data.vertices:
            vertex.co=relaxed_lid_point(vertex.co,center,lid_strength,upper_lid_bias)
    obj.data.update()
    obj['reference_lid_aperture_authored']=bool(couture_orbits)
    obj['anatomical_head']=True;obj['quality_revision']=2
    # One front-facing iris per globe, including from the side and rear.
    for eye in parts:
        if not eye.name.startswith('anatomical-eye-'):continue
        eye['anatomical_eye']=True;eye['iris_count']=1
    brow_name='anatomical-matte-brows-'+hair.name
    brow_material=bpy.data.materials.get(brow_name)
    if brow_material is None:
        brow_material=hair.copy();brow_material.name=brow_name
    brow_shader=brow_material.node_tree.nodes['Principled BSDF']
    base=hair.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
    # Scalp colour/normal textures copied with the hair material must not
    # override this fine matte pigment (brow fibres have no scalp UV map).
    for socket in ('Base Color','Normal','Roughness'):
        for link in list(brow_shader.inputs[socket].links):
            brow_material.node_tree.links.remove(link)
    brow_shader.inputs['Base Color'].default_value=tuple(max(c*.65,floor) for c,floor in zip(base[:3],(.006,.0025,.0013)))+(1,)
    brow_shader.inputs['Roughness'].default_value=.78
    brow_shader.inputs['Specular IOR Level'].default_value=.12
    # Replace broad single-triangle hairs and the solid eyebrow underlay with
    # individually tapered round fibres. Gaps expose the measured skin colour;
    # all fibres are fitted before the one shared photo deformation below.
    for brow in list(parts):
        if brow.name.startswith('eyebrow'):
            parts.remove(brow);bpy.data.objects.remove(brow,do_unlink=True)
    surface=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[f.vertices[:] for f in obj.data.polygons])
    measured_brows={}
    if photo_fit is not None:
        # Use the very same measured contour as photo colour projection.
        # The authored arc stopped at x=.055 while the photographed eyebrow
        # extends to about .061: warping both did not cure that registration
        # error, leaving a bare grey second arc below the separate fibres.
        for side,upper,lower in (
            (-1,(107,66,105,63,70),(55,65,52,53,46)),
            (1,(336,296,334,293,300),(285,295,282,283,276))):
            rows=[]
            for a,b in zip(upper,lower):
                ax,az=photo_fit.template['surface_xz'][a]
                bx,bz=photo_fit.template['surface_xz'][b]
                rows.append(((abs(ax)+abs(bx))*.5,(az+bz)*.5,abs(az-bz)*.42))
            measured_brows[side]=rows
    def brow_section(t,side,eye_z):
        if side not in measured_brows:
            return (.012+.043*t,portrait_shape.brow_height(t,eye_z,glam),
                (.0035 if glam else .0017)*math.sin(math.pi*t)**.38*(1-.60*t))
        rows=measured_brows[side];index=min(3,int(t*4));weight=t*4-index
        return tuple(a+(b-a)*weight for a,b in zip(rows[index],rows[index+1]))
    rng=random.Random(1107)
    for side in (-1,1):
        vertices=[];faces=[];count=0
        eye_z=anatomy.landmark(('l' if side==1 else 'r')+'-eye',p['presentation']).z
        for i in range(420 if glam else 240):
            t=(i+rng.random())/(420 if glam else 240)
            bx,bz,band=brow_section(t,side,eye_z)
            x=side*bx
            z=bz+rng.uniform(-1,1)*band
            if side in measured_brows:
                z-=.00065*(1-t) # the rising fibre's centre stays in the contour
            length=rng.uniform(.0018,.0036)*(1-.40*t)
            # Inner hairs rise, central hairs sweep out and the tail descends.
            dx=side*length*(.16+.82*t)
            dz=length*(.88-1.18*t)
            radius=rng.uniform(.000070,.000105)*(1-.30*t)*(1.16 if couture_orbits else 1.)
            centers=[];normals=[]
            for k in range(5):
                u=k/4;xx=x+dx*u;zz=z+dz*u+.00025*math.sin(math.pi*u)
                hit,normal,_,_=surface.ray_cast(Vector((xx,-.5,zz)),Vector((0,1,0)))
                if hit is None:break
                # Keep the entire root cross-section above skin. Previously
                # its 75 micron lift was smaller than the 113 micron radius,
                # so the surface hid roots, especially after photo warping.
                centers.append(hit+normal*(.00027+.000075*math.sin(math.pi*u)))
                normals.append(normal)
            if len(centers)!=5:continue
            base=len(vertices)
            for k,center in enumerate(centers):
                tangent=(centers[min(k+1,4)]-centers[max(k-1,0)]).normalized()
                across=tangent.cross(normals[k]).normalized()
                normal=tangent.cross(across).normalized()
                r=radius*(1-k/4)**.7+.000008
                for j in range(4):
                    angle=math.tau*j/4
                    vertices.append(tuple(center+r*(math.cos(angle)*across+math.sin(angle)*normal)))
                if k:
                    for j in range(4):faces.append((base+(k-1)*4+j,base+(k-1)*4+(j+1)%4,base+k*4+(j+1)%4,base+k*4+j))
            faces.append(tuple(base+j for j in reversed(range(4))))
            faces.append(tuple(base+16+j for j in range(4)))
            count+=1
        brow=mesh_object('eyebrow-fibres',vertices,faces,brow_material)
        for polygon in brow.data.polygons:polygon.use_smooth=True
        brow['brow_fibre_count']=count;brow['brow_method']='surface-fitted-tapered-fibres'
        brow['brow_root_clearance_m']=.00027
        brow['brow_photo_contour_aligned']=bool(measured_brows)
        parts.append(brow)
    cosmetic=bpy.data.materials.get('anatomical-lashes')
    if cosmetic is None:
        cosmetic=bpy.data.materials.new('anatomical-lashes');cosmetic.use_nodes=True
        bsdf=cosmetic.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=(.005,.003,.002,1);bsdf.inputs['Roughness'].default_value=.7
    vv=[];ff=[];liner_vertices=[];liner_faces=[];lash_counts=[]
    def fibre(points,radius):
        # Closed round fibres remain visible at oblique camera angles. The old
        # flat two-vertex strips became edge-on or disappeared behind the lid.
        base=len(vv);sides=5
        for k,q in enumerate(points):
            tangent=(points[min(k+1,len(points)-1)]-points[max(k-1,0)]).normalized()
            across=tangent.cross(Vector((0,1,0))).normalized()
            other=tangent.cross(across).normalized()
            r=radius*(1-k/(len(points)-1))**.8+.000015
            for j in range(sides):
                a=math.tau*j/sides;vv.append(tuple(q+r*(math.cos(a)*across+math.sin(a)*other)))
            if k:
                for j in range(sides):ff.append((base+(k-1)*sides+j,base+(k-1)*sides+(j+1)%sides,base+k*sides+(j+1)%sides,base+k*sides+j))
        ff.append(tuple(base+j for j in reversed(range(sides))))
        ff.append(tuple(base+(len(points)-1)*sides+j for j in range(sides)))
    for side in ('l','r'):
        previous=None;count=0;outer_root=None
        center=anatomy.landmark(side+'-eye',p['presentation']);sign=1 if center.x>0 else -1
        for i in range(44):
            t=.08+.84*i/43;x=center.x+(.5-t)*.028*sign
            candidates=[]
            for j in range(90):
                z=center.z-.011+.022*j/89;r=((x-center.x)/.0147)**2+((z-center.z)/.0143)**2
                hit,_,_,_=surface.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)))
                if r<1 and hit is not None and hit.y>center.y-.0152*math.sqrt(1-r)+.00002:candidates.append(z)
            if not candidates:continue
            z=max(candidates)+.00022;r=((x-center.x)/.0147)**2+((z-center.z)/.0143)**2
            y=center.y-.0152*math.sqrt(max(0,1-r))-.0004
            hit,_,_,_=surface.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)))
            if hit is not None:y=min(y,hit.y-.00045)
            root=Vector((x,y,z));length=(.004+.005*(1-t))*(1. if glam else .6)
            if couture_orbits:length*=.91+.12*math.sin(i*2.37)+.055*math.sin(i*4.13)
            if outer_root is None:outer_root=root.copy()
            start=len(liner_vertices)
            for dz in (0,.0007+(.0011 if glam else 0)*(1-t)):
                hit,_,_,_=surface.ray_cast(Vector((x,-.4,z+dz)),Vector((0,1,0)))
                liner_vertices.append((x,min(y,hit.y-.0005 if hit is not None else y),z+dz))
            if previous is not None:liner_faces.append((previous,start,start+1,previous+1))
            previous=start
            points=[]
            for k in range(10):
                u=k/9;q=root+Vector((sign*length*.42*u*u,-length*.72*u,length*(.2*u+.65*u*u)))
                hit,_,_,_=surface.ray_cast(Vector((q.x,-.4,q.z)),Vector((0,1,0)))
                if hit is not None:q.y=min(q.y,hit.y-.00055)
                points.append(q)
            fibre(points,.00016 if glam else .00010);count+=1
        if glam and outer_root is not None:
            previous=None
            for j in range(16):
                t=j/15;x=outer_root.x+sign*.006*t
                z=outer_root.z+.003*t
                start=len(liner_vertices)
                for dz in (0,.0018*(1-t)+.00006):
                    hit,_,_,_=surface.ray_cast(Vector((x,-.4,z+dz)),Vector((0,1,0)))
                    liner_vertices.append((x,hit.y-.00055 if hit is not None else outer_root.y,z+dz))
                if previous is not None:liner_faces.append((previous,start,start+1,previous+1))
                previous=start
        lash_counts.append(count)
    lashes=mesh_object('anatomical-lash-fibres',vv,ff,cosmetic);parts.append(lashes)
    for polygon in lashes.data.polygons:polygon.use_smooth=True
    lashes['upper_lashes_per_eye']=lash_counts
    obj['lash_geometry_required']=True
    parts.append(mesh_object('anatomical-upper-eyeliner',liner_vertices,liner_faces,cosmetic))
    cosmetic_finish=[]
    if glam:
        # Portable vertex tint multiplies the subject-independent anatomical
        # albedo. No extra portrait plane, duplicate lips or external shader.
        attr=obj.data.color_attributes.new(name='CosmeticTint',type='FLOAT_COLOR',domain='POINT')
        for vertex in obj.data.vertices:
            x,y,z=vertex.co;front=max(0,min(1,(-.085-y)/.035));ax=abs(x)
            shadow=math.exp(-((ax-.036)/.019)**4-((z-1.6868-max(0,ax-.036)*.16)/.0045)**2)*.76*front
            blush=math.exp(-((ax-.05)/.02)**2-((z-1.650)/.012)**2)*.18*front
            # Lip colour travels with the sculpted vertices. The old fixed
            # world-height mask missed the lower lip after proportion edits.
            lx,ly,lz=cosmetic_coordinates[vertex.index];lax=abs(lx)
            upper=1.620+.0025*math.exp(-((lax-.008)/.0045)**2)-.011*(lax/.026)**1.7
            lower=1.601+.012*(lax/.026)**2
            lip=portrait_shape.step(lower-.001,lower+.001,lz)*(1-portrait_shape.step(upper-.001,upper+.001,lz))
            lip*=max(0,1-(lax/.027)**8)*.78*front
            if 'makeup_rgb' in p:
                tint=p['makeup_rgb'];shadow=min(.88,shadow*1.4)
                color=[1-shadow*(1-tint[0])-lip*.22,1-shadow*(1-tint[1])-blush-lip*.96,1-shadow*(1-tint[2])-blush*.75-lip*.88]
            else:
                color=[1-shadow*.38,1-shadow*.62-blush-lip,1-shadow*.67-blush*.75-lip*.55]
            attr.data[vertex.index].color=tuple(max(.01,min(1,c)) for c in color)+(1,)
            # Store masks on these same skin vertices before nonlinear fit.
            # The photo colour pass runs later and otherwise erases the
            # finishing pigment; recomputing masks in warped coordinates
            # would leave a second misplaced mouth or eyebrow behind.
            side=1 if x>0 else -1
            t=(ax-.012)/.043;brow_fill=0.
            if side in measured_brows:
                rows=measured_brows[side];t=-1.
                for j in range(4):
                    if rows[j][0]<=ax<=rows[j+1][0]:
                        t=(j+(ax-rows[j][0])/(rows[j+1][0]-rows[j][0]))/4
                        break
            if 0<t<1:
                eye_z=anatomy.landmark(('l' if x>0 else 'r')+'-eye',p['presentation']).z
                _,brow_z,band=brow_section(t,side,eye_z)
                if side not in measured_brows:brow_z+=.0007*(1-t)
                brow_fill=math.exp(-((z-brow_z)/max(.0003,band*.82))**4)
                brow_fill*=portrait_shape.step(0,.12,t)*(1-portrait_shape.step(.82,1,t))*.38*front
            cosmetic_finish.append((brow_fill,lip,shadow))
        nodes=skin.node_tree.nodes;links=skin.node_tree.links;bsdf=nodes['Principled BSDF']
        source=bsdf.inputs['Base Color'].links[0].from_socket
        col=nodes.new('ShaderNodeVertexColor');col.layer_name=attr.name
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        links.new(source,mix.inputs[1]);links.new(col.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        # Keep the tint connected in Blender, and export the active attribute
        # as COLOR_0 so the reimported GLB has the same image-times-makeup color.
        obj.data.color_attributes.active_color=attr
    if long and p['headwear']=='none':
        from portrait_hair import build_bob
        from portrait_locks import add_locks,wave
        sampler={};pieces=build_bob(obj,mesh_object,sampler,supplied_material=hair)
        if style=='long_wavy':
            for piece in pieces:
                for v in piece.data.vertices:v.co=wave(v.co)
            pieces+=add_locks(sampler['point'],mesh_object,supplied_material=hair)
        elif style=='straight_bob':
            for piece in pieces:
                for v in piece.data.vertices:
                    if v.co.z<1.73:v.co.z=1.73+(v.co.z-1.73)*.34
        elif style=='curly':
            for piece in pieces:
                for v in piece.data.vertices:v.co=wave(v.co)
            pieces+=add_locks(sampler['point'],mesh_object,supplied_material=hair,curl=True)
            for piece in pieces:
                for v in piece.data.vertices:
                    if v.co.z<1.73:v.co.z=1.73+(v.co.z-1.73)*.8
        for piece in pieces:piece.name='anatomical-'+style+'-hair'
        parts+=pieces
    elif style=='ponytail' and p['headwear']=='none':
        crown=max(v.co.z for v in obj.data.vertices)
        parts.append(ellipsoid('anatomical-ponytail-tie',(0,.026,crown+.004),(.032,.034,.025),hair,subdivisions=3))
        vv=[];ff=[]
        for strand in range(32):
            phase=strand*math.tau/32;base=len(vv)
            for j in range(42):
                t=j/41;radius=.014*(1-t)**.65+.0004
                center=Vector((radius*math.cos(phase),.042+.075*math.sin(t*math.pi*.75)+radius*math.sin(phase),crown-.004-.48*t))
                for k in range(6):
                    a=k*math.tau/6;r=.0028*(1-t)+.0001
                    vv.append(tuple(center+Vector((math.cos(a)*r,math.sin(a)*r,0))))
                if j:
                    for k in range(6):ff.append((base+(j-1)*6+k,base+j*6+k,base+j*6+(k+1)%6,base+(j-1)*6+(k+1)%6))
        parts.append(mesh_object('anatomical-ponytail-fine-strands',vv,ff,hair))
    if p.get('eyewear')=='sunglasses':
        from run import tube
        frame=bpy.data.materials.get('portrait-sunglasses')
        if frame is None:
            frame=bpy.data.materials.new('portrait-sunglasses');frame.use_nodes=True
            s=frame.node_tree.nodes['Principled BSDF'];s.inputs['Base Color'].default_value=(.008,.009,.012,1);s.inputs['Roughness'].default_value=.19
        for side in ('l','r'):
            eye=anatomy.landmark(side+'-eye',p['presentation']);sign=1 if eye.x>0 else -1
            center=eye+Vector((0,-.025,0))
            parts.append(ellipsoid('portrait-dark-lens',center,(.032,.003,.019),frame,subdivisions=3))
            chain=[tuple(center+Vector((.033*math.cos(i*math.tau/40),-.002,.020*math.sin(i*math.tau/40)))) for i in range(41)]
            parts.append(tube('portrait-glasses-frame',chain,[.002]*len(chain),frame,8))
            points=[tuple(center+Vector((sign*.031,0,.008))),tuple(Vector((sign*.077,-.065,eye.z+.006))),tuple(Vector((sign*.078,.008,eye.z-.008)))]
            parts.append(tube('portrait-glasses-temple',points,[.002]*3,frame,8))
        a=anatomy.landmark('l-eye',p['presentation']);b=anatomy.landmark('r-eye',p['presentation'])
        parts.append(tube('portrait-glasses-bridge',[(a.x*.15,-.145,a.z+.004),(0,-.155,a.z+.008),(b.x*.15,-.145,b.z+.004)],[.002]*3,frame,8))
    if photo_fit is not None:
        photo_fit.apply(parts)
    if glam:
        # Subtle warm brow density retains gaps between the actual fibres.
        # On measured reference faces, restore a small amount of terracotta
        # lip and emerald lid pigment after the photographed colour transfer.
        measured_couture=photo_fit is not None and 'makeup_rgb' in p
        for sample,(brow_fill,lip,shadow) in zip(attr.data,cosmetic_finish):
            color=list(sample.color[:3])
            for channel,pigment in enumerate((.18,.085,.045)):
                color[channel]*=1-brow_fill*(1-pigment)
            if measured_couture:
                for channel,(lip_pigment,lid_pigment) in enumerate(zip((.90,.66,.57),(.40,.77,.62))):
                    color[channel]*=(1-lip*.40*(1-lip_pigment))*(1-shadow*.24*(1-lid_pigment))
            sample.color=tuple(max(.003,min(1,c)) for c in color)+(1,)
        obj['cosmetic_finish_after_photo']=bool(measured_couture)
    return parts


def build_portrait(p, materials, mesh_object, ellipsoid):
    parts=head(p,materials[p['skin_material']],materials[p['eye_material']],materials[p['hair_material']],mesh_object,ellipsoid)
    # Primitive scale/location setters do not synchronously refresh matrix_world.
    # Reading a stale matrix here can turn an eyeglass lens into a metre sphere.
    bpy.context.view_layer.update()
    eye_center=(anatomy.landmark('l-eye',p['presentation'])+anatomy.landmark('r-eye',p['presentation']))*.5
    transform=Matrix.Translation(p['center'])@Euler(p['rotation']).to_matrix().to_4x4()@Matrix.Scale(p['scale'],4)@Matrix.Translation(-eye_center)
    for obj in parts:
        if obj.get('anatomical_head') and 'makeup_rgb' in p:
            # Turn the skull while anchoring the lower neck in its garment.
            # Rotating the entire cut neck about the eyes exposed its jagged
            # lower boundary outside the standing collar at stronger rolls.
            neutral=Matrix.Translation(p['center'])@Matrix.Scale(p['scale'],4)@Matrix.Translation(-eye_center)
            inverse=transform.inverted();anchored=0
            for vertex in obj.data.vertices:
                v=vertex.co.copy()
                weight=max(0.,min(1.,(v.z-1.485)/.110));weight=weight*weight*(3-2*weight)
                front=max(0.,min(1.,(-.065-v.y)/.045));front=front*front*(3-2*front)
                chin=max(0.,min(1.,(v.z-1.530)/.040));chin=chin*chin*(3-2*chin)
                weight+=(1-weight)*front*chin
                if weight<1:
                    vertex.co=inverse@((neutral@v).lerp(transform@v,weight));anchored+=1
            obj['neck_pose_anchored_vertices']=anchored
            obj['neck_pose_lower_anchor']=1.485
            obj.data.update()
        obj.matrix_world=transform@obj.matrix_world
    return parts


def verify_components(objects, expected_heads, expected_hands):
    heads=[o for o in objects if o.get('anatomical_head')]
    hands=[o for o in objects if o.get('anatomical_hand')]
    eyes=[o for o in objects if o.get('anatomical_eye')]
    nails=[o for o in objects if o.get('anatomical_nail')]
    if len(heads)!=expected_heads or len(hands)!=expected_hands or len(eyes)!=2*expected_heads or len(nails)!=5*expected_hands:
        raise ValueError('Standard postaci: brakuje anatomicznej twarzy, dwoch oczu, dloni lub paznokci. Wynik nie zostal zaakceptowany.')
    for obj,minimum in [(o,12000) for o in heads]+[(o,4500) for o in hands]:
        if len(obj.data.vertices)<minimum or not obj.data.uv_layers:
            raise ValueError('Standard postaci: utracono anatomie lub UV podczas budowy.')
    for obj in heads:
        images=[n.image for m in obj.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
        if not any(min(im.size)>=2048 for im in images):raise ValueError('Standard postaci: skora wymaga atlasu 2048 px.')
    detailed=sum(bool(o.get('lash_geometry_required')) for o in heads)
    lashes=[o for o in objects if 'upper_lashes_per_eye' in o]
    if len(lashes)!=detailed or any(len(o['upper_lashes_per_eye'])!=2 or min(o['upper_lashes_per_eye'])<16 for o in lashes):
        raise ValueError('Standard portretu: brakuje rzes dopasowanych do obu powiek.')
    return {'revision':2,'heads':len(heads),'eyes':len(eyes),'hands':len(hands),'nails':len(nails),'structural_checks_passed':True,'likeness_verified':False}
