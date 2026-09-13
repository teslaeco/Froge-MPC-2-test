"""R15 reference-guided anatomy, actual connected nasal boundary and real living eye."""
import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15'
head=bpy.data.objects['anatomical-head'];report={}
# Cache head surface before opening the living eye.
tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
bm=bmesh.new();bm.from_mesh(head.data);edges=set(e for e in bm.edges if e.is_boundary);components=[]
while edges:
 seed=edges.pop();group={seed};todo=[seed]
 while todo:
  e=todo.pop()
  for v in e.verts:
   for n in v.link_edges:
    if n in edges:edges.remove(n);group.add(n);todo.append(n)
 vs={v for e in group for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs)
 if .002<c.x<.018 and 1.48<c.z<1.52 and c.y<0:components.append((group,vs))
assert len(components)==1,len(components)
group,verts=components[0];assert all(sum(e in group for e in v.link_edges)==2 for v in verts)
start=min(verts,key=lambda v:v.co.z);ordered=[start];previous=None;current=start
while True:
 candidates=[e.other_vert(current) for e in current.link_edges if e in group and e.other_vert(current)!=previous]
 nxt=next(v for v in candidates if v!=start) if len(ordered)==1 else candidates[0]
 if nxt==start:break
 assert nxt not in ordered,'Non-simple boundary';ordered.append(nxt);previous,current=current,nxt
assert len(ordered)==len(verts)
a=np.array([v.co for v in ordered]);area=sum(a[i,0]*a[(i+1)%len(a),2]-a[(i+1)%len(a),0]*a[i,2] for i in range(len(a)))
if area<0:ordered=[ordered[0]]+list(reversed(ordered[1:]));a=np.array([v.co for v in ordered])
d=np.linalg.norm(np.roll(a[:,[0,2]],-1,axis=0)-a[:,[0,2]],axis=1);arc=np.r_[0,np.cumsum(d[:-1])]/d.sum();angles=-math.pi/2+arc*math.tau
mi=next(i for i,m in enumerate(head.data.materials) if m and m.name=='R13 observed skeletal face');ci=next(i for i,m in enumerate(head.data.materials) if m and m.name=='Cavity')
reg=json.loads((ROOT/'materials-r13/reference-registration.json').read_text());uv=bm.loops.layers.uv.verify();added=[]
def photo_uv(q):
 py=(1.8856-(q.z+.032))/.0006;seam=490-(py-240)*28/520;px=seam+q.x/.00064
 return ((px*reg['scale']+reg['translate_x'])/899,1-(py*reg['scale']+reg['translate_y'])/2048)
previous=ordered
for i in range(1,13):
 t=i/12;ring=[]
 for p,theta in zip(a,angles):
  inner=Vector((.0098+.0051*(.85-.15*math.sin(theta))*math.cos(theta),-.001,1.501+.016*math.sin(theta)))
  q=Vector(p).lerp(inner,t);q.y=float(p[1])+(inner.y-float(p[1]))*(t*t*(3-2*t));ring.append(bm.verts.new(q))
 for j in range(len(ring)):
  k=(j+1)%len(ring);f=bm.faces.new((previous[j],previous[k],ring[k],ring[j]));f.material_index=mi;f.smooth=True;added.append(f)
  for l in f.loops:l[uv].uv=photo_uv(l.vert.co)
 previous=ring
for i in range(1,9):
 t=i/8;ring=[bm.verts.new((.0098+.0051*(.85-.15*math.sin(theta))*math.cos(theta)*(1-.95*t),-.001+.044*t,1.501+.016*math.sin(theta)*(1-.95*t))) for theta in angles]
 for j in range(len(ring)):
  k=(j+1)%len(ring);f=bm.faces.new((previous[j],previous[k],ring[k],ring[j]));f.material_index=ci;f.smooth=True;added.append(f)
 previous=ring
f=bm.faces.new(tuple(reversed(previous)));f.material_index=ci;added.append(f);bmesh.ops.recalc_face_normals(bm,faces=added)
report['nasal_boundary_vertices']=len(ordered);report['nasal_boundary_connected_degree_two']=True;report['nasal_new_faces']=len(added)
# Almond opening for a spherical living eye, sampled against the original head surface.
cx=-.0587;cz=1.5485;halfwidth=.025
hit,_,_,_=tree.ray_cast(Vector((cx,-.5,cz)),Vector((0,1,0)));surface_y=hit.y if hit else -.018
remove=[]
for f in bm.faces:
 c=f.calc_center_median();q=(c.x-cx)/halfwidth
 if abs(q)<1 and c.y<surface_y+.015:
  shape=max(0,1-q*q)**.68;top=cz+.0083*shape+.001*q;bottom=cz-.0060*shape+.001*q
  if bottom<c.z<top:remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(head.data);bm.free();head.data.update();report['living_eye_aperture_faces_removed']=len(remove)
for name in ('anatomical-eye-r','Nasal_opening'):
 old=bpy.data.objects.get(name)
 if old:bpy.data.objects.remove(old,do_unlink=True)
