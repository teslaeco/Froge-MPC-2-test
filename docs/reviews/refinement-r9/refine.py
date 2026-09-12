"""R9 reference-directed shoulders, tailored gown, smile and rooted crown refinement."""
import bpy,math,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r9';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors

def mat(name,color,rough=.7):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;return m

def mesh(name,verts,faces,uvs,materials,indices=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 for m in materials:me.materials.append(m)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.use_smooth=True
  if indices:p.material_index=indices[p.index]
  for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
 return o

def tube(name,points,radius,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=radius;c.bevel_resolution=3
 s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
 return o

def lockhash():
 h=hashlib.sha256()
 for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  if o.type=='MESH' and o.name.startswith(('Reference_front_lock','Reference_back_lock')):
   h.update(o.name.encode());a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);h.update(a.tobytes())
 return h.hexdigest()
hair_before=lockhash()
# Narrow the actual human mouth opening by raising its lower boundary; UVs move with skin.
head=bpy.data.objects['anatomical-head']
for v in head.data.vertices:
 x,y,z=v.co
 if x<.003 and y<.025 and 1.447<z<1.488:
  w=math.exp(-((x+.024)/.035)**4)*math.exp(-((z-1.472)/.016)**2)*max(0,min(1,(.025-y)/.03))
  v.co.z+=.008*w;v.co.y-=.002*w
# More natural crown proportions and a restrained dental arch, seated in the mouth.
for o in bpy.context.scene.objects:
 if o.name.startswith('Anatomical_upper_tooth_'):
  side,j=map(int,o.name.rsplit('_',2)[1:]);o.location.y+=.002;o.location.z-=.001
  o.scale.z=1.18 if j<2 else 1.06;o.scale.x=1.04 if j<2 else .98
  o.rotation_euler.y=(.035 if j%2 else -.025)*side
 if o.name.startswith('Anatomical_lower_tooth_'):
  o.location.y+=.003;o.location.z+=.0025;o.scale.z=.86
# Recess the separate mandibular overlay so it does not read as a detached crescent.
mand=bpy.data.objects.get('Half_mandible')
if mand:
 for v in mand.data.vertices:v.co.y+=.008;v.co.x*=.93
# Geometry boundary relaxation of the nasal opening, with fixed far-field.
import bmesh
bm=bmesh.new();bm.from_mesh(head.data)
bound=[v for v in bm.verts if v.is_boundary and -.005<v.co.x<.025 and 1.503<v.co.z<1.557 and v.co.y<.055]
for _ in range(5):bmesh.ops.smooth_vert(bm,verts=bound,factor=.28,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(head.data);bm.free();head.data.update()
# Remove former stiff clothing/neck shell; retain material identity.
skin=bpy.data.objects['Living_neck_chest'].data.materials[0];bone=bpy.data.materials['Bone']
ivory=bpy.data.materials['Ivory'].copy();ivory.name='R9 woven ivory';black=bpy.data.materials['Black'].copy();black.name='R9 woven charcoal'
for name in ('Living_neck_chest','Skeletal_neck_chest','Ivory_gown','Black_gown','Ivory_sleeve','Black_sleeve'):
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
# Packed weave normal and albedo give portable fabric relief without shader-only noise.
N=1024;u=np.arange(N)[None,:]/N;v=np.arange(N)[:,None]/N
rng=np.random.default_rng(912)
f=.91+.035*np.sin(u*math.tau*193)*np.sin(v*math.tau*227)+.018*rng.standard_normal((N,N))
for material,color in ((ivory,(.68,.62,.46)),(black,(.022,.024,.020))):
 im=bpy.data.images.new(material.name+' woven base',width=N,height=N,alpha=False);a=np.ones((N,N,4),np.float32);a[:,:,:3]=np.clip(f[:,:,None]*np.array(color),0,1);im.pixels.foreach_set(a.ravel());im.update();im.pack()
 b=material.node_tree.nodes.get('Principled BSDF');b.inputs['Roughness'].default_value=.83
 for link in list(material.node_tree.links):
  if link.to_node==b and link.to_socket.name=='Base Color':material.node_tree.links.remove(link)
 t=material.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;material.node_tree.links.new(t.outputs['Color'],b.inputs['Base Color'])
# Smooth torso rings: continuous neck-to-trapezius slope and rounded deltoid region.
zkeys=[.93,1.08,1.19,1.25,1.29,1.31,1.335,1.36,1.40,1.445]
a=[.14,.15,.19,.213,.219,.198,.132,.069,.049,.050];bb=[.105,.116,.124,.115,.09,.075,.070,.066,.065,.066]
verts=[];faces=[];uvs=[];inds=[];rows=110;cols=160
for i in range(rows+1):
 z=.93+(1.445-.93)*i/rows;rx=np.interp(z,zkeys,a);ry=np.interp(z,zkeys,bb);cy=.025+.043*max(0,min(1,(z-1.28)/.12))
 for j in range(cols):
  t=math.tau*j/cols;x=rx*math.sin(t);y=cy-ry*math.cos(t)
  front=max(0,math.cos(t))**4
  y-=.004*math.exp(-((z-(1.306-.09*abs(x)))/.009)**2)*front*min(1,abs(x)/.035)
  y+=.003*math.exp(-(x/.018)**2-((z-1.318)/.016)**2)*front
  verts.append((x,y,z));uvs.append((j/cols,i/rows))
  if i:
   faces.append(((i-1)*cols+j,(i-1)*cols+(j+1)%cols,i*cols+(j+1)%cols,i*cols+j));inds.append(0 if math.sin(t)<0 else 1)
mesh('R9_continuous_shoulders_neck',verts,faces,uvs,[skin,bone],inds)
# Dress: fitted bodice, heart neckline, waist gathers and a flared pleated skirt.
def dress(t,s):
 front=max(0,math.cos(t));top=1.272-.110*(front**5)+.014*math.exp(-((abs(math.sin(t))-.62)/.23)**2)*front
 z=.60+(top-.60)*s
 rx=np.interp(z,[.60,.78,.94,1.03,1.10,1.18,1.27],[.265,.23,.177,.143,.145,.180,.213])
 ry=np.interp(z,[.60,.78,.94,1.03,1.10,1.18,1.27],[.173,.158,.127,.113,.12,.140,.125])
 pleat=(.0065*max(0,(1.035-z)/.435)**.65+.0015*math.exp(-((z-1.02)/.045)**2))*math.sin(t*30+.4*math.sin(t*7))
 x=(rx+pleat)*math.sin(t);y=.012-(ry+pleat)*math.cos(t)
 # Small fabric tension wrinkles close to waist, not heavy ridges across bust.
 y-=.0014*math.sin(85*z+9*t)*math.exp(-((z-1.03)/.075)**2)*front
 return x,y,z
verts=[];faces=[];uvs=[];inds=[];rows=150;cols=192
for i in range(rows+1):
 for j in range(cols):
  t=math.tau*j/cols;verts.append(dress(t,i/rows));uvs.append((j/cols,i/rows))
  if i:faces.append(((i-1)*cols+j,(i-1)*cols+(j+1)%cols,i*cols+(j+1)%cols,i*cols+j));inds.append(0 if math.sin(t)<0 else 1)
gown=mesh('R9_tailored_split_gown',verts,faces,uvs,[ivory,black],inds)
for side,material in ((-1,ivory),(1,black)):
 for angle in (.30,.67):
  points=[]
  for s in np.linspace(.59,.995,75):
   p=Vector(dress(side*angle,s));p.y-=.0014;points.append(p)
  tube('R9_bodice_seam_%s_%s'%(side,angle),points,.00065,material)
 tube('R9_neckline_%s'%side,[Vector(dress(side*t,1))+Vector((0,-.001,0)) for t in np.linspace(0,math.pi,120)],.0017,material)
 # A close-fitting upper sleeve, expanded cuff and gently gathered upper edge.
 verts=[];faces=[];uvs=[];nr=95;nc=80
 for i in range(nr+1):
  s=i/nr;z=.69+.57*s;cx=side*(.292-.087*s);cy=.027
  rx=np.interp(s,[0,.30,.56,.8,1],[.064,.044,.038,.048,.061]);ry=np.interp(s,[0,.3,.56,.8,1],[.063,.049,.043,.055,.075])
  for j in range(nc):
   t=math.tau*j/nc;fold=(.004*(1-s)**2+.0035*math.exp(-((s-.91)/.12)**2))*math.sin(t*12+3*s)
   zz=z+.007*math.cos(t)*(s**8)+.0016*math.sin(t*12)*(s**14)
   verts.append((cx+(rx+fold)*math.sin(t),cy-(ry+fold)*math.cos(t),zz));uvs.append((j/nc,s))
   if i:faces.append(((i-1)*nc+j,(i-1)*nc+(j+1)%nc,i*nc+(j+1)%nc,i*nc+j))
 sleeve=mesh('R9_gathered_sleeve_%s'%side,verts,faces,uvs,[material])
 tube('R9_sleeve_edge_%s'%side,verts[-nc:]+[verts[-nc]],.0018,material)
# Fill the formerly exposed cap with fine swept roots, retaining all accepted long locks.
cap=bpy.data.objects['Reference_fitted_scalp'];capmat=cap.data.materials[0].copy();capmat.name='R9 crown fine flow';cap.data.materials[0]=capmat
for n in capmat.node_tree.nodes:
 if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.10
bvh=BVHTree.FromPolygons([v.co for v in cap.data.vertices],[p.vertices[:] for p in cap.data.polygons])
for side in (-1,1):
 for j in range(32):
  pts=[]
  for t in np.linspace(0,1,38):
   # start at the middle part, sweep out toward temple with progressively lower roots
   x=side*(.0015+.110*t);z=1.731-.060*t-.034*t*t-.0020*j*(1-.46*t);q=Vector((x,-.035,z))
   hit,n,idx,dist=bvh.find_nearest(q)
   pts.append(hit+n*(.0013+.0012*math.sin(math.pi*t)))
  tube('R9_swept_root_%s_%02d'%(side,j),pts,.0010 if j%3 else .0014,capmat)
assert hair_before==lockhash()
# Pack and export the actual editable scene; never overwrite the accepted predecessor.
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.context.scene['repair_revision']='r9-shoulders-smile-tailoring';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r9.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r9.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r9.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report.update(triangles=tri,hair_preserved=True,long_lock_hash=hair_before,cap_modified=True,likeness_accepted=False,print_ready=False,changes=['continuous rounded shoulder/neck surface','tailored gown and sleeve geometry with seams, gathers and pleats','narrowed living mouth opening and adjusted tooth crowns','recessed mandibular overlay and relaxed nasal boundary','fine swept crown roots; all accepted long locks preserved'])
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R9_SAVED',tri,flush=True)
