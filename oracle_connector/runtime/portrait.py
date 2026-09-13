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
    eye_states=p.get('eye_states',{'left':'present','right':'present'})
    present={side:eye_states.get(label,'present')=='present'
             for side,label in (('l','left'),('r','right'))}
    photo_fit=p.get('_photo_fit')
    if photo_fit is not None:
        # Calibration uses a neutral, dense feminine head. The photographed
        # residual replaces the seven authored proportions, rather than adding
        # a second deformation on top of an unrelated AI-selected face.
        p={**p,'face':{},'makeup':'soft_glam'}
    style=p.get('hair_style','short'); long=style in ('long_wavy','straight_bob','curly')
    parts=anatomy.head({**p,'hair_style':'bald' if long else 'short' if style=='ponytail' else style},skin,eyes,hair,mesh_object,ellipsoid)
    # Intent comes from the validated plan, never from a failed edit or a name
    # guessed by the agent. Keep the living eye; omit only the declared socket.
    for eye in list(parts):
        if eye.name.startswith('anatomical-eye-'):
            side=eye.name[len('anatomical-eye-')]
            if not present[side]:
                parts.remove(eye);bpy.data.objects.remove(eye,do_unlink=True)
            else:
                eye['anatomy_owner']=p['name'];eye['anatomy_eye_side']=side
    from portrait_eyes import apply_eye_albedo
    gaze=portrait_shape.measured_gaze(photo_fit.observation,photo_fit.template['observation']) if photo_fit is not None else (0.,0.)
    apply_eye_albedo(parts,eyes.diffuse_color[:3],gaze)
    obj=parts[0]
    obj['anatomy_owner']=p['name']
    for side in ('l','r'):
        obj['orbit_anchor_'+side]=list(anatomy.landmark(side+'-eye',p['presentation']))
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
    # Measured residuals are calibrated against the neutral soft-glam template.
    # An extra couture squint changed that starting surface and closed the eyes
    # a second time. Keep its exact lid basis before applying measured residuals.
    lid_strength=.36 if glam else .20
    upper_lid_bias=.08 if glam else 0
    for side in ('l','r'):
        center=anatomy.landmark(side+'-eye',p['presentation'])
        for vertex in obj.data.vertices:
            vertex.co=relaxed_lid_point(vertex.co,center,lid_strength,upper_lid_bias)
    obj.data.update()
    obj['reference_lid_aperture_authored']=False
    obj['lid_template_basis']='neutral-soft-glam' if photo_fit is not None else 'authored-style'
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
        if not present['l' if side==1 else 'r']:continue
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
        if not present[side]:
            lash_counts.append(0)
            continue
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
    if any(present.values()):
        lashes=mesh_object('anatomical-lash-fibres',vv,ff,cosmetic);parts.append(lashes)
        for polygon in lashes.data.polygons:polygon.use_smooth=True
        lashes['upper_lashes_per_eye']=lash_counts
        lashes['anatomy_owner']=p['name']
        parts.append(mesh_object('anatomical-upper-eyeliner',liner_vertices,liner_faces,cosmetic))
    obj['lash_geometry_required']=any(present.values())
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


def portrait_transforms(p):
    """One rotation shared by the skull, eyes, hair and couture jewellery."""
    eye_center=(anatomy.landmark('l-eye',p['presentation'])+anatomy.landmark('r-eye',p['presentation']))*.5
    neutral=Matrix.Translation(p['center'])@Matrix.Scale(p['scale'],4)@Matrix.Translation(-eye_center)
    pivot=neutral@Vector((0,-.015,1.565)) if 'makeup_rgb' in p else Vector(p['center'])
    turn=Matrix.Translation(pivot)@Euler(p['rotation']).to_matrix().to_4x4()@Matrix.Translation(-pivot)
    return neutral,turn,turn@neutral


