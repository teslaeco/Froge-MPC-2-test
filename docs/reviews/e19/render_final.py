"""Render actual reimported GLBs with fixed neutral comparison cameras."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'final'

def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def setup(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.max_bounces=5
    s.render.threads_mode='FIXED';s.render.threads=4
    s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.film_transparent=False
    s.world=bpy.data.worlds.new('Neutral review world');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.26,.30,1)
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    s.view_settings.view_transform='AgX'
    for name,pos,power,size in [('Key',(-1.8,-2.8,3.6),380,2.4),('Fill',(2,-1.5,2.5),130,2.3),('Rim',(0,2,3),200,2)]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1.4))
    bpy.ops.object.camera_add();s.camera=bpy.context.object;s.camera.data.type='ORTHO'
    return s

def render(s,view,path):
    c=s.camera;target=(0,.035,1.118);c.data.ortho_scale=1.30
    pos={'front':(0,-3,1.118),'left':(-3,.035,1.118),'right':(3,.035,1.118),'back':(0,3,1.118)}
    if view in pos:c.location=pos[view]
    elif view=='face':target=(0,.035,1.515);c.location=(0,-3,1.515);c.data.ortho_scale=.515
    elif view=='underside':target=(0,.035,1.47);c.location=(1.2,-2.3,.55);c.data.ortho_scale=.49
    elif view=='skin':
        target=(-.08,-.075,1.295);c.location=(-.08,-2.7,1.35);c.data.ortho_scale=.18
        s.render.resolution_x=1200;s.render.resolution_y=1500;s.cycles.samples=64
    aim(c,target);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)

report={}
for label,path,views in [
    ('before',ROOT.parent/'resume-model/FORGE-E18R.glb',['face','front']),
    ('after',OUT/'FORGE-E19-web.glb',['face','front','left','right','back','underside']),
    ('8k',OUT/'FORGE-E19-8K.glb',['skin'])]:
    s=setup(path)
    report[label]={'source':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'images':[{'name':i.name,'width':i.size[0],'height':i.size[1]} for i in bpy.data.images if i.size[0]],
                   'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH'),
                   'renders':{}}
    for view in views:
        output=OUT/(label+'-'+view+'.png');render(s,view,output)
        report[label]['renders'][view]={'file':output.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'pixels':[s.render.resolution_x,s.render.resolution_y]}
        (OUT/'render-verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print('E19_RENDER_DONE',label,view,flush=True)
