import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1'); OUT=ROOT/'resume-model'

def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,pos,power,size):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1.4))
def setup(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=5;s.render.threads_mode='FIXED';s.render.threads=4
 s.render.resolution_x=640;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 s.world=bpy.data.worlds.new('Neutral review world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.26,.30,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 s.view_settings.view_transform='AgX'
 light('Review key',(-1.8,-2.8,3.6),380,2.4);light('Review fill',(2.0,-1.5,2.5),130,2.3);light('Review rim',(0,2,3.0),200,2)
 bpy.ops.object.camera_add();s.camera=bpy.context.object;s.camera.data.type='ORTHO'
 return s

def render(s,name,view):
 c=s.camera
 if view=='face':target=(0,.035,1.515);c.location=(0,-3,1.515);c.data.ortho_scale=.515
 else:
  target=(0,.035,1.118);c.data.ortho_scale=1.30
  c.location={'front':(0,-3,1.118),'left':(-3,.035,1.118),'back':(0,3,1.118)}[view]
 aim(c,target);s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
paths={'before':ROOT/'public-resume/dist/assets/model.glb','after':OUT/'FORGE-E18R.glb'}
results={}
for label,path in paths.items():
 s=setup(path);meshes=[o for o in s.objects if o.type=='MESH']; tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
 results[label]={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mesh_objects':len(meshes),'triangles':tris,'images':[{'name':i.name,'width':i.size[0],'height':i.size[1]} for i in bpy.data.images if i.size[0]],'renders':{}}
 views=['face','front'] if label=='before' else ['face','front','left','back']
 for view in views:
  fn=f'{label}-{view}.png';render(s,fn,view);results[label]['renders'][view]={'path':fn,'sha256':hashlib.sha256((OUT/fn).read_bytes()).hexdigest()}
 (OUT/'render-verification.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
