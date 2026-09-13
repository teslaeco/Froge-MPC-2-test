"""Bounded, trusted geometry for smooth cross-sections and adult figurines.

These functions consume numeric parameters, never generated Python. A person is
a generic procedural adult; it is not a reconstruction of a named real person.
"""
import math
import bpy
from mathutils import Vector
from scene_contract import lathe_profile, round_sides, polygon_outline
import anatomy
import wardrobe


def smooth(obj):
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def revolve(name, profile, center, sides, material, mesh_object):
    contour, sides = lathe_profile(profile), round_sides(sides)
    vertices, faces, rings, uv_points, lateral = [], [], [], [], []
    base = Vector(center)
    low, high = min(p[1] for p in contour), max(p[1] for p in contour)
    for radius, z in contour:
        ring = []
        for i in range(sides if radius > 0 else 1):
            ring.append(len(vertices))
            vertices.append(tuple(base + Vector((radius*math.cos(i*math.tau/sides), radius*math.sin(i*math.tau/sides), z))))
            uv_points.append((i/sides, (z-low)/(high-low)))
        rings.append(ring)
    for n,a in enumerate(rings):
        b = rings[(n+1)%len(rings)]
        if len(a) == len(b) == 1:
            continue
        for i in range(sides):
            face = tuple(dict.fromkeys((a[i%len(a)],a[(i+1)%len(a)],b[(i+1)%len(b)],b[i%len(b)])))
            if len(face) >= 3:
                faces.append(face)
                lateral.append(abs(contour[(n+1)%len(contour)][1]-contour[n][1]) > 1e-10 and sides >= 12)
    obj = mesh_object(name,vertices,faces,material)
    for polygon, rounded in zip(obj.data.polygons,lateral):
        polygon.use_smooth = rounded
    obj.data.set_sharp_from_angle(angle=math.radians(35))
    uv = obj.data.uv_layers.new(name='UVMap')
    for poly in obj.data.polygons:
        values=[uv_points[obj.data.loops[i].vertex_index] for i in poly.loop_indices]
        seam=max(u for u,v in values)-min(u for u,v in values)>.5
        for i,(u,v) in zip(poly.loop_indices,values):
            uv.data[i].uv=(u+1 if seam and u<.5 else u,v)
    return obj


def loft(name, sections, sides, material, mesh_object, folds=0):
    """Catmull-Rom centers, bounded radii, and transported ellipse frames."""
    controls=[list(p['center'])+list(p['radii']) for p in sections]
    samples=[]
    for i in range(len(controls)-1):
        a,b,c,d=controls[max(0,i-1)],controls[i],controls[i+1],controls[min(len(controls)-1,i+2)]
        for j in range(6):
            t=j/6
            sample=[.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in range(5)]
            for k in (3,4):sample[k]=max(min(b[k],c[k]),min(max(b[k],c[k]),sample[k]))
            samples.append(sample)
    samples.append(controls[-1])
    points=[Vector(p[:3]) for p in samples]
    verts,faces=[],[]
    axis=None
    for i,point in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        if tangent.length < 1e-8:raise ValueError('Loft ma pokrywajace sie probki srodka.')
        if axis is None:axis=Vector((1,0,0)) if abs(tangent.x)<.9 else Vector((0,1,0))
        axis=axis-tangent*axis.dot(tangent)
        if axis.length<1e-6:axis=tangent.cross(Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0)))
        axis.normalize(); other=tangent.cross(axis).normalized()
        for j in range(sides):
            theta=j*math.tau/sides
            wave=1+folds*math.sin(theta*5+i*.31)*math.sin(math.pi*i/(len(points)-1))**2
            verts.append(tuple(point+axis*(samples[i][3]*math.cos(theta)*wave)+other*(samples[i][4]*math.sin(theta)*wave)))
    for i in range(len(points)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]
    obj=smooth(mesh_object(name,verts,faces,material))
    obj.data.polygons[-1].use_smooth=False;obj.data.polygons[-2].use_smooth=False
    uv=obj.data.uv_layers.new(name='UVMap')
    for poly in obj.data.polygons:
        values=[divmod(obj.data.loops[i].vertex_index,sides) for i in poly.loop_indices]
        seam=max(j for n,j in values)-min(j for n,j in values)>sides/2
        for i,(n,j) in zip(poly.loop_indices,values):uv.data[i].uv=(j/sides+(1 if seam and j==0 else 0),n/(len(points)-1))
    return obj


