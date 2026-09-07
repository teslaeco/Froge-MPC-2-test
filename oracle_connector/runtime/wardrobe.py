"""Bounded garment finishing and footwear; all geometry is trusted local code."""
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def finish_cloth(obj, role, width):
    """Compression folds survive the garment union, instead of being erased by it."""
    for vertex in obj.data.vertices:
        v=vertex.co
        if role=='pants':
            side=1 if v.x>0 else -1
            cx=side*.096*width
            angle=math.atan2(v.y, v.x-cx)
            wave=(.004*math.exp(-((v.z-.23)/.080)**2)*math.sin(v.z*74+angle*2)
                  +.0035*math.exp(-((v.z-.51)/.070)**2)*math.sin(v.z*58-angle*2)
                  +.002*math.exp(-((v.z-.84)/.060)**2)*math.sin(v.z*61+angle))
            wave*=.20+.80*max(0,-math.sin(angle))**2
            normal=Vector((v.x-cx,v.y,0)).normalized()
        else:
            angle=math.atan2(v.y,v.x)
            wave=.003*math.exp(-((v.z-1.035)/.060)**2)*math.sin(v.z*68+angle*3)
            if abs(v.x)>.235*width:
                wave+=.003*math.exp(-((v.z-1.15)/.08)**2)*math.sin(v.z*67+angle*4)
            else:
                wave+=.0016*math.sin(angle*9+v.z*6)*math.exp(-((v.z-1.20)/.21)**2)
            normal=Vector((v.x,v.y*1.6,0)).normalized()
        vertex.co+=normal*wave
    obj.data.update()


def details(p, garment, width, top, pants, hair, accent, mesh_object, tube, loft):
    parts=[]
    def line(name,points,radius,material):
        obj=tube(name,points,[radius]*len(points),material,8);parts.append(obj);return obj
    def ring(name,center,rx,ry,height,material,ribs=0):
        count=96;vertices=[];faces=[]
        for dz,scale in ((0,.99),(.003,1.02),(height-.003,1.02),(height,.99)):
            for i in range(count):
                t=i*math.tau/count;r=scale+(ribs*.016*math.cos(t*48))
                vertices.append((center[0]+rx*math.cos(t)*r,center[1]+ry*math.sin(t)*r,center[2]+dz))
        for row in range(3):
            for i in range(count):faces.append((row*count+i,row*count+(i+1)%count,(row+1)*count+(i+1)%count,(row+1)*count+i))
        obj=mesh_object(name,vertices,faces,material)
        for f in obj.data.polygons:f.use_smooth=True
        shell=obj.modifiers.new('rib-knit-thickness','SOLIDIFY');shell.thickness=.003
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=shell.name)
        parts.append(obj)
    body=garment['top'];surface=BVHTree.FromPolygons([v.co for v in body.data.vertices],[f.vertices[:] for f in body.data.polygons])
    def on_front(x,z,offset=.002):
        point,normal,_,_=surface.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
        return tuple(point+normal*offset) if point else (x,-.105,z)
    def patch(name,corners,material):
        # Subdivided bilinear panel follows the actual post-union clothing surface.
        verts=[];faces=[];n=12
        for row in range(n+1):
            v=row/n
            for col in range(n+1):
                u=col/n
                x=(1-v)*((1-u)*corners[0][0]+u*corners[1][0])+v*((1-u)*corners[3][0]+u*corners[2][0])
                z=(1-v)*((1-u)*corners[0][1]+u*corners[1][1])+v*((1-u)*corners[3][1]+u*corners[2][1])
                verts.append(on_front(x,z,.003+.0015*math.sin(math.pi*u)*math.sin(math.pi*v)))
        for row in range(n):
            for col in range(n):
                a=row*(n+1)+col;faces.append((a,a+1,a+n+2,a+n+1))
        obj=mesh_object(name,verts,faces,material)
        for f in obj.data.polygons:f.use_smooth=True
        parts.append(obj)
        for a,b in zip(corners,corners[1:]+corners[:1]):
            line(name+'-seam',[on_front(a[0]+(b[0]-a[0])*i/20,a[1]+(b[1]-a[1])*i/20,.005) for i in range(21)],.0011,material)
    loose=1.06 if p['outfit'] in ('streetwear','hoodie','tshirt') else .94 if p['outfit']=='formal' else 1.
    if p['outfit']!='tshirt':ring('ribbed-waistband',(0,0,.974),.186*width*loose,.117,.018,top,1)
    ring('neck-ribbing',(0,-.019,1.482),.065,.065,.009,top,0)
    for side in (-1,1):
        x=side*.105*width;dy=-.025 if side==-1 else .014
        if p['outfit']!='tshirt':ring('trouser-cuff',(x,dy,.135),.061,.060,.020,pants,1 if p['outfit']=='streetwear' else 0)
        # Pressed side seams and front pocket entries stay on the actual trousers.
        trouser=garment['pants'];tree=BVHTree.FromPolygons([v.co for v in trouser.data.vertices],[f.vertices[:] for f in trouser.data.polygons])
        points=[]
        for i in range(28):
            z=.28+i/27*.68;xx=side*(.096*width+.044)
            hit,normal,_,_=tree.ray_cast(Vector((xx,-1,z)),Vector((0,1,0)))
            if hit:points.append(tuple(hit+normal*.001))
        if len(points)>1:line('trouser-seam',points,.0008,pants)
    if p['outfit'] in ('streetwear','hoodie'):
        patch('kangaroo-pocket',[(-.105*width,1.030),(.105*width,1.030),(.072*width,1.148),(-.072*width,1.148)],top)
        # A folded hood is a thick draped collar around the back of the neck.
        vertices=[];faces=[];n=64;m=10
        for i in range(n+1):
            a=-.20+(math.pi+.40)*i/n
            for j in range(m+1):
                t=j/m
                radius=.077+.055*math.sin(math.pi*t*.90)
                vertices.append((radius*math.cos(a),-.015+radius*math.sin(a),1.480-.060*t-.025*math.sin(a)*math.sin(math.pi*t)))
        for i in range(n):
            for j in range(m):
                a=i*(m+1)+j;faces.append((a,a+m+1,a+m+2,a+1))
        hood=mesh_object('folded-hood',vertices,faces,top)
        for f in hood.data.polygons:f.use_smooth=True
        shell=hood.modifiers.new('hood-thickness','SOLIDIFY');shell.thickness=.008
        bpy.context.view_layer.objects.active=hood;bpy.ops.object.modifier_apply(modifier=shell.name);parts.append(hood)
        for side in (-1,1):
            line('drawstring',[on_front(side*.045,1.47,.006),on_front(side*.052,1.40,.007),on_front(side*.045,1.345,.010)],.0021,hair)
            line('drawstring-tip',[on_front(side*.045,1.345,.011),on_front(side*.045,1.328,.011)],.0026,accent)
    elif p['outfit']=='formal':
        for side in (-1,1):
            patch('jacket-lapel',[(side*.020,1.21),(side*.12,1.36),(side*.073,1.45),(side*.043,1.41)],top)
            patch('jacket-pocket',[(side*.040,1.075),(side*.130,1.075),(side*.130,1.099),(side*.040,1.099)],top)
        line('jacket-front',[on_front(.007,1.04+i/32*.22,.004) for i in range(33)],.0012,hair)
    elif p['outfit']=='casual':
        patch('chest-pocket',[(.055,1.29),(.113,1.29),(.113,1.36),(.055,1.36)],top)
    return parts


