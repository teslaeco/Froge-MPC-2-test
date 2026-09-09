"""Dedicated fitted couture. Never wraps a sweatshirt/trouser character.

The portrait remains a parameterised CC0 face, not a recovered identity.
Hidden garment/body areas are explicitly marked as reconstructed.
"""
import math
import bpy
from mathutils import Vector, Matrix, Euler
from detailed_geometry import loft
from portrait import build_portrait
from portrait_hands import build_hand
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
    parts=[];width={'slim':.94,'average':1.}[p['build']]
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
    shaped('body-under-gown',stations,body)
    shaped('neck',[(0,.006,1.39,.057,.053),(0,.005,1.54,.050,.050)],body,48)
    vv,ff=geometry.gown(p['hem_radius'],width,offset,thickness)
    gown=add(mesh_object(p['name']+'-fitted-gown',vv,ff,dress),'fitted-gown')
    for face in gown.data.polygons:face.use_smooth=True
    gown['garment_offset_m']=offset;gown['garment_thickness_m']=thickness
    # Conformal triangular gemstone inlays follow every profile change. A
    # diamond consists of four triangles raised only 1.5 mm off the garment.
    vv=[];ff=[];slots=[]
    for row in range(9):
        lo=.28+row*.12;hi=lo+.115
        for col in range(12):
            a=math.tau*(col+(row%2)*.5)/12;b=a+math.tau/12*.94
            start=len(vv)
            vv.extend(geometry.gown_point(z,angle,p['hem_radius'],width,offset+.0015)
                      for z,angle in ((lo,a),(lo,b),(hi,b),(hi,a),((lo+hi)/2,(a+b)/2)))
            ff.extend((start+i,start+(i+1)%4,start+4) for i in range(4));slots.extend([col%3]*4)
    inlay=add(mesh_object(p['name']+'-conformal-facets',vv,ff,crystal),'conformal-facets')
    inlay.data.materials.append(dress);inlay.data.materials.append(metal)
    for face,index in zip(inlay.data.polygons,slots):face.material_index=index
    # Raised collar with actual front opening and thin solid walls.
    vv=[]
    for z,rx,ry in ((1.445,.066,.060),(1.535,.061,.057)):
        for i in range(41):
            a=-math.pi/2+.18+(math.tau-.36)*i/40
            vv.append((rx*math.cos(a),.006+ry*math.sin(a),z))
    # Collar shell normal uses Blender Solidify, unlike shallow front panels.
    collar=add(mesh_object(p['name']+'-standing-collar',vv,[(i,i+1,42+i,41+i) for i in range(40)],dress),'standing-collar')
    modifier=collar.modifiers.new('Real 2 mm collar','SOLIDIFY');modifier.thickness=thickness
    bpy.context.view_layer.objects.active=collar;bpy.ops.object.modifier_apply(modifier=modifier.name)
    if p['cape']:
        vv=[];ff=[];rows=52;cols=64
        for j in range(rows):
            t=j/(rows-1);z=1.425-1.375*t
            for k in range(cols):
                u=2*k/(cols-1)-1
                x=u*(.19+.19*t)
                y=.050+.22*t+.040*(1-u*u)+.013*math.sin(10*math.pi*u)*(t+.1)
                vv.append((x,y,z+.017*math.sin(math.pi*u)**2*t))
                if j and k:ff.append(((j-1)*cols+k-1,(j-1)*cols+k,j*cols+k,j*cols+k-1))
        cape=add(mesh_object(p['name']+'-shoulder-drape',vv,ff,dress),'shoulder-drape')
        for face in cape.data.polygons:face.use_smooth=True
        solid=cape.modifiers.new('Thin cloth drape','SOLIDIFY');solid.thickness=thickness
        bpy.context.view_layer.objects.active=cape;bpy.ops.object.modifier_apply(modifier=solid.name)
    for z in (1.075,1.092,1.109,1.126):
        points=[geometry.gown_point(z,math.tau*i/96,p['hem_radius'],width,offset+.003) for i in range(97)]
        line('waist-metal-ribbon',points,[.0018]*97,metal,8)
    clasp=add(ellipsoid(p['name']+'-waist-gem',(0,-.092,1.103),(.024,.009,.030),crystal,2),'waist-gem')
    for side in (-1,1):
        # Full separate legs, ankles and shoes continue behind the opaque gown.
        shaped('leg',[(side*.097,0,.94,.073,.079),(side*.099,-.006,.53,.049,.053),
                      (side*.102,.009,.35,.050,.049),(side*.105,-.008,.10,.027,.031)],body,48)
        add(ellipsoid(p['name']+'-shoe',(side*.105,-.061,.048),(.035,.103,.031),shoe,3),'reconstructed-shoe')
        shaped('shoe-heel',[(side*.105,.008,.006,.013,.014),(side*.105,.008,.052,.014,.014)],shoe,24)
        shoulder=Vector((side*.169*width,0,1.390))
        elbow=Vector((side*.236,-.038,1.17))
        holding=(side==-1 and p['fan']['enabled'])
        wrist=Vector((-.150,-.193,1.118) if holding else (side*.240,-.018,.984))
        # One interpolated sleeve joins shoulder, elbow and wrist.
        shaped('fitted-sleeve',[(*shoulder,.051,.054),(*shoulder.lerp(elbow,.52),.043,.044),
              (*elbow,.033,.034),(*elbow.lerp(wrist,.48),.035,.032),(*wrist,.027,.024)],dress)
        direction=Vector((.10,-.20,.975)) if holding else (wrist-elbow).normalized()
        parts+=build_hand({'side':'right' if side==-1 else 'left','wrist':list(wrist),
            'direction':list(direction),'palm_normal':[0,-1,.1],'presentation':'feminine',
            'scale':.93,'curl':.92 if holding else .18,'nail_length':.0025},skin,nails,mesh_object)
        # Angular shoulder decorations stay anchored to the actual shoulder.
        front=[(side*.10,-.050,1.432),(side*.285,-.033,1.478),
               (side*.215,-.073,1.364),(side*.155,-.082,1.407)]
        vv,ff=geometry.shell(front,[(0,1,3),(1,2,3)],thickness)
        add(mesh_object(p['name']+'-shoulder-inlay',vv,ff,crystal),'shoulder-inlay')
    eye_mid=(anatomy.landmark('l-eye','feminine')+anatomy.landmark('r-eye','feminine'))*.5
    portrait_plan={**p,'presentation':'feminine','hair_style':'short' if p['updo'] else 'shoulder_length',
        'headwear':'none','eyewear':'none','center':[0,eye_mid.y,1.64],
        'rotation':p['head_rotation'],'scale':1.,'makeup_rgb':tuple(crystal.diffuse_color[:3])}
    head_parts=build_portrait(portrait_plan,materials,mesh_object,ellipsoid);parts+=head_parts
    head_accessory_start=len(parts)
    # Detailed swept updo strands, independent from the smooth face mesh.
    if p['updo']:
        strands=[]
        for i in range(100):
            phase=math.tau*i/100;points=[]
            for j in range(33):
                t=j/32
                points.append((.078*math.cos(phase)*(1-.42*t)+.020*math.sin(t*math.pi),
                    .020+.078*math.sin(phase)*(1-.60*t)+.048*t,
                    1.733+.14*math.sin(t*math.pi*.78)+.007*math.cos(phase)))
            strands.append(tube('updo-strand',points,[.0034*(1-j/33)+.0004 for j in range(33)],hair,6))
        add(join_meshes(strands,p['name']+'-swept-updo'),'swept-updo')
    # Gemstone earrings and hair ornament are fully three-dimensional.
    for side in (-1,1):
        line('earring-chain',[(side*.076,-.018,1.61),(side*.084,-.022,1.584)],[.0012,.0012],metal,8)
        gem=add(ellipsoid(p['name']+'-earring',(side*.084,-.022,1.561),(.013,.006,.029),crystal,1),'earring')
        for f in gem.data.polygons:f.use_smooth=False
    if p['hair_ornament']:
        for i in range(3):
            obj=add(ellipsoid(p['name']+'-hair-jewel',(.056+i*.009,-.010,1.783+i*.016),(.020,.010,.039),crystal,1),'hair-ornament')
            for f in obj.data.polygons:f.use_smooth=False
    bpy.context.view_layer.update()
    pivot=Vector(portrait_plan['center'])
    head_turn=Matrix.Translation(pivot)@Euler(p['head_rotation']).to_matrix().to_4x4()@Matrix.Translation(-pivot)
    for obj in parts[head_accessory_start:]:obj.matrix_world=head_turn@obj.matrix_world
    if p['fan']['enabled']:
        f=p['fan'];pivot=Vector((-.145,-.235,1.178))
        vv,ff,slots=geometry.fan(f['radius'],f['panels'],f['spread'],thickness)
        fan=add(mesh_object(p['name']+'-pleated-fan',vv,ff,dress),'pleated-fan')
        fan.location=pivot;fan.data.materials.append(crystal);fan.data.materials.append(metal)
        for face,index in zip(fan.data.polygons,slots):face.material_index=index
        fan['panel_count']=f['panels'];fan['rotor_count']=f['rotors']
        for i in range(f['panels']+1):
            a=-f['spread']/2+f['spread']*i/f['panels']
            tip=pivot+Vector((f['radius']*math.sin(a),-.002,f['radius']*math.cos(a)))
            line('fan-rib',[tuple(pivot),tuple(tip)],[.0018,.001],metal,8)
        centers=geometry.radial_positions(f['rotors'],f['radius']*.90,-f['spread']/2+.06,
                                          f['spread']-.12,tuple(pivot+Vector((0,-.012,0))))
        template=rotor({'name':p['name']+'-fan-rotor','center':centers[0],
            'radius':min(.028,f['radius']*f['spread']/f['rotors']*.34),'depth':.008,'blades':5},metal,crystal,mesh_object)
        add(template,'fan-rotor')
        for i,center in enumerate(centers[1:],1):
            obj=template.copy();obj.name=p['name']+'-fan-rotor-%02d'%i;obj.location=center
            bpy.context.collection.objects.link(obj);add(obj,'fan-rotor')
    # Uniform scale applies to geometry and accessories together.
    bpy.context.view_layer.update()
    factor=p['height']/1.88
    transform=Matrix.Translation(p['center'])@Matrix.Scale(factor,4)
    for obj in parts:
        obj.matrix_world=transform@obj.matrix_world
        obj['character']=p['name'];obj['characterStandard']=19
        obj['reference_likeness_verified']=False
        obj['observedFeatures']='; '.join(p['observed_features'])
        obj['reconstructedFeatures']='; '.join(p['reconstructed_features'])
    return parts
