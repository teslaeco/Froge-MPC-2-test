"""R14 anatomical local changes: crowns, recessed orbital eye, neck proportions."""
import bpy,math,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'anatomy-r14';sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs
before=json.loads((OUT/'geometry-before.json').read_text());records={r['name']:r for r in before}
def material(name,c,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough;return m
crown=material('R14 warm natural enamel',(.64,.56,.40),.27);crown.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.32
# Cervical shade to lighter incisal edge, packed colour data for portable exports.
N=512;v=np.arange(N,dtype=np.float32)[:,None]/(N-1);a=np.ones((N,N,4),np.float32);a[:,:,:3]=np.array([.64,.56,.40])[None,None,:]*(.91+.09*np.cos(v*math.pi/2))[:,:,None]
im=bpy.data.images.new('R14 enamel cervical shade',width=N,height=N,alpha=False);im.pixels.foreach_set(a.ravel());im.update();im.pack();t=crown.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;crown.node_tree.links.new(t.outputs['Color'],crown.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
changed=[]
for ob in list(bpy.context.scene.objects):
 if not ob.name.startswith(('Anatomical_upper_tooth','Anatomical_lower_tooth')):continue
 r=records[ob.name];lo=np.array(r['min']);hi=np.array(r['max']);center=(lo+hi)/2;size=hi-lo;upper='upper' in ob.name;j=int(ob.name.rsplit('_',1)[1]);side=-1 if center[0]<0 else 1
 width=size[0]*.94;depth=size[1]*.90;height=([.010,.0095,.0105,.0085,.008,.0075][j] if upper else .0038)
 # Upper crowns keep their incisal edge instead of protruding farther into the smile.
 center[2]=lo[2]+height*.5;center[1]+=.0018 if upper else .003
 vs=[];fs=[];uv=[];rings=24;cols=32
 for i in range(rings+1):
  phi=math.pi*(i+.0001)/(rings+.0002);z=math.cos(phi);rad=math.sin(phi);taper=1-.15*max(z,0)
  for k in range(cols):
   th=math.tau*k/cols;cs=math.cos(th);sn=math.sin(th)
   x=width*.5*math.copysign(abs(cs)**.75,cs)*rad**.55*taper
   y=depth*.5*sn*rad**.65
   zz=height*.5*z
   # Canine incisal tip, softly blended rather than cuboid crown.
   if upper and j==2:zz-=.0013*max(0,-z)**3*max(0,1-abs(x)/(width*.5))
   angle=side*(.015 if j==1 else -.010 if j==2 else 0)
   vs.append((center[0]+x*math.cos(angle)-zz*math.sin(angle),center[1]+y,center[2]+zz*math.cos(angle)+x*math.sin(angle)));uv.append((k/cols,i/rings))
   if i:fs.append(((i-1)*cols+k,(i-1)*cols+(k+1)%cols,i*cols+(k+1)%cols,i*cols+k))
 fs.append(tuple(reversed(range(cols))));fs.append(tuple(rings*cols+k for k in range(cols)))
 name=ob.name;bpy.data.objects.remove(ob,do_unlink=True);me=bpy.data.meshes.new(name+' rounded crown');me.from_pydata(vs,[],fs);me.update();obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);me.materials.append(crown);layer=me.uv_layers.new(name='CrownUV')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
 changed.append({'object':name,'crown_dimensions':[width,depth,height],'rounded_surface':True})
# Alive eye is moved slightly behind its existing eyelid opening.
eye=bpy.data.objects['anatomical-eye-r'];center=sum((v.co for v in eye.data.vertices),Vector())/len(eye.data.vertices)
for vert in eye.data.vertices:
 vert.co.x=center.x+(vert.co.x-center.x)*.96;vert.co.z=center.z+(vert.co.z-center.z)*.96;vert.co.y+=.0012
# User explicitly requests an eye inside the skeletal socket. Keep it recessed and dark.
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
sclera=material('R14 shaded orbital sclera',(.105,.082,.054),.34);iris=material('R14 dark brown recessed iris',(.033,.014,.006),.23);pupil=material('R14 recessed pupil',(.0015,.0012,.001),.16)
sphere('anatomical-eye-l',(.0423,.036,1.5842),(.020,.020,.020),sclera)
sphere('R14 recessed brown iris',(.0423,.0161,1.5842),(.0086,.0014,.0086),iris)
sphere('R14 recessed pupil',(.0423,.0148,1.5842),(.0041,.0007,.0041),pupil)
# Reduce the hidden overlapping neck stump gradually; no deletion of head faces.
head=bpy.data.objects['anatomical-head'];chest=bpy.data.objects['R9_continuous_shoulders_neck'];neck_adjusted=0
for vert in head.data.vertices:
 x,y,z=vert.co
 if z<1.438:
  f=max(0,min(1,(1.438-z)/.035));f=f*f*(3-2*f);cy=.068;rx=.047;ry=.062
  q=math.sqrt((x/rx)**2+((y-cy)/ry)**2)
  if q>1:
   vert.co.x=x*(1-f)+x/q*f;vert.co.y=y*(1-f)+(cy+(y-cy)/q)*f;neck_adjusted+=1
 # Small sculpted living-cheek contour, preserving registered UVs.
 if x<-.010 and y<.04 and z>1.45:
  cheek=math.exp(-((x+.065)/.026)**2-((z-1.541)/.028)**2);vert.co.y-=.0022*cheek
head.data.update()
# Shorten transition by 32mm in source scene units, deforming every attached mesh together.
neck_shift=.032
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 inv=ob.matrix_world.inverted();raw=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',raw);xyz=raw.reshape(-1,3);mat=np.array(ob.matrix_world);world=xyz@mat[:3,:3].T+mat[:3,3];f=np.clip((world[:,2]-1.30)/.145,0,1);f=f*f*(3-2*f);world[:,2]-=neck_shift*f;imat=np.array(inv);local=world@imat[:3,:3].T+imat[:3,3];ob.data.vertices.foreach_set('co',local.astype(np.float32).ravel());ob.data.update()
# Warmer coherent skin response on neck, shoulders and arms; retained fine normal maps.
skin_materials=[]
for m in bpy.data.materials:
 if m.name.startswith('R11 warm skin') and m.use_nodes:
  bs=m.node_tree.nodes.get('Principled BSDF')
  for l in list(m.node_tree.links):
   if l.to_node==bs and l.to_socket.name=='Base Color':m.node_tree.links.remove(l)
  bs.inputs['Base Color'].default_value=(.44,.305,.185,1);bs.inputs['Specular IOR Level'].default_value=.27;bs.inputs['Subsurface Weight'].default_value=.045;skin_materials.append(m.name)
# Drier dark garment response, avoiding glossy latex-like broad highlights.
for m in bpy.data.materials:
 if m.name=='R13 black fine twill':m.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.19
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
tri=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
bpy.context.scene['repair_revision']='r14-anatomy';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r14.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r14.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r14.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=tri,teeth_rebuilt=changed,neck_shift_source_units=neck_shift,neck_vertices_tapered=neck_adjusted,eye_added='recessed skeletal socket eye explicitly requested by user',living_eye_recess=.0012,skin_materials=skin_materials,wave_guides_retained=True,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R14_SAVED',tri,len(changed),neck_adjusted,flush=True)
