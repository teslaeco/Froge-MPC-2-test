"""Numerical couture geometry shared by Blender and offline geometry checks.

Metres, Z up, face towards -Y. No bpy, external files or model-supplied code.
Shells have real inner surfaces and stitched boundaries, not thickness labels.
"""
import math


def hair_lock_radii(samples, base=.00022, crown=.00115):
    """A smooth, bounded root-to-tip taper for surface-fitted updo locks."""
    if not 9 <= samples <= 80 or not .00015 <= base <= .0005 or not .0007 <= crown <= .0015:
        raise ValueError('Hair-lock taper outside supported range')
    return [base+(crown-base)*max(0.,math.sin(math.pi*i/(samples-1)))**.72
            for i in range(samples)]


def shell(front, faces, thickness):
    """Close an orientable surface by duplicating it along its local -Y normal.

Used for shallow crystalline panels; gown thickness is radial below.
    """
    n = len(front)
    vertices = [tuple(p) for p in front] + [(x, y + thickness, z) for x, y, z in front]
    result = [tuple(f) for f in faces] + [tuple(n + i for i in reversed(f)) for f in faces]
    edges = {}
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            if key in edges:
                del edges[key]
            else:
                edges[key] = (a, b)
    result += [(b, a, n + a, n + b) for a, b in edges.values()]
    volume=0.
    for face in result:
        a=vertices[face[0]]
        for j in range(1,len(face)-1):
            b,c=vertices[face[j]],vertices[face[j+1]]
            volume+=sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))
    if volume<0:result=[tuple(reversed(f)) for f in result]
    return vertices, result


def profile(z, hem=.30, width=1.):
    """One continuous fitted waist/bust/hip silhouette, independently of sleeves."""
    stations = [(0.025, hem, .23, 0), (.17, hem*.93, .205, 0),
                (.42, .225, .15, 0), (.65, .151, .101, 0),
                (.86, .168, .116, .005), (.99, .163, .108, 0),
                (1.10, .116, .077, 0), (1.19, .132, .092, -.008),
                (1.30, .166, .107, -.009), (1.39, .166, .080, 0),
                (1.45, .080, .057, .006)]
    z = max(stations[0][0], min(stations[-1][0], z))
    for a, b in zip(stations, stations[1:]):
        if a[0] <= z <= b[0]:
            t = (z-a[0])/(b[0]-a[0]); t = t*t*(3-2*t)
            values = [a[i]*(1-t)+b[i]*t for i in range(1,4)]
            return values[0]*width, values[1], values[2]
    raise ValueError('Invalid gown section')


def gown_point(z, angle, hem=.30, width=1., offset=.004):
    rx, ry, cy = profile(z, hem, width)
    # Fine cloth folds grow towards the hem; the fitted bodice stays thin.
    folds = max(0., (.85-z)/.825)*.010*math.cos(18*angle + .8*z)
    return ((rx+offset+folds)*math.cos(angle),
            cy+(ry+offset+folds*.6)*math.sin(angle), z)


def cape_point(t, u, hem=.30, width=1., side=False, offset=.004):
    """Authored hanging cloth with a curved cross-section, never a rear plane.

    The back is unobserved. Clearance is measured against the same gown
    envelope; folds vary in phase and width instead of identical corrugations.
    t runs shoulder to hem; u runs across the cloth, both in [0, 1].
    """
    if not 0 <= t <= 1 or not 0 <= u <= 1:
        raise ValueError('Cape coordinates outside the cloth')
    angle = (-.36 + .69*u) if side else (.30+(math.pi-.60)*u)
    top = 1.415 - .021*u if side else 1.414+.029*math.sin(math.pi*u)**2
    bottom = .075 + (.065*(1-u) if side else .085*abs(2*u-1)**1.7)
    z = top*(1-t)+bottom*t
    rx, ry, cy = profile(z, hem, width)
    # A loose cut hangs outside the waist while resting close to the shoulders.
    hang_x = .180*width*(1-t)+(hem+.028)*t
    hang_y = .108*(1-t)+.262*t
    wave = (.003+.009*t)*(.67*math.sin(11*angle+.55*t)+
                          .33*math.sin(19*angle-1.1*t))
    radius_x = max(rx+.024,hang_x)+wave
    yoke=min(1.,t/.16);yoke=yoke*yoke*(3-2*yoke)
    radius_y = (ry+offset+.004)*(1-yoke)+(max(ry+.026,hang_y)+wave*.7)*yoke
    x,y=radius_x*math.cos(angle),cy+radius_y*math.sin(angle)
    # Protect fold valleys at the widest allowed gown offset, including its
    # own folds. Uniform radial projection preserves the drape's cross-section.
    ratio=envelope_ratio((x,y,z),hem,width,offset+.005)
    if ratio<1:x,y=x/ratio,cy+(y-cy)/ratio
    return (x,y,z)


