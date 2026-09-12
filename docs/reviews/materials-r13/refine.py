"""R13 portable, scale-calibrated fabric and region-specific facial PBR materials."""
import bpy,math,json,sys,hashlib
import numpy as np
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'materials-r13';sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs
N=2048;u=np.arange(N,dtype=np.float32)[None,:]/N;v=np.arange(N,dtype=np.float32)[:,None]/N
maps=[]
def image(name,a,data=False):
 im=bpy.data.images.new(name,width=N,height=N,alpha=False);im.colorspace_settings.name='Non-Color' if data else 'sRGB';p=np.ones((N,N,4),np.float32);p[:,:,:3]=a[:,:,None] if a.ndim==2 else a;im.pixels.foreach_set(p.ravel());im.update();im.pack();maps.append(name);return im
def normal(name,h,strength):
 dx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength;d=np.sqrt(1+dx*dx+dy*dy);return image(name,np.stack((.5-.5*dx/d,.5-.5*dy/d,.5+.5/d),2),True)
def bind(m,im,socket):
 bs=m.node_tree.nodes.get('Principled BSDF');nt=m.node_tree
 for l in list(nt.links):
  if l.to_node==bs and l.to_socket.name==socket:nt.links.remove(l)
 t=nt.nodes.new('ShaderNodeTexImage');t.image=im;t.interpolation='Linear'
 if socket=='Normal':
  n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.32;nt.links.new(t.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs[socket])
 else:nt.links.new(t.outputs['Color'],bs.inputs[socket])
def mat(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;return m
# 200mm repeat, 0.8mm warp/weft; subtle thread variation, no macro stains.
warp=np.cos(math.tau*u*250);weft=np.cos(math.tau*v*250);over=np.sin(math.tau*u*125)*np.sin(math.tau*v*125)
height=(warp+weft+.5*over).astype(np.float32)
thread=(1+.025*warp+.025*weft+.008*np.sin(u*math.tau*41)+.006*np.sin(v*math.tau*37)).astype(np.float32)
rng=np.random.default_rng(913);fine=rng.standard_normal((N,N),dtype=np.float32);thread+=.004*fine
fabrics=[]
for name,col,rough in [('R13 ivory linen silk',(.69,.655,.555),.70),('R13 black fine twill',(.032,.035,.030),.78)]:
 m=mat(name);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.28;bs.inputs['Sheen Weight'].default_value=.12;bs.inputs['Sheen Roughness'].default_value=.65
 bind(m,image(name+' colour',np.clip(thread[:,:,None]*np.array(col)[None,None,:],0,1)),'Base Color')
 bind(m,image(name+' roughness',np.clip(rough+.035*over+.012*fine,.35,.95),True),'Roughness');bind(m,normal(name+' tangent weave',height,.25),'Normal');fabrics.append(m)
# UV repeat calibrated to approximate circumference and measured vertical extent.
uv_report=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith(('R9_tailored_split_gown','R9_gathered_sleeve')):
  for i,m in enumerate(ob.data.materials):ob.data.materials[i]=fabrics[0 if 'ivory' in m.name.lower() else 1]
  uv=ob.data.uv_layers[0];a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a);a=a.reshape(-1,2)
  scale=(6.,3.35) if 'gown' in ob.name else (1.8,2.85);a*=np.array(scale,np.float32);uv.data.foreach_set('uv',a.ravel());uv_report.append({'object':ob.name,'uv_repeat':scale,'tile_m':.2})
# Seams retain their original geometry but are distinguishable from the fabric.
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob.name.startswith(('R9_bodice_seam','R9_neckline','R9_sleeve_edge')):
  m=mat('R13 seam '+ob.name);bs=m.node_tree.nodes.get('Principled BSDF');light='-1' in ob.name;bs.inputs['Base Color'].default_value=(.28,.24,.16,1) if light else (.011,.012,.01,1);bs.inputs['Roughness'].default_value=.78;ob.data.materials.clear();ob.data.materials.append(m)
# Preserve observed features in the existing registered photo; separate surface response.
base=bpy.data.materials['Reference_observed_face'];skin=base.copy();skin.name='R13 observed living face';bone=base.copy();bone.name='R13 observed skeletal face'
# Roughness map registered to the original 899x2048 reference coordinates.
x=u*899;y=(1-v)*2048
lip=np.exp(-((x-425)/49)**4-((y-660)/23)**4);nose=np.exp(-((x-446)/24)**2-((y-584)/49)**2);cheek=np.exp(-((x-358)/45)**2-((y-575)/60)**2)
rough=np.clip(.52-.23*lip-.12*nose-.06*cheek,.27,.58)
bind(skin,image('R13 face feature roughness',rough,True),'Roughness')
# Lower pore strength; the prior uniform relief should not roughen lips/eyelids.
bs=skin.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.30;bs.inputs['Subsurface Weight'].default_value=.035;bs.inputs['Subsurface Radius'].default_value=(1,.45,.22)
for n in skin.node_tree.nodes:
 if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.12
bs=bone.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.86;bs.inputs['Specular IOR Level'].default_value=.12;bs.inputs['Subsurface Weight'].default_value=0
for n in bone.node_tree.nodes:
 if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.4
head=bpy.data.objects['anatomical-head'];head.data.materials.append(skin);si=len(head.data.materials)-1;head.data.materials.append(bone);bi=len(head.data.materials)-1
counts={'skin':0,'bone':0}
for p in head.data.polygons:
 m=head.data.materials[p.material_index]
 if m and m.name.startswith('Reference_observed_face'):
  if p.center.x<0:p.material_index=si;counts['skin']+=1
  else:p.material_index=bi;counts['bone']+=1
# Tone down uniform chalkiness of enamel; keep actual tooth shape intact.
for m in bpy.data.materials:
 if 'tooth' in m.name.lower() or 'teeth' in m.name.lower():
  if m.use_nodes:
   bs=m.node_tree.nodes.get('Principled BSDF')
   if bs:bs.inputs['Roughness'].default_value=.28;bs.inputs['Specular IOR Level'].default_value=.32
# Remove unused nodes/images imported during earlier rejected iterations from this copy.
used={m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m}
for m in used:
 if not m.use_nodes:continue
 nt=m.node_tree;out=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None);keep=set()
 def walk(n):
  if n in keep:return
  keep.add(n)
  for s in n.inputs:
   for l in s.links:walk(l.from_node)
 if out:walk(out)
 for n in list(nt.nodes):
  if n not in keep:nt.nodes.remove(n)
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
tri=sum(len(o.data.loop_triangles) for o in []);tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
bpy.context.scene['repair_revision']='r13-materials';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r13.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r13.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r13.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=tri,maps=maps,cloth_uv=uv_report,face_region_polygons=counts,geometry_changed=False,wave_guides_retained=True,likeness_accepted=False,reference_lighting_removed=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R13_SAVED',tri,counts,flush=True)