def sneaker(x,dy,angle,shoe,trim,cloth,mesh_object,tube):
    """Flat outsole, continuous upper, layered panels, heel tab and crossed laces."""
    parts=[]
    def mesh(name,vertices,faces,material):
        obj=mesh_object(name,vertices,faces,material)
        for f in obj.data.polygons:f.use_smooth=True
        parts.append(obj);return obj
    def line(name,points,radius,material):
        obj=tube(name,points,[radius]*len(points),material,8);parts.append(obj)
    n=80
    def outline(t):
        y=-.065+.155*math.sin(t)
        xx=.060*math.copysign(abs(math.cos(t))**.70,math.cos(t))*(1.02-.10*math.sin(t))
        return xx,y
    for name,levels,material in (
        ('rubber-outsole',[(.000,.96),(.003,1.02),(.010,1.02),(.013,1.0)],trim),
        ('sculpted-midsole',[(.011,1.0),(.018,1.025),(.031,1.0),(.038,.96)],shoe)):
        verts=[];faces=[]
        for z,scale in levels:
            for i in range(n):
                xx,y=outline(i*math.tau/n);verts.append((xx*scale,(y+.065)*scale-.065,z))
        for row in range(len(levels)-1):
            for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
        faces.extend([tuple(reversed(range(n))),tuple((len(levels)-1)*n+i for i in range(n))])
        obj=mesh(name,verts,faces,material);obj['shoe_solid']=True
        obj.data.polygons[-1].use_smooth=False;obj.data.polygons[-2].use_smooth=False
    stations=[(-.219,.012,.011),(-.214,.024,.023),(-.200,.046,.034),(-.175,.058,.044),(-.140,.060,.051),(-.100,.056,.066),(-.060,.052,.090),(-.020,.050,.110),(.018,.050,.114),(.055,.047,.097),(.077,.035,.071),(.083,.012,.045)]
    verts=[];faces=[];sides=48
    for y,w,h in stations:
        for j in range(sides):
            t=j*math.tau/sides;s=math.sin(t)
            verts.append((w*math.cos(t),y,.036+(h*max(0,s)**.68 if s>=0 else .004*s)))
    for i in range(len(stations)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(stations)-1)*sides+j for j in range(sides))])
    upper=mesh('sneaker-upper',verts,[tuple(reversed(f)) for f in faces],shoe)
    bpy.context.view_layer.objects.active=upper
    subdiv=upper.modifiers.new('upper-surface','SUBSURF');subdiv.levels=2;bpy.ops.object.modifier_apply(modifier=subdiv.name)
    tree=BVHTree.FromPolygons([v.co for v in upper.data.vertices],[f.vertices[:] for f in upper.data.polygons])
    def top(xx,y,offset=.0015):
        hit,normal,_,_=tree.ray_cast(Vector((xx,y,.5)),Vector((0,0,-1)))
        return tuple(hit+normal*offset) if hit else (xx,y,.13)
    # Toe seam and five genuine crossed lace pairs lie on the same upper.
    line('toe-panel-stitch',[top(-.049+i*.098/24,-.148-.025*math.sin(math.pi*i/24)) for i in range(25)],.0009,trim)
    for i in range(5):
        y=-.120+i*.024
        for side in (-1,1):
            line('crossed-lace',[top(side*.028,y,.004),top(0,y+.012,.008),top(-side*.027,y+.024,.004)],.0021,shoe)
            line('lace-eyelet',[top(side*.033,y-.004,.002),top(side*.032,y+.004,.002)],.0030,trim)
    for side in (-1,1):
        # Project every panel sample onto the upper: no floating heel wings.
        def on_side(y,z):
            hit,normal,_,_=tree.ray_cast(Vector((side*.3,y,z)),Vector((-side,0,0)))
            if hit is None:raise ValueError('Panel buta wychodzi poza cholewke.')
            return tuple(hit+normal*.0015)
        corners=[(-.095,.051),(-.042,.083),(.043,.096),(.060,.051)]
        vertices=[];faces=[];n=10
        for row in range(n+1):
            v=row/n
            for col in range(n+1):
                u=col/n
                y=(1-v)*((1-u)*corners[0][0]+u*corners[1][0])+v*((1-u)*corners[3][0]+u*corners[2][0])
                z=(1-v)*((1-u)*corners[0][1]+u*corners[1][1])+v*((1-u)*corners[3][1]+u*corners[2][1])
                vertices.append(on_side(y,z))
        for row in range(n):
            for col in range(n):
                a=row*(n+1)+col;face=(a,a+1,a+n+2,a+n+1);faces.append(face if side==1 else tuple(reversed(face)))
        overlay=mesh('quarter-panel',vertices,faces,cloth)
        shell=overlay.modifiers.new('panel-thickness','SOLIDIFY');shell.thickness=.0015
        bpy.context.view_layer.objects.active=overlay;bpy.ops.object.modifier_apply(modifier=shell.name)
        for a,b in zip(corners,corners[1:]+corners[:1]):
            line('quarter-stitch',[on_side(a[0]+(b[0]-a[0])*i/16,a[1]+(b[1]-a[1])*i/16) for i in range(17)],.00085,shoe)
    # Heel pull tab, toe perforations, and visible sidewall grooves.
    line('heel-tab',[(-.012,.077,.092),(-.012,.080,.136),(.012,.080,.136),(.012,.077,.092)],.003,trim)
    for row in range(2):
        for col in range(5):
            xx=(col-2)*.012;y=-.183+row*.012
            q=Vector(top(xx,y,.0017));line('toe-perforation',[tuple(q-Vector((.0007,0,0))),tuple(q+Vector((.0007,0,0)))],.00065,trim)
    for side in (-1,1):
        for i in range(12):
            y=-.160+i*.018
            points=[]
            for yy,z in ((y,.016),(y+.004,.026)):
                sy=(yy+.065)/.155
                xx=.060*(1-sy*sy)**.35*(1.02-.10*sy)*1.024
                points.append((side*xx,yy,z))
            line('sole-groove',points,.0007,trim)
    co,si=math.cos(angle),math.sin(angle)
    for obj in parts:
        for v in obj.data.vertices:
            xx,y,z=v.co;v.co=(x+co*xx-si*y,dy+si*xx+co*y,z)
    return parts