def cape_surface(hem=.30, width=1., side=False, rows=52, cols=65,offset=.004):
    vertices=[cape_point(j/(rows-1),k/(cols-1),hem,width,side,offset)
              for j in range(rows) for k in range(cols)]
    faces=[((j-1)*cols+k-1,j*cols+k-1,j*cols+k,(j-1)*cols+k)
           for j in range(1,rows) for k in range(1,cols)]
    return vertices,faces


def gown(hem=.30, width=1., offset=.004, thickness=.002, sides=96, rings=96):
    if not .001 <= thickness <= .006 or not .001 <= offset <= .018:
        raise ValueError('Garment clearance/thickness outside fitted range')
    vertices=[]
    for inner in (False, True):
        for j in range(rings):
            z=.025+1.425*j/(rings-1)
            for k in range(sides):
                vertices.append(gown_point(z, math.tau*k/sides, hem, width,
                                           offset-thickness if inner else offset))
    n=rings*sides; faces=[]
    for j in range(rings-1):
        for k in range(sides):
            a=j*sides+k; b=j*sides+(k+1)%sides
            face=(a,b,b+sides,a+sides)
            faces.append(face); faces.append(tuple(n+i for i in reversed(face)))
    for k in range(sides):
        a=k; b=(k+1)%sides
        faces.append((b,a,n+a,n+b))
        a=(rings-1)*sides+k; b=(rings-1)*sides+(k+1)%sides
        faces.append((a,b,n+b,n+a))
    return vertices,faces


def envelope_ratio(point, hem=.30, width=1., offset=.002):
    """Radial containment against the *same* folded surface used by the gown."""
    x,y,z=point;rx,ry,cy=profile(z,hem,width)
    angle=math.atan2((y-cy)/ry,x/rx)
    bx,by,_=gown_point(z,angle,hem,width,offset)
    boundary=math.hypot(bx,by-cy)
    return math.hypot(x,y-cy)/max(boundary,1e-9)


def contain_under_gown(point, hem=.30, width=1., offset=.004, thickness=.002):
    """Fit hidden anatomy inside the inner shell with 3 mm clearance.

    The exterior garment is never inflated to hide an intersecting body. Shoes
    and the visible neck are outside this operation's vertical interval.
    """
    x,y,z=point
    if not .10 <= z <= 1.45:return tuple(point)
    margin=offset-thickness-.003
    ratio=envelope_ratio(point,hem,width,margin)
    if ratio<=1:return tuple(point)
    cy=profile(z,hem,width)[2]
    return x/ratio,cy+(y-cy)/ratio,z


def shoulder_plate(side, thickness=.002):
    """Thin closed couture shard with crystal faces and metal edge walls."""
    if side not in (-1,1) or not .001<=thickness<=.006:
        raise ValueError('Invalid shoulder plate')
    front=[(side*.090,-.050,1.434),(side*.270,-.019,1.495),
           (side*.208,-.091,1.396),(side*.143,-.095,1.403)]
    vertices,faces=shell(front,[(0,1,3),(1,2,3)],thickness)
    # shell() writes two front faces, two reversed back faces, then boundary
    # walls. Crystal stays on the broad faces; only the thin rim is metallic.
    return vertices,faces,[0]*4+[1]*(len(faces)-4)


def garment_panels():
    """Shared surface coordinates for gemstones and their thin seam network."""
    for row,(bottom,top) in enumerate(((.065,.58),(.58,1.08),(1.10,1.43))):
        for col in range(12):
            lo=bottom+(.025*math.sin(col*2.3) if row else 0)
            hi=top+(.025*math.sin(col*2.3) if row==0 else 0)
            a=math.tau*col/12;b=a+math.tau/12*.985
            sweep=.26 if row<2 else -.24
            if row==2 and col>=6:
                # Front couture blades converge on the central waist jewel.
                # Previous near-parallel stripes erased the reference's V cut.
                centre=math.pi*1.5
                yield col,[(lo,centre+(a-centre)*.34),
                           (lo,centre+(b-centre)*.34),
                           (hi,b),(hi,a),
                           (lo+(hi-lo)*(.54+.06*math.sin(col)),
                            centre+((a+b)/2-centre)*.72)]
                continue
            yield col,[(lo,a),(lo,b),(hi,b+sweep),(hi,a+sweep),
                       (lo+(hi-lo)*(.46+.12*math.sin(col*1.7)),(a+b)/2+sweep*.5)]