def extrusion(p, material, cap_material, mesh_object):
    outline=polygon_outline(p['outline']);n=len(outline)
    levels=p['levels'];base=Vector(p['center'])
    vertices=[tuple(base+Vector((x*s['scale']+s['offset'][0],y*s['scale']+s['offset'][1],s['z']))) for s in levels for x,y in outline]
    faces=[]
    for i in range(len(levels)-1):
        for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    faces += [tuple(reversed(range(n))),tuple((len(levels)-1)*n+j for j in range(n))]
    obj=mesh_object(p['name'],vertices,faces,material);obj.data.materials.append(cap_material)
    uv=obj.data.uv_layers.new(name='UVMap')
    cumulative=[0]
    for a,b in zip(outline,outline[1:]+outline[:1]):cumulative.append(cumulative[-1]+math.dist(a,b))
    low,high=levels[0]['z'],levels[-1]['z']
    for index,face in enumerate(obj.data.polygons):
        if index >= (len(levels)-1)*n:
            face.material_index=1
            continue
        level,edge=divmod(index,n)
        terrace=levels[level+1]['z']==levels[level]['z']
        face.material_index=1 if terrace else 0
        values=[(cumulative[edge]/cumulative[-1],(levels[level]['z']-low)/(high-low)),
                (cumulative[edge+1]/cumulative[-1],(levels[level]['z']-low)/(high-low)),
                (cumulative[edge+1]/cumulative[-1],(levels[level+1]['z']-low)/(high-low)),
                (cumulative[edge]/cumulative[-1],(levels[level+1]['z']-low)/(high-low))]
        for loop,value in zip(face.loop_indices,values):uv.data[loop].uv=value
    return obj


