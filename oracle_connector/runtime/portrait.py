"""Anatomical portrait component with bounded shape controls and portable detail.

The photo planner chooses proportions; this renderer never claims an identity
match. Skin is a generic CC0 atlas, not another person's portrait texture.
"""
import math
import bpy
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
import anatomy
import portrait_shape


def head(p, skin, eyes, hair, mesh_object, ellipsoid):
    style=p.get('hair_style','short'); long=style in ('long_wavy','straight_bob','curly')
    parts=anatomy.head({**p,'hair_style':'bald' if long else 'short' if style=='ponytail' else style},skin,eyes,hair,mesh_object,ellipsoid)
    from portrait_eyes import apply_eye_albedo
    apply_eye_albedo(parts,eyes.diffuse_color[:3])
    obj=parts[0];portrait_shape.sculpt(obj,p.get('face',{}))
    obj['anatomical_head']=True;obj['quality_revision']=1
    # One front-facing iris per globe, including from the side and rear.
    for eye in parts:
        if not eye.name.startswith('anatomical-eye-'):continue
        eye['anatomical_eye']=True;eye['iris_count']=1
    for brow in parts:
        if brow.name.startswith('eyebrow'):
            brow.data.materials.clear();brow.data.materials.append(hair)
    # Trace the visible anatomical upper lid for fine eyelashes in all genders.
    surface=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[f.vertices[:] for f in obj.data.polygons])
    cosmetic=bpy.data.materials.get('anatomical-lashes')
    if cosmetic is None:
        cosmetic=bpy.data.materials.new('anatomical-lashes');cosmetic.use_nodes=True
        bsdf=cosmetic.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=(.005,.003,.002,1);bsdf.inputs['Roughness'].default_value=.7
    vv=[];ff=[];liner_vertices=[];liner_faces=[];glam=p.get('makeup')=='soft_glam'
    for side in ('l','r'):
        previous=None
        center=anatomy.landmark(side+'-eye',p['presentation']);sign=1 if center.x>0 else -1
        for i in range(44):
            t=.08+.84*i/43;x=center.x+(.5-t)*.028*sign
            candidates=[]
            for j in range(90):
                z=center.z-.011+.022*j/89;r=((x-center.x)/.0147)**2+((z-center.z)/.0143)**2
                hit,_,_,_=surface.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)))
                if r<1 and hit is not None and hit.y>center.y-.0152*math.sqrt(1-r)+.00002:candidates.append(z)
            if not candidates:continue
            z=max(candidates);r=((x-center.x)/.0147)**2+((z-center.z)/.0143)**2
            y=center.y-.0152*math.sqrt(max(0,1-r))-.00025
            root=Vector((x,y,z));length=(.002+.004*(1-t))*(1.25 if glam else .8)
            start=len(liner_vertices)
            for dz in (0,.0007+(.0011 if glam else 0)*(1-t)):
                hit,_,_,_=surface.ray_cast(Vector((x,-.4,z+dz)),Vector((0,1,0)))
                liner_vertices.append((x,min(y,hit.y-.0005 if hit is not None else y),z+dz))
            if previous is not None:liner_faces.append((previous,start,start+1,previous+1))
            previous=start
            base=len(vv)
            for k in range(9):
                u=k/8;q=root+Vector((sign*length*.4*u*u,-length*.7*u,length*(.25*u+.6*u*u)))
                hit,_,_,_=surface.ray_cast(Vector((q.x,-.4,q.z)),Vector((0,1,0)))
                if hit is not None:q.y=min(q.y,hit.y-.00055)
                radius=.00018*(1-u)+.000012
                for v in (-1,1):vv.append(tuple(q+Vector((radius*v,0,0))))
                if k:ff.append((base+2*k-2,base+2*k,base+2*k+1,base+2*k-1))
    lashes=mesh_object('anatomical-lash-fibres',vv,ff,cosmetic);parts.append(lashes)
    parts.append(mesh_object('anatomical-upper-eyeliner',liner_vertices,liner_faces,cosmetic))
    if glam:
        # Portable vertex tint multiplies the subject-independent anatomical
        # albedo. No extra portrait plane, duplicate lips or external shader.
        attr=obj.data.color_attributes.new(name='CosmeticTint',type='FLOAT_COLOR',domain='POINT')
        for vertex in obj.data.vertices:
            x,y,z=vertex.co;front=max(0,min(1,(-.085-y)/.035));ax=abs(x)
            shadow=math.exp(-((ax-.034)/.018)**4-((z-1.689)/.008)**2)*.30*front
            blush=math.exp(-((ax-.05)/.02)**2-((z-1.650)/.012)**2)*.12*front
            lip=math.exp(-(x/.025)**6-((z-1.614)/.007)**4)*.24*front
            if 'makeup_rgb' in p:
                tint=p['makeup_rgb'];shadow=min(1.,shadow*1.8)
                attr.data[vertex.index].color=(1-shadow*(1-tint[0]),1-shadow*(1-tint[1])-blush-lip,1-shadow*(1-tint[2])-blush*.75-lip*.55,1)
            else:
                attr.data[vertex.index].color=(1-shadow*.38,1-shadow*.62-blush-lip,1-shadow*.67-blush*.75-lip*.55,1)
        nodes=skin.node_tree.nodes;links=skin.node_tree.links;bsdf=nodes['Principled BSDF']
        source=bsdf.inputs['Base Color'].links[0].from_socket
        col=nodes.new('ShaderNodeVertexColor');col.layer_name=attr.name
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        links.new(source,mix.inputs[1]);links.new(col.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        # glTF exports COLOR_0 automatically and multiplies baseColorTexture.
        # Keep the supported image link; the tint is an exported vertex color.
        links.new(source,bsdf.inputs['Base Color'])
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
    return parts


def build_portrait(p, materials, mesh_object, ellipsoid):
    parts=head(p,materials[p['skin_material']],materials[p['eye_material']],materials[p['hair_material']],mesh_object,ellipsoid)
    # Primitive scale/location setters do not synchronously refresh matrix_world.
    # Reading a stale matrix here can turn an eyeglass lens into a metre sphere.
    bpy.context.view_layer.update()
    eye_center=(anatomy.landmark('l-eye',p['presentation'])+anatomy.landmark('r-eye',p['presentation']))*.5
    transform=Matrix.Translation(p['center'])@Euler(p['rotation']).to_matrix().to_4x4()@Matrix.Scale(p['scale'],4)@Matrix.Translation(-eye_center)
    for obj in parts:obj.matrix_world=transform@obj.matrix_world
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
    return {'revision':1,'heads':len(heads),'eyes':len(eyes),'hands':len(hands),'nails':len(nails),'structural_checks_passed':True,'likeness_verified':False}