def garment_seams(hem=.30,width=1.,offset=.004):
    """Couture piping follows the same curved surface as the inset panels."""
    paths=[]
    for col,corners in garment_panels():
        for a,b in [(corners[0],corners[3])]+[(corner,corners[4]) for corner in corners[:4]]:
            paths.append([gown_point(a[0]+(b[0]-a[0])*t/32,
                a[1]+(b[1]-a[1])*t/32,hem,width,offset+.0051) for t in range(33)])
    return paths


def garment_inlays(hem=.30,width=1.,offset=.004,subdivisions=20):
    """Tessellated jewel panels follow curvature between their corners.

    v19 projected only five vertices per panel; their long chords cut through
    the dress. Every new vertex is evaluated on the garment and each triangle
    is short enough to stay above the cloth, including bust/waist transitions.
    Metal is reserved for the separate edging, not one third of the fabric.
    """
    vertices=[];faces=[];slots=[]
    # Long, swept facets follow couture seams instead of a horizontal diamond
    # checkerboard. Alternate seam heights avoid mechanical horizontal bands.
    for col,corners in garment_panels():
        for facet in range(4):
            pa,pb,pc=corners[facet],corners[(facet+1)%4],corners[4]
            ids={}
            for i in range(subdivisions+1):
                for j in range(subdivisions+1-i):
                    u=i/subdivisions;v=j/subdivisions;w=1-u-v
                    z=pa[0]*w+pb[0]*u+pc[0]*v
                    angle=pa[1]*w+pb[1]*u+pc[1]*v
                    ids[i,j]=len(vertices)
                    vertices.append(gown_point(z,angle,hem,width,offset+.0040+.0020*v))
            for i in range(subdivisions):
                for j in range(subdivisions-i):
                    faces.append((ids[i,j],ids[i+1,j],ids[i,j+1]));slots.append((col+facet)%2)
                    if j<subdivisions-i-1:
                        faces.append((ids[i+1,j],ids[i+1,j+1],ids[i,j+1]));slots.append((col+facet)%2)
    return vertices,faces,slots


def fan(radius=.37, panels=12, spread=2.35, thickness=.0015):
    """Closed folded leaves with broad kite facets and a scalloped outer rim.

    Each leaf has a raised staggered spine; twelve large front triangles replace
    forty tiny facets. Adjacent leaves share the same radial edge positions.
    """
    vertices=[];faces=[];slots=[]
    for i in range(panels):
        a=-spread/2+spread*i/panels; b=a+spread/panels
        def point(r,angle,y):return (r*math.sin(angle),y,r*math.cos(angle))
        front=[];f=[]
        for row,(edge,spine,height) in enumerate(((.065,.065,.003),(.46,.31,.039),
                                                 (.76,.64,.070),(.970,1.025,.024))):
            for col,u in enumerate((0,.5,1)):
                front.append(point(radius*(spine if col==1 else edge),
                                   a+(b-a)*u,-radius*height if col==1 else 0))
            if row:
                start=(row-1)*3
                for col in range(2):
                    q=start+col
                    if col==0:f.extend(((q,q+1,q+4),(q,q+4,q+3)))
                    else:f.extend(((q,q+1,q+3),(q+1,q+4,q+3)))
        vv,ff=shell(front,f,thickness);start=len(vertices)
        vertices+=vv;faces.extend(tuple(start+v for v in face) for face in ff)
        # Jewel fabric dominates the fan. Silver belongs to its ribs and rotors.
        slots.extend(1 if index<len(f) else 0 for index in range(len(ff)))
    return vertices,faces,slots


def turbine_frame(inner_radius, outer_radius, depth=.005, sides=6):
    """Closed polygonal rim with a genuinely empty centre, local axis Y."""
    if not 0<inner_radius<outer_radius or depth<=0 or sides<3:
        raise ValueError('Invalid open turbine frame')
    vertices=[];faces=[]
    for y in (-depth/2,depth/2):
        for r in (inner_radius,outer_radius):
            for i in range(sides):
                a=math.tau*i/sides
                vertices.append((r*math.sin(a),y,r*math.cos(a)))
    n=sides
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)))
    return vertices,faces


def window_outline(radius, angle, half_span):
    return [(radius*r*math.sin(angle+da),radius*r*math.cos(angle+da))
            for r,da in ((.735,-half_span),(.735,half_span),(.973,half_span),(.992,0),(.973,-half_span))]


def fan_rotor_radius(radius, spread, count):
    """Fit the entire dark housing inside its sector, including sparse fans."""
    polygon=window_outline(radius,0,spread/(2*count));centre=(0,radius*.91)
    clearance=radius
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dz=b[0]-a[0],b[1]-a[1]
        clearance=min(clearance,abs(dx*(centre[1]-a[1])-dz*(centre[0]-a[0]))/math.hypot(dx,dz))
    return min(.025,radius*spread/count*.28,clearance*.98/1.24)