def person(p, materials, mesh_object, tube, ellipsoid, join_meshes):
    if p['outfit'] in ('crop_skirt','puffer_crop','black_crop'):
        from fashion import fashion_person
        return fashion_person(p,materials,mesh_object,tube,ellipsoid)
    import portrait
    from portrait_hands import build_hand
    parts=[]
    skin,hair,top,pants,shoe,accent,eyes=[materials[p[k+'_material']] for k in ('skin','hair','top','trouser','shoe','accent','eye')]
    if skin in (hair,top,pants,shoe,accent,eyes) and len(bpy.data.materials)<8:
        skin=skin.copy();skin.name+='-anatomy'
    tee=p['outfit']=='tshirt'
    sleeve_ends=[]
    width={'slim':.90,'average':1.,'broad':1.13}[p['build']]
    feminine=p['presentation']=='feminine'
    shoulder=.92 if feminine else 1.
    hip=1.04 if feminine else 1.
    waist=.90 if feminine else 1.
    def ball(name,center,radii,mat,detail=3):
        obj=ellipsoid(name,center,radii,mat,subdivisions=detail)
        obj['garment']='top' if name=='shoulder' else ''
        parts.append(obj);return obj
    def shaped(name,stations,mat,folds=0,sides=48):
        obj=loft(name,[{'center':s[:3],'radii':s[3:]} for s in stations],sides,mat,mesh_object,folds)
        obj['garment']='pants' if name in {'pelvis','trouser-leg'} else 'top' if name in {'top','sleeve'} else ''
        parts.append(obj);return obj
    def line(name,points,radius,mat,sides=12):
        obj=tube(name,points,[radius]*len(points),mat,sides);parts.append(obj);return obj
    def lathe(name,profile,center,mat):
        obj=revolve(name,profile,center,64,mat,mesh_object);parts.append(obj);return obj

    # Relaxed weight distribution: wider ankle spacing and a small forward step.
    shaped('pelvis',[(0,0,.87,.169*width*hip,.093),(0,0,.98,.177*width*hip,.10),(0,0,1.04,.164*width,.095)],pants,.012,64)
    for side in (-1,1):
        x=side*.105*width;dy=-.025 if side==-1 else .014
        shaped('trouser-leg',[(x,dy,.14,.065 if tee else .054,.062 if tee else .051),(x,dy,.24,.069 if tee else .063,.066 if tee else .063),(x+side*.006,dy-.020,.45,.069,.073),(side*.096*width,-.016,.67,.079,.084),(side*.093*width,0,.89,.098,.090),(side*.093*width,0,.99,.103,.091)],pants,0,64)
        parts.extend(wardrobe.sneaker(x,dy,side*.08,shoe,accent,shoe,mesh_object,tube))
    loose=1.06 if p['outfit'] in ('streetwear','hoodie','tshirt') else .94 if p['outfit']=='formal' else 1.
    fitted=p.get('clothing_fit')=='fitted'
    if fitted:loose=.97
    # Fitted tees overlap the waistband without an oversized hem over the seat.
    hem=.985 if tee and fitted else .900 if tee else .965
    second=1.025 if tee and fitted else .955 if tee else 1.00
    shaped('top',[(0,0,hem,.193*width*loose,.113 if fitted else .127),(0,0,second,.190*width*loose,.112 if fitted else .125),(0,0,1.05,.18*width*loose*waist,.115),(0,0,1.19,.175*width*loose*waist,.109),(0,0,1.33,.205*width*loose,.11),(0,0,1.412,.198*width*shoulder,.093),(0,0,1.442,.140*width,.074),(0,-.015,1.470,.073,.062),(0,-.019,1.490,.065,.065)],top,.012,64)
    for side in (-1,1):
        raised=side==1 and (p['pose']=='performing' or p['microphone'])
        if raised:
            path=[(.155*width,0,1.385,.048,.050),(.205*width,0,1.365,.059,.058),(.27*width,-.012,1.30,.067,.069),(.332*width,-.051,1.205,.060,.061),(.344*width,-.113,1.200,.056,.056),(.31*width,-.202,1.267,.042,.044)]
        else:
            path=[(side*.155*width,0,1.385,.048,.050),(side*.205*width,0,1.365,.059,.058),(side*.245*width,0,1.305,.059,.062),(side*.281*width,-.008,1.16,.059,.062),(side*.297*width,-.020,1.04,.050,.053),(side*.29*width,-.055,.93,.039,.042)]
        # Keep sleeves, arms and gripping hands on the same shoulder frame.
        # Previously only the torso narrowed for feminine presentation.
        path=[(x*shoulder,y,z,rx,ry) for x,y,z,rx,ry in path]
        sleeve_path=path
        if tee:
            sleeve_path=path[:3]+[tuple(path[3][:3])+(.064,.063)]
            parts.append(anatomy.forearm(side,path[3][:3],path[-1][:3],p['presentation'],skin,mesh_object,include_hand=False,sleeve_axis=Vector(path[3][:3])-Vector(path[2][:3])))
            sleeve_ends.append((side,path[3][:3],(Vector(path[3][:3])-Vector(path[2][:3])).normalized()))
        shaped('sleeve',sleeve_path,top,.014,48)
        x,y,z=path[-1][:3]
        direction=(Vector(path[-1][:3])-Vector(path[-2][:3])).normalized()
        a=Vector((x,y,z))-direction*.026;b=Vector((x,y,z))+direction*.008
        if not tee:shaped('sleeve-cuff',[(*a,.041,.042),(*b,.040,.041)],top,0,48)
        direction=Vector((.1,-.96,.27) if raised else (0,-.12,-1)).normalized()
        built=build_hand({'side':'left' if side==1 else 'right','wrist':(x,y,z),'direction':direction,'palm_normal':(side,0,.1),'presentation':p['presentation'],'scale':1.,'curl':1.65 if raised else .18,'nail_length':.001},skin,materials[p['nail_material']],mesh_object)
        parts.extend(built);hand=built[0]
        hand['grip_center']=list(Vector((x,y,z))+direction*.095)
        hand['grip_axis']=[0,0,1]
        if raised and p['microphone']:
            grip=Vector(hand['grip_center']);direction=Vector(hand['grip_axis'])
            shaped('microphone-handle',[(*tuple(grip-direction*.080),.014,.014),(*tuple(grip+direction*.080),.014,.014)],hair,0,32)
            grille=ball('microphone-grille',tuple(grip+direction*.105),(.026,.026,.035),hair)
            grille.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    parts.extend(portrait.head(p,skin,eyes,hair,mesh_object,ellipsoid))
    if p['headwear']=='cap':
        ball('cap-brim',(0,-.157,1.744),(.094,.074,.006),hair)
    if p['necklace']:
        for i in range(38):
            t=i/37
            x=(t-.5)*.28
            y=-.086-.05*math.sin(t*math.pi)
            z=1.435-.145*math.sin(t*math.pi)
            bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=6,major_radius=.0075,minor_radius=.0019,location=(x,y,z),rotation=(math.pi/2,0,(i%2)*math.pi/2))
            obj=bpy.context.object;obj.name='necklace-link';obj.scale=(1,1.35,1);obj.data.materials.append(accent);parts.append(smooth(obj))
    # Remesh garment pieces only, even when skin and clothes share a material.
    # Fixed resolution and one subdivision keep this operation bounded.
    garments={}
    for obj in parts:
        if obj.get('garment'):garments.setdefault(obj['garment'],[]).append(obj)
    parts=[obj for obj in parts if not obj.get('garment')]
    finished={}
    for role,group in garments.items():
        obj=join_meshes(group,p['name']+'-garment-'+role)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        remesh=obj.modifiers.new('continuous-garment','REMESH')
        remesh.mode='VOXEL';remesh.voxel_size=.012;remesh.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        soften=obj.modifiers.new('garment-surface','SMOOTH');soften.factor=.65;soften.iterations=4
        bpy.ops.object.modifier_apply(modifier=soften.name)
        subdiv=obj.modifiers.new('garment-detail','SUBSURF');subdiv.levels=1
        bpy.ops.object.modifier_apply(modifier=subdiv.name)
        wardrobe.fit_silhouette(obj,role,p,width)
        wardrobe.finish_cloth(obj,role,width,tee)
        if tee and role=='top':wardrobe.open_sleeves(obj,sleeve_ends,width)
        finished[role]=obj
        parts.append(smooth(obj))
    wardrobe.clear_trousers(finished['top'],finished['pants'])
    parts.extend(wardrobe.details(p,finished,width,top,pants,hair,accent,mesh_object,tube,loft))
    for obj in parts:
        if not obj.name.startswith(('anatomical','eyebrow','fitted','beanie')):wardrobe.fabric_uv(obj)
    # A subtle lateral weight shift follows all parts, including accessories.
    for obj in parts:
        for vertex in obj.data.vertices:
            v=obj.matrix_world @ vertex.co
            v.x+=.012*math.sin(math.pi*max(0,min(1,v.z/1.8)))
            vertex.co=obj.matrix_world.inverted() @ v
    # Join only pieces sharing material. The GLB stays light and editable by group.
    bpy.context.view_layer.update()
    bounds=[obj.matrix_world @ Vector(corner) for obj in parts for corner in obj.bound_box]
    floor=min(v.z for v in bounds);factor=p['height']/(max(v.z for v in bounds)-floor)
    grouped={}
    for obj in parts:
        preserve=('upper_lashes_per_eye' in obj or
                  any(obj.get(key) for key in ('anatomical_head','anatomical_hand','anatomical_eye','anatomical_nail')))
        grouped.setdefault(obj.name if preserve else obj.data.materials[0].name,[]).append(obj)
    result=[]
    for material,group in grouped.items():
        obj=join_meshes(group,p['name']+'-'+material)
        obj.location=Vector(p['center'])+(obj.location-Vector((0,0,floor)))*factor
        obj.scale*=factor
        obj['froge_kind']='person'
        result.append(obj)
    return result
