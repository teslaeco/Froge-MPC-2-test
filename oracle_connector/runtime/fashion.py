"""Reusable dressed adult figures, with real portrait/hand components.

This is a bounded garment and pose builder, not a face-identity reconstruction.
The data planner supplies each subject's palette and seven facial proportions.
"""
import math
import bpy
from mathutils import Vector, Matrix
from detailed_geometry import loft
from portrait import build_portrait
from portrait_hands import build_hand
import anatomy


def fashion_person(p, materials, mesh_object, tube, ellipsoid):
    skin,hair,top,bottom,shoe,accent,eyes=[materials[p[k+'_material']] for k in ('skin','hair','top','trouser','shoe','accent','eye')]
    # Bare limbs use a portable, softly textured body material. The head and
    # hands retain their 2048px anatomical UV atlas without projected face UVs.
    body=bpy.data.materials.get(skin.name+'-body')
    if body is None:
        body=bpy.data.materials.new(skin.name+'-body');body.use_nodes=True
        # The atlas stores sRGB texels, while constant shader inputs are linear.
        linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in skin.diffuse_color[:3]]
        s=body.node_tree.nodes['Principled BSDF'];s.inputs['Base Color'].default_value=(*linear,1);s.inputs['Roughness'].default_value=.59
        body.diffuse_color=skin.diffuse_color
    parts=[];sitting=p['pose']=='sitting';outfit=p['outfit']
    pelvis=.57 if sitting else .94;torso=pelvis+.24;eye_z=pelvis+.64
    width={'slim':.90,'average':1.,'broad':1.12}[p['build']]
    def shape(name, stations, mat, folds=0., sides=48):
        obj=loft(p['name']+'-'+name,[{'center':s[:3],'radii':s[3:]} for s in stations],sides,mat,mesh_object,folds)
        parts.append(obj);return obj
    def line(name,points,radii,mat,sides=12):
        obj=tube(p['name']+'-'+name,points,radii,mat,sides);parts.append(obj);return obj
    def ball(name,center,radii,mat):
        obj=ellipsoid(p['name']+'-'+name,center,radii,mat,subdivisions=3);parts.append(obj);return obj
    # Connected torso outline, never two separate breast spheres.
    torso_stations=[(0,0,pelvis,.15*width,.10),(0,0,pelvis+.13,.117*width,.078),
        (0,-.007,pelvis+.23,.136*width,.087),(0,-.009,pelvis+.33,.167*width,.104),
        (0,0,pelvis+.40,.164*width,.079),(0,0,pelvis+.45,.115*width,.066)]
    shape('body',torso_stations,body)
    shape('neck',[(0,.004,pelvis+.40,.065,.058),(0,.004,pelvis+.59,.062,.056)],body,sides=32)
    if outfit=='crop_skirt':
        shape('high-neck-top',[(x,y,z,rx+.012,ry+.012) for x,y,z,rx,ry in torso_stations],top,.002)
        shape('top-collar',[(0,.004,pelvis+.44,.056,.052),(0,.004,pelvis+.52,.050,.051)],top,sides=32)
        # Ring pleats, continuous waist and opaque hem.
        vv=[];ff=[];rings=15;n=96
        for j in range(rings):
            t=j/(rings-1);r=.149*width+.072*t;depth=.11+.095*t
            for k in range(n):
                a=k*math.tau/n;pleat=1+.055*math.sin(a*16)*t
                vv.append((r*math.cos(a)*pleat,(-.14*t if sitting else 0)+depth*math.sin(a)*pleat,pelvis+.065-(.11 if sitting else .245)*t))
                if j:ff.append(((j-1)*n+k,(j-1)*n+(k+1)%n,j*n+(k+1)%n,j*n+k))
        obj=mesh_object(p['name']+'-pleated-skirt',vv,ff,bottom);parts.append(obj)
        solid=obj.modifiers.new('Finished skirt thickness','SOLIDIFY');solid.thickness=.002
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=solid.name)
    else:
        shape('crop-top',[(x,y,z,rx+.012,ry+.012) for x,y,z,rx,ry in torso_stations[2:5]],bottom,.002)
        shape('waistband',[(0,0,pelvis+.03,.159*width,.108),(0,0,pelvis+.09,.147*width,.101)],bottom,sides=48)
        shape('connected-hip-garment',[(0,0,pelvis-.06,.166*width,.111),(0,0,pelvis+.045,.165*width,.112)],bottom,.003)
        # Two visibly open front panels with back and shoulder seams.
        for side in (-1,1):
            shape('open-vest',[(side*.145,0,pelvis+.10,.045,.12),(side*.150,.002,pelvis+.29,.052,.123),(side*.14,.02,pelvis+.45,.054,.083)],top,.014 if outfit=='puffer_crop' else .009)
            for j in range(5):
                z=pelvis+.13+j*.063
                line('stitched-panel',[(side*.107,-.112,z),(side*.146,-.124,z-.007),(side*.187,-.108,z)],[.001]*3,top,8)
        shape('jacket-back',[(0,.085,pelvis+.12,.17,.035),(0,.087,pelvis+.43,.176,.03)],top,.005)
    for side in (-1,1):
        hip=Vector((side*.105*width,0,pelvis-.01))
        knee=Vector((side*(.22 if sitting else .105),-.36 if sitting else -.018,.44 if sitting else .49))
        ankle=Vector((side*(.235 if sitting else .12),-.43 if sitting else -.015,.095))
        legmat=bottom if outfit=='puffer_crop' else body
        shape('thigh',[(hip.x,hip.y,hip.z,.10,.095),(*hip.lerp(knee,.45),.088,.08),(*knee,.062,.063)],legmat,sides=48)
        ball('knee',knee,(.061,.061,.063),legmat)
        shape('upper-shin',[(knee.x,knee.y,knee.z,.056,.059),(*knee.lerp(ankle,.24),.059,.059)],legmat,sides=48)
        # Opaque shorts cover hips before the uncovered thigh begins.
        if outfit=='black_crop':
            shape('shorts',[(hip.x,hip.y,pelvis+.02,.111,.112),(*hip.lerp(knee,.35),.093,.089)],bottom,.003)
        boot_top=knee.lerp(ankle,.20)
        shape('boot-shaft',[(*boot_top,.064,.069),(*knee.lerp(ankle,.63),.058,.058),(*ankle,.041,.047)],shoe,.003)
        foot=Vector((ankle.x,ankle.y-.064,.058))
        ball('rounded-boot',foot,(.046,.112,.048),shoe)
        shape('sole',[(foot.x,foot.y,.019,.049,.113),(foot.x,foot.y,.032,.049,.113)],shoe,sides=48)
        for j in range(7):
            t=.18+j*.09;c=knee.lerp(ankle,t)
            line('boot-lace',[(c.x-.025,c.y-.062,c.z),(c.x+.025,c.y-.060,c.z-.017)],[.0012,.0012],accent,8)
        shoulder=Vector((side*.175*width,0,pelvis+.42))
        elbow=Vector((side*.245,-.052,pelvis+.23))
        wrist=Vector((side*(.18 if sitting else .235),-.21 if sitting else -.025,pelvis+.075 if sitting else pelvis-.02))
        sleeve=top if outfit=='black_crop' else body
        ball('rounded-shoulder',shoulder,(.060,.061,.061),sleeve)
        shape('upper-arm',[(*shoulder,.055,.057),(*shoulder.lerp(elbow,.55),.047,.048),(*elbow,.037,.037)],sleeve)
        ball('elbow',elbow,(.039,.039,.038),sleeve)
        shape('forearm',[(*elbow,.037,.037),(*elbow.lerp(wrist,.45),.043,.037),(*wrist,.029,.023)],sleeve)
        direction=(wrist-elbow).normalized()
        parts+=build_hand({'side':'left' if side==1 else 'right','wrist':list(wrist),'direction':list(direction),'palm_normal':[0,-1,.35],'presentation':p['presentation'],'scale':.94,'curl':.22,'nail_length':.002},skin,materials[p['nail_material']],mesh_object)
    eye_mid=(anatomy.landmark('l-eye',p['presentation'])+anatomy.landmark('r-eye',p['presentation']))*.5
    parts+=build_portrait({**p,'center':[0,eye_mid.y,eye_z],'scale':1.,'rotation':[0,0,0]},materials,mesh_object,ellipsoid)
    if p.get('necklace'):
        points=[]
        for i in range(41):
            t=i/40;a=math.pi*t;points.append((.077*math.cos(a),-.091-.018*math.sin(a),pelvis+.39-.065*math.sin(a)))
        line('fine-necklace',points,[.0016]*len(points),accent,10)
    factor=p['height']/1.68
    garment_names=('thigh','knee','upper-shin','waistband','connected-hip-garment','shorts')
    trousers=[o for o in parts if o.data.materials and o.data.materials[0]==bottom and any(o.name.startswith(p['name']+'-'+n) for n in garment_names)]
    if outfit!='crop_skirt' and trousers:
        retained=[o for o in parts if o not in trousers]
        bpy.ops.object.select_all(action='DESELECT')
        for o in trousers:o.select_set(True)
        bpy.context.view_layer.objects.active=trousers[0];bpy.ops.object.join();garment=bpy.context.object
        remesh=garment.modifiers.new('Continuous trouser seams','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.006;remesh.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth=garment.modifiers.new('Soft garment seams','SMOOTH');smooth.factor=.75;smooth.iterations=8;bpy.ops.object.modifier_apply(modifier=smooth.name)
        parts=retained+[garment]
    # Join intersecting skin surfaces into a continuous shoulder/elbow/neck
    # surface; keep the high-resolution head and hands completely untouched.
    bare=[o for o in parts if o.data.materials and o.data.materials[0]==body]
    if bare:
        retained=[o for o in parts if o not in bare]
        bpy.ops.object.select_all(action='DESELECT')
        for o in bare:o.select_set(True)
        bpy.context.view_layer.objects.active=bare[0];bpy.ops.object.join();merged=bpy.context.object
        remesh=merged.modifiers.new('Continuous dressed body','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0035;remesh.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth=merged.modifiers.new('Soft joints','SMOOTH');smooth.factor=.7;smooth.iterations=10;bpy.ops.object.modifier_apply(modifier=smooth.name)
        # Joining invalidates removed object handles; retain by stable names.
        parts=retained+[merged]
    transform=Matrix.Translation(p['center'])@Matrix.Scale(factor,4)
    bpy.context.view_layer.update()
    for obj in parts:
        obj.matrix_world=transform@obj.matrix_world
        obj['character']=p['name'];obj['reference_likeness_verified']=False
    return parts