def build_portrait(p, materials, mesh_object, ellipsoid):
    parts=head(p,materials[p['skin_material']],materials[p['eye_material']],materials[p['hair_material']],mesh_object,ellipsoid)
    # Primitive scale/location setters do not synchronously refresh matrix_world.
    # Reading a stale matrix here can turn an eyeglass lens into a metre sphere.
    bpy.context.view_layer.update()
    neutral,_,transform=portrait_transforms(p)
    for obj in parts:
        if obj.get('anatomical_head') and 'makeup_rgb' in p:
            # Turn the skull while anchoring the lower neck in its garment.
            # Rotating the entire cut neck about the eyes exposed its jagged
            # lower boundary outside the standing collar at stronger rolls.
            inverse=transform.inverted();anchored=0
            for vertex in obj.data.vertices:
                v=vertex.co.copy()
                weight=max(0.,min(1.,(v.z-1.485)/.090));weight=weight*weight*(3-2*weight)
                front=max(0.,min(1.,(-.065-v.y)/.045));front=front*front*(3-2*front)
                chin=max(0.,min(1.,(v.z-1.530)/.040));chin=chin*chin*(3-2*chin)
                weight+=(1-weight)*front*chin
                if weight<1:
                    vertex.co=inverse@((neutral@v).lerp(transform@v,weight));anchored+=1
            obj['neck_pose_anchored_vertices']=anchored
            obj['neck_pose_lower_anchor']=1.485
            obj['neck_pose_revision']=2
            obj['head_pivot_local']=[0,-.015,1.565]
            obj.data.update()
        obj.matrix_world=transform@obj.matrix_world
    return parts


COMPONENT_TAGS = {
    'heads': 'anatomical_head', 'eyes': 'anatomical_eye',
    'hands': 'anatomical_hand', 'nails': 'anatomical_nail',
}


def socket_clearance_checks(objects, intent):
    """A bounded occupancy check, NOT proof of skull shape or likeness.

    Check real evaluated geometry, including untagged black filler spheres.
    Rays use the head's local anatomical frame, so world pose/scale are retained.
    The base intentionally remains a draft until its eyelids are sculpted away.
    """
    checks=[]
    if not intent:return {'required':False,'passed':True,'checks':checks}
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for owner,states in intent.items():
        for side,label in (('l','left'),('r','right')):
            if states[label]!='empty_socket':continue
            heads=[obj for obj in objects if obj.get('anatomical_head') and obj.get('anatomy_owner')==owner]
            item={'owner':owner,'side':label,'passed':False,'clear_rays':0,'required_rays':5}
            checks.append(item)
            if len(heads)!=1 or 'orbit_anchor_'+side not in heads[0]:continue
            head=heads[0];anchor=Vector(head['orbit_anchor_'+side]);transform=head.matrix_world
            # A shallow slit, a black globe and a front disk all fail. The
            # five samples must reach behind the former eye centre.
            for dx,dz in ((0,0),(-.009,0),(.009,0),(0,-.008),(0,.008)):
                start=transform@(anchor+Vector((dx,-.05,dz)))
                end=transform@(anchor+Vector((dx,.006,dz)))
                vector=end-start;length=vector.length
                hit,*_=bpy.context.scene.ray_cast(depsgraph,start,vector.normalized(),distance=length)
                if not hit:item['clear_rays']+=1
            item['passed']=item['clear_rays']==item['required_rays']
    return {'required':bool(checks),'passed':all(item['passed'] for item in checks),
            'checks':checks,'scope':'Orbital foreground occupancy only; skull shape and likeness require visual review.'}


class AnatomyValidationError(ValueError):
    """A failed structural gate with diagnostics the agent can act on."""
    def __init__(self, report):
        self.report = report
        names = {'heads': 'twarze', 'eyes': 'oczy', 'hands': 'dlonie', 'nails': 'paznokcie'}
        counts = ', '.join('%s %d/%d' % (names[key], report['actual'][key],
                                       report['expected'][key]) for key in COMPONENT_TAGS)
        details = '; '.join(issue['message'] for issue in report['violations'])
        super().__init__('Standard postaci: %s. %s Wynik nie zostal zaakceptowany.' % (counts, details))