def window_surround(radius, angle, half_span, opening_radius, thickness=.002):
    """Solid crystal sector surrounding one hexagonal turbine opening.

    Both convex outlines are sampled on the same rays from the hole centre.
    Their annular strip closes every gap outside the frame without a Boolean,
    overlapping filler triangles or a cap across the opening.
    """
    centre=(radius*.91*math.sin(angle),radius*.91*math.cos(angle))
    outer=window_outline(radius,angle,half_span)
    inner=[(centre[0]+opening_radius*math.sin(math.tau*i/6),
            centre[1]+opening_radius*math.cos(math.tau*i/6)) for i in range(6)]
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    def boundary(polygon,direction):
        hits=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            edge=(b[0]-a[0],b[1]-a[1]);delta=(a[0]-centre[0],a[1]-centre[1])
            denominator=cross(direction,edge)
            if abs(denominator)<1e-12:continue
            distance=cross(delta,edge)/denominator;u=cross(delta,direction)/denominator
            if distance>1e-10 and -1e-8<=u<=1+1e-8:hits.append(distance)
        if not hits:raise ValueError('Turbine opening is outside its crystal sector')
        return min(hits)
    angles=sorted({round(math.atan2(z-centre[1],x-centre[0]),12) for x,z in outer+inner})
    front=[]
    for layer in range(3):
        t=layer/2
        for a in angles:
            direction=(math.cos(a),math.sin(a))
            lo,hi=boundary(inner,direction),boundary(outer,direction)
            if hi<=lo:raise ValueError('Turbine aperture overlaps the sector boundary')
            r=lo+(hi-lo)*t
            # The middle ridge is shallow genuine relief, not only a normal map.
            y=-.0035-.0022*math.sin(math.pi*t)*(.70+.30*math.sin(a*3+.4))
            front.append((centre[0]+r*direction[0],y,centre[1]+r*direction[1]))
    n=len(angles);faces=[]
    for layer in range(2):
        for i in range(n):
            j=(i+1)%n;a=layer*n+i;b=layer*n+j;c=(layer+1)*n+j;d=(layer+1)*n+i
            faces.extend(((a,b,c),(a,c,d)))
    return shell(front,faces,thickness)


def cut_jewel(outline,depth=.006):
    """Closed pointed gemstone with a raised central ridge, not an ellipsoid."""
    # outline is an ordered x/z silhouette. shell() orients the solid.
    centre=(sum(x for x,z in outline)/len(outline),-depth,sum(z for x,z in outline)/len(outline))
    front=[(x,0,z) for x,z in outline]+[centre]
    return shell(front,[(i,(i+1)%len(outline),len(outline)) for i in range(len(outline))],depth*.45)


def rotor(radius=.027, depth=.008, blades=5):
    """Closed hub and swept solid blades, local rotor axis Y."""
    vertices=[];faces=[];slots=[];segments=24
    for y in (-depth/2,depth/2):
        for i in range(segments):
            a=math.tau*i/segments
            vertices.append((radius*.23*math.cos(a),y,radius*.23*math.sin(a)))
    faces+=[tuple(range(segments)),tuple(reversed(range(segments,2*segments)))];slots+=[1,1]
    for i in range(segments):
        j=(i+1)%segments;faces.append((i,segments+i,segments+j,j));slots.append(1)
    for blade in range(blades):
        angle=math.tau*blade/blades
        front=[]
        # Rounded swept petals rather than six-corner paddle silhouettes.
        outline=[(.20+.77*math.sin(math.pi*t/2),-.17+.36*t-.09*math.sin(math.pi*t)) for t in (0,.2,.4,.6,.8,1)]
        outline+=[(.97-.77*t,.19+.31*math.sin(math.pi*t*.8)) for t in (.15,.3,.5,.7,.85,1)]
        for r,da in outline:
            a=angle+da;front.append((radius*r*math.cos(a),-depth*.26,radius*r*math.sin(a)))
        vv,ff=shell(front,[tuple(range(len(front)))],depth*.52);start=len(vertices)
        vertices+=vv;faces.extend(tuple(start+i for i in f) for f in ff);slots.extend([0]*len(ff))
    return vertices,faces,slots


def radial_positions(count,radius,start,arc,center=(0,0,0)):
    return [(center[0]+radius*math.sin(start+arc*i/(count-1)),center[1],
             center[2]+radius*math.cos(start+arc*i/(count-1))) for i in range(count)]
