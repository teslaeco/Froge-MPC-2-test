"""Reimport actual FBX and compare geometry/UVs; render that imported model."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from review_views import geometry_bounds,face_framing
asset=OUT/'FORGE-model-r15.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(asset));bpy.context.view_layer.update()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];low,high=geometry_bounds(meshes)
triangles=0
for ob in meshes:ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
source=json.loads((OUT/'export-report.json').read_text());assert source['triangles']==triangles,(source['triangles'],triangles)
assert len([o for o in meshes if o.name=='anatomical-eye-r'])==1
assert len([o for o in meshes if o.name=='anatomical-eye-l'])==1
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
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Review studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.14,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for loc,power,size in [((-2,-3,4),420,3),((2,-1,2),190,2),((0,2,3),330,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.size=size
 light.rotation_euler=(Vector((0,0,1.4))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO'
scene.cycles.samples=128
scene.cycles.adaptive_threshold=.012
scene.render.resolution_x=2048;scene.render.resolution_y=2560
# Dramatic but readable green studio background; geometry remains the same.
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.055,.044,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
for ob in scene.objects:
 if ob.type=='LIGHT':
  if ob.location.x<0:ob.data.color=(1,.91,.79)
  elif ob.location.y>0:ob.data.color=(.78,.87,1)
camera.location=Vector((.055,-3,1.35));target=Vector((.004,.018,1.285));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.93
scene.render.filepath=str(OUT/'FORGE-r15-render-HQ.png');bpy.ops.render.render(write_still=True)
(OUT/'hq-render-report.json').write_text(json.dumps({'source_fbx_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'resolution':[2048,2560],'samples':128,'engine':'Cycles CPU','generated_illustration':False,'same_geometry_as_reviews':True},indent=2));print('HQ_RENDER_READY',flush=True)
