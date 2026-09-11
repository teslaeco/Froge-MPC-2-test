"""Bounded, data-only freeform surfaces. No learned reconstruction is claimed."""
import math


def curve(points, samples, closed=False):
    """Interpolating Catmull-Rom with coordinate bounds to limit overshoot."""
    n=len(points);result=[]
    def at(i):return points[i%n] if closed else points[max(0,min(n-1,i))]
    for i in range(n if closed else n-1):
        a,b,c,d=(at(i+j) for j in (-1,0,1,2))
        for step in range(samples):
            t=step/samples
            v=[.5*((2*b[k])+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+
                (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in range(3)]
            result.append(tuple(max(min(b[k],c[k]),min(max(b[k],c[k]),v[k])) for k in range(3)))
    if not closed:result.append(tuple(points[-1]))
    return result


def dimensions(p):
    s=p['samples']
    if p['kind']=='surface_grid':
        rows,cols=len(p['control_grid']),len(p['control_grid'][0])
        if any(len(row)!=cols for row in p['control_grid']):raise ValueError('Siatka kontrolna musi byc prostokatna.')
        h,w=(rows-1)*s+1,(cols-1)*s+1
        double=p['thickness']>0
        return h*w*(2 if double else 1),2*(h-1)*(w-1)*(2 if double else 1)+(4*(h+w-2) if double else 0)
    rings=p['rings'];n=len(rings[0])
    if any(len(r)!=n for r in rings):raise ValueError('Przekroje musza miec te sama liczbe punktow.')
    if any(a==b for a,b in zip(rings,rings[1:])):raise ValueError('Kolejne przekroje nie moga byc identyczne.')
    if any(any(a==b for a,b in zip(r,r[1:]+r[:1])) for r in rings):raise ValueError('Przekroj zawiera powtorzony punkt.')
    h,w=(len(rings)-1)*s+1,n*s
    return h*w,2*(h-1)*w+(2*(w-2) if p['caps'] else 0)


def geometry(p):
    dimensions(p)
    grid=p['control_grid'] if p['kind']=='surface_grid' else p['rings']
    closed=p['kind']=='contour_loft';s=p['samples']
    rows=[curve(row,s,closed) for row in grid]
    columns=[curve([row[j] for row in rows],s) for j in range(len(rows[0]))]
    h,w=len(columns[0]),len(columns)
    vertices=[columns[j][i] for i in range(h) for j in range(w)]
    faces=[]
    for i in range(h-1):
        for j in range(w if closed else w-1):
            nxt=(j+1)%w
            faces.append((i*w+j,i*w+nxt,(i+1)*w+nxt,(i+1)*w+j))
    if closed:
        if p['caps']:faces += [tuple(reversed(range(w))),tuple((h-1)*w+j for j in range(w))]
    elif p['thickness']:
        normals=[[0.,0.,0.] for _ in vertices]
        for face in faces:
            a,b,c=(vertices[j] for j in face[:3]);u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            n=[u[(k+1)%3]*v[(k+2)%3]-u[(k+2)%3]*v[(k+1)%3] for k in range(3)]
            for j in face:
                for k in range(3):normals[j][k]+=n[k]
        count=len(vertices);opposite=[]
        for point,normal in zip(vertices,normals):
            size=math.sqrt(sum(x*x for x in normal))
            if size<1e-12:raise ValueError('Powierzchnia ma zerowe pole lub odwracajace sie przekroje.')
            opposite.append(tuple(point[k]-p['thickness']*normal[k]/size for k in range(3)))
        vertices+=opposite
        faces += [tuple(j+count for j in reversed(f)) for f in list(faces)]
        border=list(range(w))+[i*w+w-1 for i in range(1,h)]+[(h-1)*w+j for j in range(w-2,-1,-1)]+[i*w for i in range(h-2,0,-1)]
        for a,b in zip(border,border[1:]+border[:1]):faces.append((a,a+count,b+count,b))
    if any(not all(math.isfinite(x) for x in v) for v in vertices):raise ValueError('Nieprawidlowa geometria powierzchni.')
    return vertices,faces,(h,w)


def build(p, material, mesh_object):
    import bmesh
    vertices,faces,(h,w)=geometry(p)
    obj=mesh_object(p['name'],vertices,faces,material)
    bm=bmesh.new()
    try:
        bm.from_mesh(obj.data)
        if any(f.calc_area()<1e-14 for f in bm.faces):raise ValueError('Powierzchnia ma sciany o zerowym polu.')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data)
    finally:bm.free()
    uv=obj.data.uv_layers.new(name='SurfaceUV')
    closed=p['kind']=='contour_loft'
    for face in obj.data.polygons:
        indices=[obj.data.loops[i].vertex_index%(h*w) for i in face.loop_indices]
        seam=closed and any(j%w==0 for j in indices) and any(j%w==w-1 for j in indices)
        for loop,j in zip(face.loop_indices,indices):
            u=1. if seam and j%w==0 else (j%w)/(w if closed else w-1)
            uv.data[loop].uv=(u,(j//w)/(h-1))
        face.use_smooth=True
    obj['geometry_method']=p['kind'];obj['geometry_from_image_measurements_verified']=False
    return obj
