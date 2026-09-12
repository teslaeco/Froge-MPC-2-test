import bpy,math,sys
from mathutils import Vector
from pathlib import Path
out=Path('/workspace/scratch/584c9d97a5a1/model-repair')
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
prefix=args[0] if args else 'baseline'
if prefix!='baseline':
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(out/('FORGE-model-poprawka-'+prefix+'.glb')))
scene=bpy.context.scene
for o in list(scene.objects):
 if o.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Repair_studio_world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.14,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-2,-3,4),420,3),('Fill',(2,-1,2),190,2),('Rim',(0,2,3),330,2)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,(0,0,1.4))
d=bpy.data.cameras.new('Repair_camera');cam=bpy.data.objects.new('Repair_camera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=1.18
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
prefix=args[0] if args else 'baseline'
views=['front'] if prefix=='baseline' else ['front','left','back']
for name in views:
 angle={'front':0,'left':math.pi/2,'back':math.pi}[name]
 target=Vector((0,.02,1.29));cam.location=target+Vector((-3*math.sin(angle),-3*math.cos(angle),.06));aim(cam,target)
 scene.render.filepath=str(out/(prefix+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print('RENDER_READY',scene.render.filepath,flush=True)
