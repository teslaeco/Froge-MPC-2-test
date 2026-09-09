"""Numerical couture geometry shared by Blender and offline geometry checks.

Metres, Z up, face towards -Y. No bpy, external files or model-supplied code.
Shells have real inner surfaces and stitched boundaries, not thickness labels.
"""
import math


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


def fan(radius=.37, panels=12, spread=2.35, thickness=.0015):
    """Folded solid fan; each radial sector has four faceted triangles."""
    vertices=[];faces=[];slots=[]
    for i in range(panels):
        a=-spread/2+spread*i/panels; b=a+spread/panels
        def point(r,angle,y):return (r*math.sin(angle),y,r*math.cos(angle))
        front=[point(.025,a,0),point(radius,a,0),
               point(radius*.985,(a+b)/2,-radius*.036),
               point(radius,b,0),point(.025,b,0),
               point(radius*.55,(a+b)/2,-radius*.022)]
        f=[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)]
        vv,ff=shell(front,f,thickness);start=len(vertices)
        vertices+=vv;faces.extend(tuple(start+v for v in face) for face in ff)
        slots.extend((i+index)%3 for index in range(len(ff)))
    return vertices,faces,slots


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
        for r,da in ((.18,-.18),(.74,-.15),(1.,.15),(.91,.42),(.43,.46),(.18,.15)):
            a=angle+da;front.append((radius*r*math.cos(a),-depth*.26,radius*r*math.sin(a)))
        vv,ff=shell(front,[tuple(range(6))],depth*.52);start=len(vertices)
        vertices+=vv;faces.extend(tuple(start+i for i in f) for f in ff);slots.extend([0]*len(ff))
    return vertices,faces,slots


def radial_positions(count,radius,start,arc,center=(0,0,0)):
    return [(center[0]+radius*math.sin(start+arc*i/(count-1)),center[1],
             center[2]+radius*math.cos(start+arc*i/(count-1))) for i in range(count)]
