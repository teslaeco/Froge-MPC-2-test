"""R11: authored UV PBR data maps and thinner grouped hair volumes from R10 guides."""
import bpy,math,json,sys,hashlib,gc
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r11'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
N=2048;u=np.arange(N,dtype=np.float32)[None,:]/N;v=np.arange(N,dtype=np.float32)[:,None]/N
rng=np.random.default_rng(20260912)
def smooth(a,n=3):
 for _ in range(n):a=(a+np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1))*.2
 return a
fine=rng.standard_normal((N,N),dtype=np.float32);cloud=smooth(fine,14);cloud/=max(.01,float(cloud.std()))
large=(np.sin(u*math.tau*7+np.sin(v*21))*np.cos(v*math.tau*9+np.sin(u*33))).astype(np.float32)
texture_names=[]
def img(name,data,noncolor=False):
 im=bpy.data.images.new(name,width=N,height=N,alpha=False);im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
 a=np.ones((N,N,4),np.float32)
 if data.ndim==2:a[:,:,:3]=data[:,:,None]
 else:a[:,:,:3]=data
 im.pixels.foreach_set(a.ravel());im.update();im.pack();texture_names.append(name);return im

def normal(name,height,strength):
 dx=(np.roll(height,-1,1)-np.roll(height,1,1))*strength;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*strength
 z=np.ones_like(dx);l=np.sqrt(dx*dx+dy*dy+1);return img(name,np.stack((-dx/l*.5+.5,-dy/l*.5+.5,z/l*.5+.5),axis=2),True)

def link(m,image,socket):
 bs=m.node_tree.nodes.get('Principled BSDF')
 for l in list(m.node_tree.links):
  if l.to_node==bs and l.to_socket.name==socket:m.node_tree.links.remove(l)
 t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=image
 if socket=='Normal':
  node=m.node_tree.nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.6;m.node_tree.links.new(t.outputs['Color'],node.inputs['Color']);m.node_tree.links.new(node.outputs['Normal'],bs.inputs[socket])
 else:m.node_tree.links.new(t.outputs['Color'],bs.inputs[socket])

def material(name,color,rough,pattern,height,relief):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.24
 albedo=np.clip(pattern[:,:,None]*np.array(color,dtype=np.float32)[None,None,:],0,1)
 link(m,img(name+' BaseColor 2K',albedo),'Base Color');link(m,img(name+' Roughness 2K',np.clip(rough+.035*cloud,0,1),True),'Roughness');link(m,normal(name+' Normal 2K',height,relief),'Normal');return m
# Fine skin relief and subtle pigmentation; existing registered face colours are retained.
pores=smooth(fine,1);freckles=(smooth(fine,5)>1.02).astype(np.float32)
skin=material('R11 warm skin',(.54,.35,.225),.59,1+.018*cloud+.022*large-.11*freckles,pores,.11)
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.055
bone=material('R11 weathered bone',(.16,.145,.098),.84,np.clip(.9+.14*cloud+.23*large,.28,1.45),smooth(fine,2)+.3*large,.48)
weave=(np.sin(u*math.tau*630)*np.sin(v*math.tau*710)).astype(np.float32)
clothpattern=1+.05*cloud+.085*large+.017*weave
ivory=material('R11 ivory woven cloth',(.52,.47,.36),.82,clothpattern,weave+.24*smooth(fine,2),.15)
black=material('R11 charcoal woven cloth',(.012,.015,.012),.88,clothpattern,weave+.24*smooth(fine,2),.17)
# Soft highlights and fine longitudinal striations replace thick plastic-looking hair shading.
flow=.09*np.sin(v*math.tau*3)+.024*np.sin(v*math.tau*11)
strand=(np.sin(math.tau*(u*340+flow))+.3*np.sin(math.tau*(u*711+flow*.6))).astype(np.float32)
hair=material('R11 chestnut fine hair',(.053,.025,.010),.57,1+.07*strand+.065*cloud+.09*large,strand,.17)
hair.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.20
# Bind explicit UV maps, using the source's observed face diffuse where available.
for m in list(bpy.data.materials):
 if m.name in ('Reference_observed_face','Observed_brown_eye'):
  if m.name=='Reference_observed_face':
   link(m,normal('R11 observed face microrelief 2K',pores,.065),'Normal')
   bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.58;bs.inputs['Specular IOR Level'].default_value=.20
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 for i,m in enumerate(o.data.materials):
  if not m:continue
  if m.name in ('Living_skin_clean','Skin'):o.data.materials[i]=skin
  elif m.name=='Bone':o.data.materials[i]=bone
  elif m.name.startswith('R9 woven ivory'):o.data.materials[i]=ivory
  elif m.name.startswith('R9 woven charcoal'):o.data.materials[i]=black
  elif o.name.startswith(('Reference_','R10_swept_hairline')):o.data.materials[i]=hair
