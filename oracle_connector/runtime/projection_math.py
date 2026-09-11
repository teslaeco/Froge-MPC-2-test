"""Camera and image-mask mathematics, independent of Blender and credentials."""
import math


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return tuple(a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3] for i in range(3))
def unit(v):
    length=math.sqrt(dot(v,v))
    if length<1e-8:raise ValueError('Kamera wymaga roznych punktow i poprzecznego kierunku gory.')
    return tuple(x/length for x in v)


def camera_basis(view):
    forward=unit(sub(view['target'],view['position']))
    right=unit(cross(forward,view['up']))
    return forward,right,cross(right,forward)


def project(point,view,aspect,basis=None):
    forward,right,up=basis or camera_basis(view)
    offset=sub(point,view['position']);depth=dot(offset,forward)
    if depth<=1e-7:return None
    span=view['vertical_span'] if view['projection']=='orthographic' else 2*depth*math.tan(view['fov']/2)
    return (.5+dot(offset,right)/(span*aspect),.5-dot(offset,up)/span,depth)


def inside(point,polygon):
    x,y=point;odd=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        if abs((x-a[0])*dy-(y-a[1])*dx)<1e-10 and min(a[0],b[0])-1e-10<=x<=max(a[0],b[0])+1e-10 and min(a[1],b[1])-1e-10<=y<=max(a[1],b[1])+1e-10:return True
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:odd=not odd
    return odd
