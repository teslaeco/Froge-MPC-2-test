"""Continuous strand paths sampled from the fitted hair's own root-to-tip map."""
import bpy, math
import numpy as np
from mathutils import Vector

def wave(point):
 p=Vector(point)
 if p.z<1.73:
  t=max(0,min(1,(1.73-p.z)/.18));w=t*t*(3-2*t)
  p.x+=.009*math.sin((1.73-p.z)*28+math.atan2(p.x,p.y+.05)*2)*w
  p.y+=.009*math.sin((1.73-p.z)*34+abs(p.x)*19)*w
  p.z=1.73+(p.z-1.73)*.80
 return p

def add_locks(sample,mesh_object,supplied_material=None,curl=False):
 rng=np.random.default_rng(8432);palettes=[]
 for i,c in enumerate([(.145,.078,.029),(.215,.132,.056),(.27,.177,.083)]):
  if supplied_material is not None:
   palettes.append(supplied_material);continue
  m=bpy.data.materials.new('Blonde individual locks '+str(i));m.diffuse_color=(*c,1);m.use_nodes=True
  s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=.51;s.inputs['Specular IOR Level'].default_value=.13
  palettes.append(m)
 vertices=[];faces=[];uvs=[];groups=[]
 for lock in range(120):
  theta=-math.pi+2*math.pi*(lock+.35)/120;phase=rng.uniform(0,6.28)
  if abs(theta)<.55:continue
  chain=[];start=rng.uniform(.10,.21);end=rng.uniform(.90,1.00)
  steps=100 if curl else 50
  for j in range(steps+1):
   f=j/steps;s=start+(end-start)*f
   p=wave(sample(theta+.012*math.sin(f*7+phase)*f,s))
   if curl:
    amount=.014*math.sin(math.pi*f)**.5
    p.x+=amount*math.cos(f*37+phase);p.y+=amount*math.sin(f*37+phase)
   normal=Vector((math.sin(theta),-math.cos(theta),max(0,(p.z-1.70)*8))).normalized()
   p+=normal*(.00025+.00065*math.sin(math.pi*f)**.6)
   chain.append(p)
  base=len(vertices);sides=6;width=rng.uniform(.0024,.0046) if curl else rng.uniform(.00035,.00090)
  for j,p in enumerate(chain):
   tangent=(chain[min(j+1,steps)]-chain[max(j-1,0)]).normalized()
   normal=Vector((math.sin(theta),-math.cos(theta),max(0,(p.z-1.70)*8))).normalized()
   a=tangent.cross(normal).normalized();b=tangent.cross(a).normalized();f=j/steps
   taper=(.12+.88*math.sin(math.pi*f)**.4)*(1-.96*f**8)
   for k in range(sides):
    angle=k*2*math.pi/sides
    thickness=width*.4 if curl else .00028
    vertices.append(tuple(p+a*math.cos(angle)*width*taper+b*math.sin(angle)*thickness*taper));uvs.append((k/sides,1-f))
   if j:
    for k in range(sides):faces.append((base+(j-1)*sides+k,base+j*sides+k,base+j*sides+(k+1)%sides,base+(j-1)*sides+(k+1)%sides));groups.append(lock%3)
 obj=mesh_object('Anatomical individual wavy locks',vertices,faces,palettes[0])
 for m in palettes[1:]:obj.data.materials.append(m)
 layer=obj.data.uv_layers.new(name='HairFlow')
 for p,g in zip(obj.data.polygons,groups):
  p.material_index=g;p.use_smooth=True
  for li in p.loop_indices:layer.data[li].uv=uvs[obj.data.loops[li].vertex_index]
 from portrait_hair_surface import add_strand_normal
 add_strand_normal(obj,palettes)
 return [obj]
