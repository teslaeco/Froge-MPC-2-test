"""E17: actual strand geometry, split-age hair palette, crown coverage and tooth refinement."""
import bpy,bmesh,math,json,sys,random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path('/workspace/scratch/584c9d97a5a1/correction-e17');sys.path.insert(0,str(P.parent/'correction-e16/runtime'))
from scene_exports import _portable_images,_portable_uvs
rng=random.Random(17017);report={'base':'E16','head_global_scale_unchanged':True,'likeness_accepted':False,'age_split_is_user_art_direction':True}
def material(name,color,rough=.49):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=.28
 return m
mats=[]
for side in range(2):
 for j in range(6):
  f=.7+j*.11;c=(.045*f,.022*f,.011*f) if side==0 else (.19*f,.185*f,.17*f)
  mats.append(material(('E17 chestnut ' if side==0 else 'E17 aged silver ')+str(j),c,.48 if side==0 else .56))
# Mesh batches keep FBX editable without thousands of scene objects.
V=[];F=[];M=[];UV=[];strands=0
def tube(points,radii,mi,sides=6):
 global strands
 if len(points)<2:return
 start=len(V);oldn=None
 for i,p in enumerate(points):
  t=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();n=t.cross(Vector((0,1,0)))
  if n.length<.01:n=t.cross(Vector((1,0,0)))
  n.normalize();b=t.cross(n).normalized()
  for j in range(sides):
   a=math.tau*j/sides;V.append(tuple(p+float(radii[i])*(math.cos(a)*n+math.sin(a)*b)));UV.append((j/sides,i/(len(points)-1)))
  if i:
   for j in range(sides):F.append((start+(i-1)*sides+j,start+(i-1)*sides+(j+1)%sides,start+i*sides+(j+1)%sides,start+i*sides+j));M.append(mi)
 F.append(tuple(start+j for j in reversed(range(sides))));M.append(mi);F.append(tuple(start+(len(points)-1)*sides+j for j in range(sides)));M.append(mi);strands+=1
hair=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('R11_Reference')]
for oi,o in enumerate(hair):
 a=np.array([o.matrix_world@v.co for v in o.data.vertices]);assert len(a)%8==0
 a=a.reshape(-1,8,3);cent=a.mean(1);rad=np.linalg.norm(a-cent[:,None,:],axis=2).mean(1);side=0 if cent[:,0].mean()<0 else 1
 # Keep a slimmer inner lock; strand ribbons fill its edge with actual fine fibers.
 for j,row in enumerate(a):
  for k,c in enumerate(row):o.data.vertices[j*8+k].co=o.matrix_world.inverted()@Vector(tuple(cent[j]+(c-cent[j])*.50))
 o.data.materials.clear();o.data.materials.append(mats[side*6+1]);o.data.update()
 for f in range(10):
  phase=math.tau*f/10+rng.uniform(-.08,.08);points=[];radii=[]
  for i,c in enumerate(cent):
   t=i/(len(cent)-1);tangent=Vector(tuple(cent[min(i+1,len(cent)-1)]-cent[max(0,i-1)])).normalized();n=tangent.cross(Vector((0,1,0)))
   if n.length<.01:n=tangent.cross(Vector((1,0,0)))
   n.normalize();b=tangent.cross(n).normalized();spread=float(rad[i])*(.40+.10*math.sin(t*8+phase));angle=phase+.12*math.sin(t*12+oi)
   points.append(Vector(tuple(c))+spread*(math.cos(angle)*n+math.sin(angle)*b));radii.append(max(.000055,min(.00038,rad[i]*.14))*(1-.8*t**7))
  tube(points,radii,side*6+rng.randrange(6))
report['existing_locks_slimmed']=len(hair);report['fine_length_strands']=strands
# Hairline coverage: close-spaced strands laid directly over the existing scalp, from central part to temple/back.
cap=bpy.data.objects['R12_asymmetric_scalp'];capverts=[cap.matrix_world@v.co for v in cap.data.vertices];tree=BVHTree.FromPolygons(capverts,[p.vertices[:] for p in cap.data.polygons])
cap.data.materials.clear();cap.data.materials.append(mats[1]);cap.data.materials.append(mats[7])
for p in cap.data.polygons:p.material_index=0 if p.center.x<0 else 1
roots=0
for side,sgn in [(0,-1),(1,1)]:
 for j in range(240):
  yy=-.019+j/239*.195;points=[];radii=[]
  for k in range(45):
   t=k/44;x=sgn*(.0005+.123*t);z=1.704-.125*t*t-.32*(yy-.075)**2;y=yy-.018*math.sin(math.pi*t)
   q,no,_,_=tree.find_nearest(Vector((x,y,z)))
   if q is None:continue
   outward=(q-Vector((0,.075,1.55))).normalized();q+=outward*(.0010+.0003*math.sin(j*1.7+t*4));points.append(q);radii.append(.00055*(1-.65*t**9))
  tube(points,radii,side*6+rng.randrange(6));roots+=1