def component_snapshot(objects):
    """Remember identities before an edit without retaining removed bpy objects."""
    return {key: [{'name': obj.name, 'pointer': obj.as_pointer()}
                  for obj in objects if obj.get(tag)]
            for key, tag in COMPONENT_TAGS.items()}


def skin_atlas_evidence(obj):
    """Inspect images of effective assigned materials, including node groups.

    Object-linked material slots can override mesh.data.materials; reporting the
    latter alone can reject a valid head or inspect a material that is not used.
    Group nesting is bounded and cycle-safe. This establishes image attachment
    and resolution only, not likeness or whether a specific shader uses colour.
    """
    slots = getattr(obj, 'material_slots', None)
    materials = ([slot.material for slot in slots] if slots is not None
                 else list(obj.data.materials))
    images = []
    seen_trees = set()
    for material in materials:
        if not material or not material.use_nodes or not material.node_tree:
            continue
        pending = [material.node_tree]
        while pending and len(seen_trees) < 128:
            tree = pending.pop()
            pointer = tree.as_pointer()
            if pointer in seen_trees:
                continue
            seen_trees.add(pointer)
            for node in tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    images.append(node.image)
                elif node.type == 'GROUP' and node.node_tree:
                    pending.append(node.node_tree)
    edges = [min(image.size) for image in images]
    return {
        'minimum_edge': 2048,
        'largest_image_edge': int(max(edges, default=0)),
        'observed_materials': ', '.join(material.name for material in materials if material)[:600],
        'observed_images': ', '.join('%s (%dx%d)' % (image.name, *image.size) for image in images)[:1000],
        'atlas_scope': 'effective_head_materials_including_groups',
    }