# Use a unique material for photo-mapped head regions; skin UV replacement does not move face pixels.
# Three thinner strands per guide preserve wave centres and reduce each strand radius to 35%.
original=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(('Reference_front_lock','Reference_back_lock'))]
for ob in original:
 a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a);rings=a.reshape(-1,12,3);centers=rings.mean(axis=1);nr=len(centers)
 axis=rings[:,0,:]-centers;other=rings[:,3,:]-centers
 for child in range(3):
  vs=[];fs=[];uvs=[];phase=math.tau*child/3
  for i,c in enumerate(centers):
   t=i/(nr-1);angle=phase+.27*math.sin(t*math.tau*1.6+child)
   center=c+.43*(math.cos(angle)*axis[i]+math.sin(angle)*other[i])
   for j in range(8):
    q=math.tau*j/8;p=center+.35*(math.cos(q)*axis[i]+math.sin(q)*other[i]);vs.append(tuple(p));uvs.append((j/8,t))
    if i:fs.append(((i-1)*8+j,(i-1)*8+(j+1)%8,i*8+(j+1)%8,i*8+j))
  fs.extend([tuple(reversed(range(8))),tuple((nr-1)*8+j for j in range(8))])
  me=bpy.data.meshes.new('R11 finer hair strand');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('R11_'+ob.name+'_'+str(child),me);bpy.context.collection.objects.link(o);me.materials.append(hair)
  uv=me.uv_layers.new(name='HairFlow')
  for poly in me.polygons:
   poly.use_smooth=True
   for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
  o['original_wave_guide']=ob.name;o['relative_cross_section_radius']=.35
 bpy.data.objects.remove(ob,do_unlink=True)
print('PBR_AND_HAIR_READY',len(original),len(texture_names),flush=True)
head=bpy.data.objects['anatomical-head']
# Densify the face and tune its triangle budget after all genuine shape changes.
def count(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();n=len(me.loop_triangles);ev.to_mesh_clear();return n
others=sum(count(o) for o in bpy.context.scene.objects if o.type=='MESH' and o!=head)
# Barycentric triangle subdivision avoids a multi-million-face temporary Subsurf.
# It adds density without claiming extra observed detail. Preserve per-corner UVs.
old=head.data;old.calc_loop_triangles();base=len(old.loop_triangles);need=2000000-others-base
assert need>=0,(others,base)
vertices=[tuple(v.co) for v in old.vertices];faces=[];uvvalues=[];materials=[]
uv=old.uv_layers[0]
count_split=need//2
candidates=[t.index for t in old.loop_triangles if sum(old.vertices[k].co.y for k in t.vertices)/3<.04]
if len(candidates)<count_split:candidates=list(range(base))
chosen=set(candidates[int(i)] for i in np.linspace(0,len(candidates)-1,count_split,dtype=int)) if count_split else set()
assert len(chosen)==count_split
odd=need%2;boundary_triangle=None;boundary_pair=None
if odd:
 bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table()
 edge=next(e for e in bm.edges if e.is_boundary)
 boundary_pair={v.index for v in edge.verts};bm.free()
 boundary_triangle=next(t.index for t in old.loop_triangles if boundary_pair.issubset(t.vertices))
 if boundary_triangle in chosen:
  chosen.remove(boundary_triangle);chosen.add(next(i for i in range(base) if i not in chosen and i!=boundary_triangle))
for t in old.loop_triangles:
 ids=list(t.vertices);coords=[tuple(uv.data[i].uv) for i in t.loops];mi=old.polygons[t.polygon_index].material_index
 if t.index in chosen:
  center=tuple(sum(vertices[k][d] for k in ids)/3 for d in range(3));uid=tuple(sum(c[d] for c in coords)/3 for d in range(2));vi=len(vertices);vertices.append(center)
  for j in range(3):faces.append((ids[j],ids[(j+1)%3],vi));uvvalues.extend((coords[j],coords[(j+1)%3],uid));materials.append(mi)
 elif t.index==boundary_triangle:
  j=next(j for j in range(3) if {ids[j],ids[(j+1)%3]}==boundary_pair);ids=ids[j:]+ids[:j];coords=coords[j:]+coords[:j]
  vi=len(vertices);vertices.append(tuple((vertices[ids[0]][d]+vertices[ids[1]][d])/2 for d in range(3)));uid=tuple((coords[0][d]+coords[1][d])/2 for d in range(2))
  faces.extend(((ids[0],vi,ids[2]),(vi,ids[1],ids[2])));uvvalues.extend((coords[0],uid,coords[2],uid,coords[1],coords[2]));materials.extend((mi,mi))
 else:faces.append(tuple(ids));uvvalues.extend(coords);materials.append(mi)
new=bpy.data.meshes.new('R11 exact-density face');new.from_pydata(vertices,[],faces);new.update()
for m in old.materials:new.materials.append(m)
layer=new.uv_layers.new(name=uv.name);layer.data.foreach_set('uv',np.asarray(uvvalues,np.float32).ravel());new.polygons.foreach_set('material_index',materials);new.polygons.foreach_set('use_smooth',[True]*len(faces))
head.data=new
triangles=others+count(head);assert triangles==2000000,triangles
print('EXACT_TRIANGLES',triangles,flush=True)
del vertices,faces,uvvalues,materials
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.context.scene['repair_revision']='r11-2M';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r11-2000k.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r11-2000k.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r11-2000k.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=triangles,target_triangles=2000000,hair_preserved=False,wave_guides_retained=True,original_locks=104,new_thin_locks=312,relative_strand_radius=.35,pbr_maps=texture_names,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R11_SAVED',triangles,flush=True)