def mat(name,rgb,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.32;return m
def sphere(name,loc,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
sclera=mat('R15 living sclera',(.57,.52,.43),.23);iris=mat('R15 brown iris fibres',(.12,.045,.009),.26);pupil=mat('R15 pupil',(.001,.001,.001),.13)
# Radial iris colour data; geometry still receives studio reflections.
N=512;y,x=np.mgrid[0:N,0:N].astype(np.float32);x=(x-N/2)/(N/2);y=(y-N/2)/(N/2);r=np.sqrt(x*x+y*y);theta=np.arctan2(y,x);fibres=.5+.18*np.sin(theta*173+np.sin(r*39))+.10*np.sin(theta*319-r*19);limbal=1-.65*np.clip((r-.76)/.22,0,1);p=np.ones((N,N,4),np.float32);p[:,:,:3]=np.array([.32,.17,.063])[None,None,:]*(.65+.55*fibres[:,:,None])*limbal[:,:,None]
im=bpy.data.images.new('R15 radial brown iris map',width=N,height=N,alpha=False);im.pixels.foreach_set(p.ravel());im.update();im.pack();tex=iris.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;iris.node_tree.links.new(tex.outputs['Color'],iris.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
center_y=.010;o=sphere('anatomical-eye-r',(cx,center_y,cz),(.024,.024,.024),sclera);o['anatomical_eye']=True;o['anatomical_side']='right'
# Spherical cap iris has planar radial UV; no stretched photographic eye panel.
vs=[];fs=[];uvs=[];steps=96;rings=16;ir=.0108
for i in range(rings+1):
 radius=ir*(i+.0001)/(rings+.0001)
 for j in range(steps):
  t=math.tau*j/steps;xx=radius*math.cos(t);zz=radius*math.sin(t);yy=center_y-math.sqrt(max(1e-9,.024**2-radius**2))-.00018;vs.append((cx+xx,yy,cz+zz));uvs.append((.5+xx/(2*ir),.5+zz/(2*ir)))
  if i:fs.append(((i-1)*steps+j,(i-1)*steps+(j+1)%steps,i*steps+(j+1)%steps,i*steps+j))
me=bpy.data.meshes.new('R15 iris surface');me.from_pydata(vs,[],fs);me.update();me.flip_normals();ob=bpy.data.objects.new('R15 living iris',me);bpy.context.collection.objects.link(ob);me.materials.append(iris);layer=me.uv_layers.new(name='IrisUV')
for f in me.polygons:
 f.use_smooth=True
 for li in f.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
sphere('R15 living pupil',(cx,center_y-.0246,cz),(.0043,.00045,.0043),pupil)
# Dark skeletal iris remains a real recessed object, reduced glossy appearance.
for name in ('R14 dark brown recessed iris','R14 shaded orbital sclera'):
 m=bpy.data.materials.get(name)
 if m:m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.40
# Local facial sculpt before global proportion adjustment.
for v in head.data.vertices:
 x,y,z=v.co
 if y<.045:
  if x<0:
   tip=math.exp(-((x+.015)/.014)**2-((z-1.496)/.019)**2);v.co.x+=.0013*tip;v.co.y+=.0012*tip
   smile=math.exp(-((x+.041)/.018)**2-((z-1.457)/.012)**2);v.co.z+=.0018*smile;v.co.y-=.0011*smile
  else:
   corner=math.exp(-((x-.057)/.024)**2-((z-1.452)/.020)**2);v.co.x-=.0055*corner;v.co.y-=.002*corner
head.data.update()
# Shared deformation preserves attached eye/teeth/hair relationships.
head_before=[];head_after=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 raw=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',raw);xyz=raw.reshape(-1,3);matr=np.array(ob.matrix_world);w=xyz@matr[:3,:3].T+matr[:3,3];old=w.copy();x,y,z=w.T
 # Less elongated upper cranium: maximum compression22mm, gradual above brow.
 q=np.clip((z-1.560)/.145,0,1);w[:,2]-=.022*q*q*(3-2*q)
 temple=np.exp(-((z-1.585)/.052)**2);w[:,0]*=1+.035*temple
 # Defined clothed bust, applied equally to dress/chest/seams, and shaped waist.
 if ob.name.startswith(('R9_tailored','R9_bodice','R9_neckline','R9_continuous','R10_upper_arm')):
  front=np.clip((.035-y)/.10,0,1);bust=np.exp(-((np.abs(x)-.09)/.055)**2-((z-1.196)/.062)**2)*front;w[:,1]-=.021*bust;w[:,2]+=.005*bust;waist=np.exp(-((z-1.035)/.068)**2);w[:,0]*=1-.045*waist
 # Very slight posture lean in frontal silhouette, shared across all parts.
 lean=np.clip((w[:,2]-1.1)/.55,0,1);w[:,0]+=.009*lean
 imat=np.array(ob.matrix_world.inverted());local=w@imat[:3,:3].T+imat[:3,3];ob.data.vertices.foreach_set('co',local.astype(np.float32).ravel());ob.data.update()
 if ob==head:head_before=[old.min(0).tolist(),old.max(0).tolist()];head_after=[w.min(0).tolist(),w.max(0).tolist()]
report.update(head_bounds_before=head_before,head_bounds_after=head_after,upper_cranium_max_compression=.022,temple_width_factor=1.035,bust_local_depth=.021,living_eye_surface_y=surface_y,living_eye_center_y=center_y,likeness_accepted=False)
(OUT/'anatomy-report.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stage-anatomy.blend'),compress=True);print('R15_ANATOMY_SAVED',json.dumps(report),flush=True)