def verify_components(objects, expected_heads, expected_hands, before=None, intent=None):
    groups = {key: [obj for obj in objects if obj.get(tag)]
              for key, tag in COMPONENT_TAGS.items()}
    expected = {'heads': int(expected_heads), 'eyes': 2 * int(expected_heads),
                'hands': int(expected_hands), 'nails': 5 * int(expected_hands)}
    if intent is not None:
        if len(intent)!=int(expected_heads):
            raise ValueError('Niespojny kontrakt anatomii z planem sceny.')
        expected['eyes']=sum(states[side]=='present' for states in intent.values()
                             for side in ('left','right'))
    actual = {key: len(items) for key, items in groups.items()}
    violations = []
    report = {
        'revision': 2, 'diagnostic_revision': 1, 'expected': expected, 'actual': actual,
        'missing': {key: max(0, expected[key] - actual[key]) for key in COMPONENT_TAGS},
        'excess': {key: max(0, actual[key] - expected[key]) for key in COMPONENT_TAGS},
        'objects': {key: [obj.name for obj in items] for key, items in groups.items()},
        'violations': violations, 'structural_checks_passed': False,
        'likeness_verified': False,
    }
    if intent is not None:
        report['reference_anatomy']=intent
        for owner,states in intent.items():
            owned_heads=[obj for obj in groups['heads'] if obj.get('anatomy_owner')==owner]
            if len(owned_heads)!=1:
                violations.append({'code':'head_identity','object':owner,
                                   'message':'Brak jednoznacznej glowy: '+owner})
            for side,label in (('l','left'),('r','right')):
                wanted=int(states[label]=='present')
                found=sum(obj.get('anatomy_owner')==owner and obj.get('anatomy_eye_side')==side
                          for obj in groups['eyes'])
                if found!=wanted:
                    violations.append({'code':'eye_identity','object':owner+':'+label,
                                       'expected':wanted,'actual':found,
                                       'message':'Oko '+owner+':'+label+' nie zgadza sie z deklaracja referencji.'})
    if before:
        present = {key: {obj.as_pointer() for obj in items} for key, items in groups.items()}
        report['removed_or_untagged'] = {
            key: [item['name'] for item in before.get(key, [])
                  if item['pointer'] not in present[key]] for key in COMPONENT_TAGS
        }
    for key in COMPONENT_TAGS:
        if actual[key] != expected[key]:
            violations.append({'code': 'component_count', 'component': key,
                               'expected': expected[key], 'actual': actual[key],
                               'message': '%s: wymagane %d, znalezione %d.' %
                                          (key, expected[key], actual[key])})
    for key, minimum in (('heads', 12000), ('hands', 4500)):
        for obj in groups[key]:
            count = len(obj.data.vertices)
            if count < minimum or not obj.data.uv_layers:
                violations.append({'code': 'anatomy_topology_or_uv', 'object': obj.name,
                                   'vertices': count, 'minimum_vertices': minimum,
                                   'has_uv': bool(obj.data.uv_layers),
                                   'message': '%s: wierzcholki %d/%d, UV %s.' %
                                              (obj.name, count, minimum,
                                               'zachowane' if obj.data.uv_layers else 'brak')})
    for obj in groups['heads']:
        atlas = skin_atlas_evidence(obj)
        if atlas['largest_image_edge'] < atlas['minimum_edge']:
            violations.append({'code': 'skin_atlas', 'object': obj.name, **atlas,
                               'message': '%s: przypisany atlas skory ma maksymalna krotsza krawedz %d px; wymagane 2048 px. '
                                          'Zachowaj material i UV glowy; make_material(pattern="skin") tworzy ogolna mape 512 px.' %
                                          (obj.name, atlas['largest_image_edge'])})
    detailed = (sum(any(states[side]=='present' for side in ('left','right')) for states in intent.values())
                if intent is not None else sum(bool(obj.get('lash_geometry_required')) for obj in groups['heads']))
    lashes = [obj for obj in objects if 'upper_lashes_per_eye' in obj]
    if len(lashes) != detailed:
        violations.append({'code': 'lash_components', 'expected': detailed, 'actual': len(lashes),
                           'message': 'Rzesy: wymagane %d par, znalezione %d.' % (detailed, len(lashes))})
    for obj in lashes:
        counts = list(obj['upper_lashes_per_eye'])
        states=intent.get(obj.get('anatomy_owner'),{}) if intent is not None else {}
        minimum=[16 if states.get(side,'present')=='present' else 0 for side in ('left','right')]
        if (len(counts) != 2 or (intent is not None and not states) or
                any((count<limit if limit else count!=0) for count,limit in zip(counts,minimum))):
            violations.append({'code': 'lash_count', 'object': obj.name, 'actual': counts,
                               'minimum_per_eye': 16,
                               'message': '%s: rzesy %s; wymagane %s zgodnie z referencja.' %
                                          (obj.name, counts, minimum)})
    if intent is not None:
        for owner,states in intent.items():
            wanted=int(any(states[side]=='present' for side in ('left','right')))
            if sum(obj.get('anatomy_owner')==owner for obj in lashes)!=wanted:
                violations.append({'code':'lash_identity','object':owner,
                                   'message':'Rzesy nie sa przypisane do wlasciwej glowy: '+owner})
    if violations:
        report['repair_hint'] = (
            ('Blad skin_atlas dotyczy materialow przypisanych do glowy, nie liczby obiektow. '
             'Zachowaj istniejacy atlas i UV; do osobnej stylizacji skopiuj material glowy metoda copy(). '
             'Nie zastepuj go make_material(pattern="skin") 512 px ani nie skaluj szumu do 2048. '
             if any(v['code'] == 'skin_atlas' for v in violations) else '') +
            'Zachowaj osobne anatomiczne obiekty, ich znaczniki i UV. '
            'Celowy pusty oczodol deklaruj przed budowa w portrait.eye_states; '
            'nie zmieniaj licznikow po bledzie. Zachowaj zywe oko, '
            'dloni ani paznokci podczas stylizacji. Laczenie akcesoriow wykonuj '
            'osobno od anatomii. Napraw wymienione braki przed kolejna ocena renderow.')
        raise AnatomyValidationError(report)
    return {'revision': 2, 'diagnostic_revision': 2, **actual, 'expected': expected,
            'reference_anatomy':intent or {},
            'socket_shape_verified':False,
            'structural_checks_passed': True, 'likeness_verified': False}