def fabric_uv(obj):
    """Assign UVs before material joins; preserve a consistent weave scale in metres."""
    layer=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
    for face in obj.data.polygons:
        normal=face.normal
        axes=(0,2) if abs(normal.y)>=max(abs(normal.x),abs(normal.z)) else (1,2) if abs(normal.x)>abs(normal.z) else (0,1)
        for loop in face.loop_indices:
            v=obj.matrix_world@obj.data.vertices[obj.data.loops[loop].vertex_index].co
            layer.data[loop].uv=(v[axes[0]]*2.5,v[axes[1]]*2.5)


def open_sleeves(obj, ends, width):
    """Trim the two sleeve ends locally; leave the torso and anatomy intact."""
    bm=bmesh.new();bm.from_mesh(obj.data)
    for side,origin,axis in ends:
        origin=Vector(origin)-Vector(axis)*.018
        vertices=[v for v in bm.verts if v.co.x*side>.205*width]
        selected=set(vertices)
        edges=[e for e in bm.edges if all(v in selected for v in e.verts)]
        faces=[f for f in bm.faces if all(v in selected for v in f.verts)]
        bmesh.ops.bisect_plane(bm,geom=vertices+edges+faces,dist=1e-6,plane_co=origin,plane_no=-Vector(axis),clear_inner=True)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
