"""Bounded, trusted geometry for smooth cross-sections and adult figurines.

These functions consume numeric parameters, never generated Python. A person is
a generic procedural adult; it is not a reconstruction of a named real person.
"""
import math
import bpy
from mathutils import Vector
from scene_contract import lathe_profile, round_sides, polygon_outline


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
    parts=[]
    skin,hair,top,pants,shoe,accent,eyes=[materials[p[k+'_material']] for k in ('skin','hair','top','trouser','shoe','accent','eye')]
    width={'slim':.90,'average':1.,'broad':1.13}[p['build']]
    shoulder=.95 if p['presentation']=='feminine' else 1.
    jaw=.85 if p['presentation']=='feminine' else .94 if p['presentation']=='androgynous' else 1.
    def ball(name,center,radii,mat,detail=3):
        obj=ellipsoid(name,center,radii,mat,subdivisions=detail)
        obj['garment']=name=='shoulder'
        parts.append(obj);return obj
    def shaped(name,stations,mat,folds=0,sides=48):
        obj=loft(name,[{'center':s[:3],'radii':s[3:]} for s in stations],sides,mat,mesh_object,folds)
        obj['garment']=name in {'pelvis','trouser-leg','top','sleeve'}
        parts.append(obj);return obj
    def line(name,points,radius,mat,sides=12):
        obj=tube(name,points,[radius]*len(points),mat,sides);parts.append(obj);return obj
    def lathe(name,profile,center,mat):
        obj=revolve(name,profile,center,64,mat,mesh_object);parts.append(obj);return obj

    # Continuous shaped clothing, with restrained geometric folds.
    shaped('pelvis',[(0,0,.87,.175*width,.092),(0,0,.98,.18*width,.10),(0,0,1.04,.164*width,.095)],pants,.012,64)
    for side in (-1,1):
        x=side*.096*width
        shaped('trouser-leg',[(x,0,.10,.057,.056),(x,-.004,.20,.060,.060),(x,-.018,.44,.070,.070),(x,0,.67,.081,.080),(x,0,.91,.099,.088),(x,0,.99,.105,.090)],pants,.025,64)
        # Shaped uppers and separate rubber soles, toe stitching and laces.
        shaped('shoe-upper',[(x,-.226,.056,.006,.006),(x,-.20,.065,.042,.027),(x,-.14,.074,.060,.040),(x,-.015,.079,.055,.049),(x,.056,.071,.047,.039),(x,.071,.070,.010,.016)],shoe,0,48)
        shaped('shoe-sole',[(x,-.23,.026,.006,.004),(x,-.202,.026,.046,.014),(x,-.13,.026,.064,.016),(x,.038,.026,.057,.016),(x,.075,.026,.012,.007)],eyes,0,48)
        for i,y in enumerate((-.112,-.080,-.048,-.016)):
            line('lace',[(x-.033,y,.115),(x,y+.010,.124),(x+.033,y,.115)],.0023,hair)
        line('shoe-stitch',[(x-.045,-.18,.09),(x-.027,-.19,.094),(x,-.194,.097),(x+.027,-.19,.094),(x+.045,-.18,.09)],.0013,accent)
    loose=1.06 if p['outfit']=='streetwear' else .94 if p['outfit']=='formal' else 1.
    shaped('top',[(0,0,.965,.18*width*loose,.112),(0,0,1.05,.18*width*loose,.107),(0,0,1.19,.175*width*loose,.105),(0,0,1.33,.205*width*loose,.11),(0,0,1.405,.226*width*shoulder,.099),(0,0,1.445,.19*width,.090),(0,0,1.470,.068,.059)],top,.016,64)
    ball('neck',(0,.007,1.51),(.050,.049,.084),skin)
    for side in (-1,1):
        raised=side==1 and (p['pose']=='performing' or p['microphone'])
        ball('shoulder',(side*.213*width,0,1.40),(.076,.079,.082),top)
        if raised:
            path=[(.214*width,0,1.405,.071,.072),(.275*width,-.012,1.30,.066,.068),(.35*width,-.035,1.165,.060,.061),(.353*width,-.12,1.205,.054,.054),(.31*width,-.202,1.267,.043,.046)]
        else:
            path=[(side*.214*width,0,1.405,.071,.072),(side*.26*width,0,1.31,.065,.066),(side*.285*width,-.008,1.15,.061,.062),(side*.315*width,-.008,.97,.047,.047),(side*.32*width,-.005,.90,.040,.043)]
        shaped('sleeve',path,top,.024,48)
        x,y,z=path[-1][:3]
        if raised:
            ball('palm',(x,y-.018,z+.027),(.034,.022,.046),skin)
            for k in range(4):
                dx=(k-1.5)*.016
                shaped('finger',[(x+dx,y-.03,z+.047,.009,.009),(x+dx,y-.061,z+.050,.008,.008),(x+dx,y-.065,z+.022,.007,.007)],skin,0,16)
            shaped('thumb',[(x-.034,y-.010,z+.027,.012,.012),(x-.045,y-.035,z+.043,.010,.010),(x-.032,y-.052,z+.051,.008,.008)],skin,0,16)
            if p['microphone']:
                shaped('microphone-handle',[(x,y-.049,z-.005,.015,.015),(x,y-.049,z+.135,.014,.014)],hair,0,32)
                ball('microphone-grille',(x,y-.049,z+.153),(.028,.028,.038),hair)
                for k in range(6):
                    line('grille-band',[(x+.027*math.cos(t*math.tau/24),y-.049+.027*math.sin(t*math.tau/24),z+.132+k*.006) for t in range(25)],.0011,accent,6)
        else:
            ball('palm',(x,y-.006,z-.043),(.037,.024,.060),skin)
            for k,length in enumerate((.062,.075,.071,.052)):
                dx=(k-1.5)*.017
                shaped('finger',[(x+dx,y-.012,z-.078,.0095,.010),(x+dx,y-.020,z-.095-length*.35,.009,.009),(x+dx,y-.028,z-.075-length,.007,.007)],skin,0,16)
            shaped('thumb',[(x-side*.035,y-.005,z-.023,.014,.015),(x-side*.050,y-.017,z-.054,.012,.011),(x-side*.054,y-.032,z-.079,.008,.008)],skin,0,20)

    # A single dense, sculpted head mesh. Facial relief changes the surface,
    # rather than merely placing a tiny nose on a low-poly sphere.
    verts,faces,rings=[],[],[]
    segments,levels=96,72
    def gauss(x,z,cx,cz,sx,sz):return math.exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
    for i in range(levels+1):
        phi=math.pi*i/levels
        z=1.665+.126*math.cos(phi)
        ring=[]
        for j in range(1 if i in (0,levels) else segments):
            angle=j*math.tau/segments
            taper=1-(1-jaw)*max(0,(1.66-z)/.12)
            x=.091*math.sin(phi)*math.cos(angle)*taper
            y=.096*math.sin(phi)*math.sin(angle)
            forward=max(0,-math.sin(angle))**8
            relief=.026*gauss(x,z,0,1.667,.013,.047)+.033*gauss(x,z,0,1.631,.014,.012)
            relief+=.012*gauss(x,z,-.015,1.625,.009,.008)+.012*gauss(x,z,.015,1.625,.009,.008)
            relief+=.012*gauss(x,z,-.047,1.649,.027,.027)+.012*gauss(x,z,.047,1.649,.027,.027)
            relief-=.012*gauss(x,z,-.035,1.687,.023,.014)+.012*gauss(x,z,.035,1.687,.023,.014)
            relief+=.014*gauss(x,z,0,1.600,.034,.012)+.014*gauss(x,z,0,1.568,.048,.018)
            y-=forward*relief
            ring.append(len(verts));verts.append((x,y,z))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for j in range(segments):
            face=tuple(dict.fromkeys((a[j%len(a)],b[j%len(b)],b[(j+1)%len(b)],a[(j+1)%len(a)])))
            if len(face)>=3:faces.append(face)
    head=smooth(mesh_object('sculpted-face',verts,faces,skin));parts.append(head)
    for side in (-1,1):
        x=side*.034
        ball('eye-white',(x,-.087,1.684),(.017,.009,.0068),eyes)
        ball('iris',(x,-.0955,1.684),(.0045,.0012,.0048),hair)
        ball('eye-highlight',(x-.0015,-.0968,1.686),(.001,.0005,.001),eyes,2)
        for upper in (-1,1):
            line('eyelid',[(x+.017*math.cos(t*math.pi/18),-.086-.009*math.sin(t*math.pi/18),1.684+upper*.0065*math.sin(t*math.pi/18)) for t in range(19)],.0015,skin)
        line('eyebrow',[(x-.021+t*.04/18,-.084-.009*math.sin(t*math.pi/18),1.705+.006*math.sin(t*math.pi/18)) for t in range(19)],.002,hair)
        ball('ear',(side*.089,.004,1.665),(.014,.020,.033),skin)
        line('ear-helix',[(side*(.093+.006*math.sin(t*math.pi/18)),.004+.015*math.cos(t*math.pi/18),1.665+.027*math.sin(t*math.pi/18)) for t in range(37)],.003,skin)
        ball('nostril',(side*.012,-.123,1.623),(.003,.0015,.0018),hair,2)
    for lip,offset,mat,radius in [('mouth-crease',0,hair,.0007),('upper-lip',.002,skin,.0016),('lower-lip',-.0025,skin,.0018)]:
        line(lip,[(x,-.097-.006*math.cos(x/.023*math.pi/2),1.600+offset+.001*math.sin(abs(x)/.023*math.pi)) for x in [(-1+i/12)*.023 for i in range(25)]],radius,mat)
    # Rounded cap/beanie with a shaped brim, or cropped hair.
    if p['headwear']=='cap':
        lathe('cap',[[0,0],[.095,0],[.098,.023],[.089,.056],[.065,.077],[0,.088],[0,0]],(0,.006,1.715),hair)
        ball('cap-brim',(0,-.091,1.738),(.096,.074,.007),hair)
        line('cap-stitch',[(.088*math.cos(t*math.pi/32),-.091-.065*math.sin(t*math.pi/32),1.741) for t in range(33)],.0009,accent)
    elif p['headwear']=='beanie':
        lathe('beanie',[[0,0]]+[[.101*math.cos(i*math.pi/32),.104*math.sin(i*math.pi/32)] for i in range(16)]+[[0,.104],[0,0]],(0,.004,1.709),hair)
        lathe('beanie-cuff',[[.099,0],[.104,0],[.104,.023],[.099,.023],[.099,0]],(0,.004,1.709),hair)
    else:
        lathe('cropped-hair',[[0,0],[.081,0],[.087,.010],[.073,.037],[0,.061],[0,0]],(0,.012,1.735),hair)
    if p['necklace']:
        for i in range(38):
            t=i/37
            x=(t-.5)*.28
            y=-.086-.05*math.sin(t*math.pi)
            z=1.435-.145*math.sin(t*math.pi)
            bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=6,major_radius=.0075,minor_radius=.0019,location=(x,y,z),rotation=(math.pi/2,0,(i%2)*math.pi/2))
            obj=bpy.context.object;obj.name='necklace-link';obj.scale=(1,1.35,1);obj.data.materials.append(accent);parts.append(smooth(obj))
    if p['outfit']=='formal':
        line('jacket-lapel',[(-.07,-.080,1.459),(-.12,-.109,1.32),(0,-.114,1.16),(.12,-.109,1.32),(.07,-.080,1.459)],.006,accent)
    elif p['outfit']=='streetwear':
        for side in (-1,1):line('hoodie-drawstring',[(side*.045,-.057,1.455),(side*.055,-.107,1.40),(side*.050,-.116,1.335)],.0023,accent)
    # Remesh garment pieces only, even when skin and clothes share a material.
    # Fixed resolution and one subdivision keep this operation bounded.
    garments={}
    for obj in parts:
        if obj.get('garment'):garments.setdefault(obj.data.materials[0].name,[]).append(obj)
    parts=[obj for obj in parts if not obj.get('garment')]
    for material,group in garments.items():
        obj=join_meshes(group,p['name']+'-garment-'+material)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        remesh=obj.modifiers.new('continuous-garment','REMESH')
        remesh.mode='VOXEL';remesh.voxel_size=.012;remesh.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        soften=obj.modifiers.new('garment-surface','SMOOTH');soften.factor=.65;soften.iterations=4
        bpy.ops.object.modifier_apply(modifier=soften.name)
        subdiv=obj.modifiers.new('garment-detail','SUBSURF');subdiv.levels=1
        bpy.ops.object.modifier_apply(modifier=subdiv.name)
        parts.append(smooth(obj))
    # Join only pieces sharing material. The GLB stays light and editable by group.
    grouped={}
    for obj in parts:grouped.setdefault(obj.data.materials[0].name,[]).append(obj)
    result=[]
    for material,group in grouped.items():
        obj=join_meshes(group,p['name']+'-'+material)
        factor=p['height']/1.815
        obj.location=Vector(p['center'])+obj.location*factor
        obj.scale*=factor
        result.append(obj)
    return result