# Dense temple-swept baby-hair rows cover the lower frontal scalp wedge.
for side,sgn in [(0,-1),(1,1)]:
 for j in range(160):
  a=j/159;points=[];radii=[]
  for k in range(45):
   t=k/44;x=sgn*(.0006+.120*t);z=(1.651+.052*a)-(.050+.025*a)*t**1.35
   q,no,_,_=tree.find_nearest(Vector((x,-.085,z)))
   if q is None:continue
   q+=Vector((0,-.0011,0));points.append(q);radii.append(.00034*(1-.7*t**10))
  tube(points,radii,side*6+rng.randrange(6));roots+=1
# Old root ribbons caused blunt cut ends over forehead; replace them with the above fibers.
oldroots=[o for o in bpy.context.scene.objects if o.name.startswith('R12_root')]
for o in oldroots:bpy.data.objects.remove(o,do_unlink=True)
mesh=bpy.data.meshes.new('E17 longitudinal strand mesh');mesh.from_pydata(V,[],F);mesh.update();o=bpy.data.objects.new('E17 individual hair fibers and swept hairline',mesh);bpy.context.collection.objects.link(o)
for m in mats:mesh.materials.append(m)
uv=mesh.uv_layers.new(name='Strand UV')
for p,mi in zip(mesh.polygons,M):
 p.material_index=mi;p.use_smooth=True
 for li in p.loop_indices:uv.data[li].uv=UV[mesh.loops[li].vertex_index]
report['hairline_strands']=roots;report['total_new_strands']=strands;report['removed_blunt_root_ribbons']=len(oldroots)
# Enamel: reduce flat rectangular appearance with tapered cervical thirds and restrained edge variation.
teeth=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.name.startswith('Anatomical_'):continue
 coords=np.array([v.co for v in o.data.vertices]);lo=coords.min(0);hi=coords.max(0);c=(lo+hi)/2;h=max(hi[2]-lo[2],1e-6)
 for v in o.data.vertices:
  t=(v.co.z-lo[2])/h;dx=v.co.x-c[0];dy=v.co.y-c[1]
  v.co.x=c[0]+dx*(1.025-.10*t*t);v.co.y=c[1]+dy*.82+.0011
  if 'upper' in o.name:v.co.z+=.00065*(1-t)**3*(abs(dx)/max((hi[0]-lo[0])/2,1e-6))**2
  else:v.co.z-=.00035*t**3
 o.data.update();teeth.append(o.name)
for m in bpy.data.materials:
 if 'enamel' in m.name.lower() and m.use_nodes:
  b=m.node_tree.nodes.get('Principled BSDF')
  if b:b.inputs['Base Color'].default_value=(.55,.47,.33,1);b.inputs['Roughness'].default_value=.32
report['tooth_crowns_refined']=len(teeth)
# Physically small skin relief for Blender master; clear export limitation recorded below.
for m in bpy.data.materials:
 if m.use_nodes and (m.name.startswith('R11 warm skin') or m.name=='R13 observed living face'):
  nt=m.node_tree;b=nt.nodes.get('Principled BSDF')
  if not b:continue
  tex=nt.nodes.new('ShaderNodeTexNoise');tex.name='E17 fine skin pores';tex.inputs['Scale'].default_value=620;tex.inputs['Detail'].default_value=2
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00012;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],b.inputs['Normal'])
report['procedural_skin_pores']='Blender master only; FBX/GLB procedural normal not claimed portable'
# Anatomical contour cues: subtle collarbones and underbust shaping, no global inflation.
count=0
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.name.startswith(('R9_continuous','R9_tailored','R9_bodice','R9_neckline')):continue
 for v in o.data.vertices:
  x,y,z=v.co;front=max(0,min(1,(.02-y)/.10))
  if o.name.startswith('R9_continuous'):
   collar=math.exp(-((z-(1.300-.17*abs(x)))/.009)**2)*math.exp(-((abs(x)-.072)/.08)**2);v.co.y-=.0015*front*collar
  else:
   fullness=math.exp(-((abs(x)-.092)/.061)**2-((z-1.18)/.061)**2);under=math.exp(-((z-1.095)/.022)**2)*math.exp(-((abs(x)-.081)/.067)**2);v.co.y+=front*(.004*under-.005*fullness)
  count+=1
 o.data.update()
report['torso_vertices_processed']=count
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report['triangles']=tri;bpy.context.scene['repair_revision']='E17-strand-hair-anatomical-detail'
(P/'build-report.json').write_text(json.dumps(report,indent=2));print('E17_GEOMETRY_READY',report,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'FORGE-model-E17.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(P/'FORGE-model-E17.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
portable={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,portable),_portable_images(bpy,P,portable):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(P/'FORGE-model-E17.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report['portable']=portable;(P/'build-report.json').write_text(json.dumps(report,indent=2));print('E17_EXPORTED',tri,flush=True)
