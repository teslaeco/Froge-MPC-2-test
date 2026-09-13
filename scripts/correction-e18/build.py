import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path('/workspace/scratch/584c9d97a5a1/correction-e18');report={'base':'E17','head_global_scale_unchanged':True,'likeness_accepted':False}
head=bpy.data.objects['anatomical-head'];cx=.0423;cz=1.5522
# Local orbital warp: upper arch flatter, outer lower corner wider; compact support leaves living half intact.
def orbital(w):
 x,y,z=w;u=(x-cx)/.038;v=(z-cz)/.034;r=math.hypot(u,v)
 if x<.001 or y>.09 or r>1.72 or r<.05:return w
 a=math.atan2(v,u);co=math.cos(a);si=math.sin(a)
 uu=math.copysign(abs(co)**.80,co);vv=math.copysign(abs(si)**.88,si)
 # gently sloping orbital roof and lower lateral corner
 tx=cx+.039*r*uu;tz=cz+.031*r*vv+.003*r*co
 weight=1 if r<=1.10 else max(0,1-(r-1.10)/.62);weight*=min(1,x/.009)
 return Vector((x+(tx-x)*weight,y,z+(tz-z)*weight))
count=0
for ob in [head,bpy.data.objects['Recessed_empty_orbit']]:
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;q=orbital(w)
  if (q-w).length>1e-9:v.co=inv@q;count+=1
 ob.data.update()
report['orbital_vertices_reshaped']=count
# Recess all eye components as one assembly; remain present as requested, with dark natural catchlight.
center=Vector((cx,.045,cz))
for name in ['anatomical-eye-l','R14 recessed brown iris','R14 recessed pupil']:
 ob=bpy.data.objects[name];inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  q=ob.matrix_world@v.co;q=center+(q-center)*.72;q.y+=.014;v.co=inv@q
 ob.data.update()
 for m in ob.data.materials:
  if m and m.use_nodes:
   b=m.node_tree.nodes.get('Principled BSDF')
   if b:
    c=b.inputs['Base Color'].default_value;b.inputs['Base Color'].default_value=(c[0]*.30,c[1]*.30,c[2]*.30,1);b.inputs['Roughness'].default_value=.42
report['skeletal_eye_scale']=.72;report['skeletal_eye_recess']=.014
# Carve zygomatic hollow, retain a thin cheek crest, articulate jaw rather than widening skull.
changed=0
for v in head.data.vertices:
 x,y,z=v.co
 if x>.003 and y<.075:
  front=max(0,min(1,(.075-y)/.10));side=min(1,x/.025)
  hollow=math.exp(-((x-.063)/.024)**2-((z-1.487)/.026)**2)
  crest=math.exp(-((x-.062)/.029)**2-((z-(1.522-.13*(x-.055)))/.0075)**2)
  jaw=math.exp(-((x-.067)/.026)**2-((z-1.414)/.025)**2)
  v.co.y+=front*side*(.017*hollow-.0075*crest+.004*jaw);changed+=1
head.data.update();report['cheek_jaw_vertices_sculpted']=changed
# Calm the ragged skeletal mouth opening and its protruding cavity insert.
bm=bmesh.new();bm.from_mesh(head.data);boundary=[v for v in bm.verts if any(e.is_boundary for e in v.link_edges) and .012<v.co.x<.085 and 1.426<v.co.z<1.480 and v.co.y<.065]
patch=set(boundary)
for _ in range(5):patch|={e.other_vert(v) for v in list(patch) for e in v.link_edges}
for _ in range(35):bmesh.ops.smooth_vert(bm,verts=list(patch),factor=.45,use_axis_x=True,use_axis_y=True,use_axis_z=True)
for v in patch:
 x,y,z=v.co
 if x>.020:
  t=min(1,(x-.020)/.035);v.co.z=1.455+(z-1.455)*(1-.32*t)
# Bring the mandibular gum margin close beneath the lower dental arch.
for v in bm.verts:
 x,y,z=v.co
 if .003<x<.068 and y<.055 and 1.423<z<1.453:
  w=math.exp(-((z-1.439)/.014)**2)*math.exp(-((x-.030)/.035)**2);v.co.z+=.007*w
