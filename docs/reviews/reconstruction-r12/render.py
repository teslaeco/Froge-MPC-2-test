"""Reimport actual FBX and compare geometry/UVs; render that imported model."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'reconstruction-r12'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from review_views import geometry_bounds,face_framing
asset=OUT/'FORGE-model-r12.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(asset));bpy.context.view_layer.update()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];low,high=geometry_bounds(meshes)
triangles=0
for ob in meshes:ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
source=json.loads((OUT/'export-report.json').read_text());assert abs(source['triangles']-triangles)<10,(source['triangles'],triangles)
assert len([o for o in meshes if o.name.startswith('anatomical-eye-r')])==1
missing=[im.name for im in bpy.data.images if im.users and min(im.size)==0];assert not missing,missing
# FBX does not preserve glTF extras; recover known semantic object identity.
for ob in meshes:
 if ob.name=='anatomical-head':ob['anatomical_head']=True
 if ob.name=='anatomical-eye-r':ob['anatomical_eye']=True
# Freeze review camera to R11 head geometry for a genuine before/after comparison.
with bpy.data.libraries.load(str(ROOT/'refinement-r11/FORGE-model-r11-2000k.blend'),link=False) as (src,dst):dst.objects=['anatomical-head']
ref=dst.objects[0];coords=[v.co for v in ref.data.vertices]
lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)));hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
face=(lo+hi)*.5;span=hi-lo;scale=max(span.z,span.x/.8,span.y/.8)*1.20
bpy.data.objects.remove(ref,do_unlink=True)
(OUT/'fixed-camera.json').write_text(json.dumps({'source':'R11 head bounds','target':list(face),'ortho_scale':scale,'resolution':[640,800],'lighting':'same as R11'}))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Review studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.14,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for loc,power,size in [((-2,-3,4),420,3),((2,-1,2),190,2),((0,2,3),330,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.size=size
 light.rotation_euler=(Vector((0,0,1.4))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO'
views=[('face',face,scale,0),('front',Vector((0,.02,1.15)),1.32,0),('left',Vector((0,.02,1.15)),1.32,math.pi/2),('back',Vector((0,.02,1.15)),1.32,math.pi)]
for name,target,frame,angle in views:
 camera.location=target+Vector((-3*math.sin(angle),-3*math.cos(angle),0 if name=='face' else .06));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=frame
 scene.render.filepath=str(OUT/('FBX-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print('FBX_RENDER_READY',name,flush=True)
# Neutral material exposes geometry without reference photo colours.
clay=bpy.data.materials.new('Geometry only clay');clay.use_nodes=True;bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.38,.38,.38,1);bs.inputs['Roughness'].default_value=.8
scene.view_layers[0].material_override=clay
camera.location=face+Vector((0,-3,0));camera.rotation_euler=(face-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
scene.render.filepath=str(OUT/'FBX-face-clay.png');bpy.ops.render.render(write_still=True)
report={'fbx_reimport_verified':True,'triangles':triangles,'mesh_objects':len(meshes),'bounds':[list(low),list(high)],'missing_textures':missing,'meshes_with_uv':sum(bool(o.data.uv_layers) for o in meshes),'renders':'actual reimported FBX','wave_guides_retained':source['wave_guides_retained'],'likeness_accepted':False,'print_ready':False}
(OUT/'fbx-reimport-report.json').write_text(json.dumps(report,indent=2));print('FBX_REIMPORT_PASS',json.dumps(report),flush=True)