# Relax high-frequency creases around the lower nasal transition without changing cranial scale.
nasal=[v for v in bm.verts if -.001<v.co.x<.024 and 1.476<v.co.z<1.531 and v.co.y<.018]
for _ in range(18):bmesh.ops.smooth_vert(bm,verts=nasal,factor=.40,use_axis_x=True,use_axis_y=True,use_axis_z=True)
report['nasal_vertices_relaxed']=len(nasal)
bm.to_mesh(head.data);bm.free();head.data.update();report['mouth_boundary_vertices_relaxed']=len(boundary)
cavity=bpy.data.objects['Recessed oral cavity']
for v in cavity.data.vertices:
 v.co.y+=.018;v.co.z=1.454+(v.co.z-1.454)*.64
cavity.data.update();report['oral_cavity_recess']=.018
# Follow the dental arch: recess outer crowns progressively, lift canine tips toward corners.
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith('Anatomical_'):continue
 inv=ob.matrix_world.inverted();center=sum((ob.matrix_world@v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);side=max(0,min(1,(center.x-.012)/.027))
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co
  if center.x>0:w.y+=.002+.004*side;w.z+=.0015*side if 'upper' in ob.name else .0005*side
  v.co=inv@w
 ob.data.update()
# Surface-conforming frontal hairs: use ray hits at prescribed X/Z, not nearest-point projection.
cap=bpy.data.objects['R12_asymmetric_scalp'];tree=BVHTree.FromPolygons([cap.matrix_world@v.co for v in cap.data.vertices],[p.vertices[:] for p in cap.data.polygons])
V=[];F=[];MI=[];UV=[];strands=0
mats=[bpy.data.materials['E17 chestnut '+str(i)] for i in range(6)]+[bpy.data.materials['E17 aged silver '+str(i)] for i in range(6)]
def tube(ps,mi):
 global strands
 if len(ps)<5:return
 start=len(V);n=len(ps)
 for i,p in enumerate(ps):
  t=(ps[min(i+1,n-1)]-ps[max(i-1,0)]).normalized();a=t.cross(Vector((0,1,0))).normalized();b=t.cross(a).normalized();r=.00031*(1-.65*(i/(n-1))**8)
  for j in range(6):V.append(tuple(p+r*(a*math.cos(j*math.tau/6)+b*math.sin(j*math.tau/6))));UV.append((j/6,i/(n-1)))
  if i:
   for j in range(6):F.append((start+(i-1)*6+j,start+(i-1)*6+(j+1)%6,start+i*6+(j+1)%6,start+i*6+j));MI.append(mi)
 F.append(tuple(start+j for j in reversed(range(6))));MI.append(mi);F.append(tuple(start+(n-1)*6+j for j in range(6)));MI.append(mi);strands+=1
for side,sgn in [(0,-1),(1,1)]:
 for row in range(220):
  a=row/219;ps=[]
  for k in range(100):
   t=k/99;x=sgn*(.0007+.123*t);z=1.646+.061*a-(.039+.052*a)*t**1.65
   q,no,_,d=tree.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.5)
   if q is not None:q.y-=.00065;ps.append(q)
  tube(ps,side*6+row%6)
mesh=bpy.data.meshes.new('E18 frontal scalp hair geometry');mesh.from_pydata(V,[],F);mesh.update();ob=bpy.data.objects.new('E18 swept frontal individual hair',mesh);bpy.context.collection.objects.link(ob)
for m in mats:mesh.materials.append(m)
uv=mesh.uv_layers.new(name='Strand UV')
for p,mi in zip(mesh.polygons,MI):
 p.use_smooth=True;p.material_index=mi
 for li in p.loop_indices:uv.data[li].uv=UV[mesh.loops[li].vertex_index]
report['ray_fitted_hairline_strands']=strands
# Preview save before export: no claim of final likeness until clay and textured inspection.
tri=0
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report['triangles']=tri;(P/'build-report.json').write_text(json.dumps(report,indent=2));bpy.context.scene['repair_revision']='E18-local-orbit-cheek-mouth-hairline';bpy.ops.wm.save_as_mainfile(filepath=str(P/'FORGE-model-E18.blend'),compress=True);print(report,flush=True)
