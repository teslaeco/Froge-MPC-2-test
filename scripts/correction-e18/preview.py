import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path('/workspace/scratch/584c9d97a5a1/correction-e18');mode='preview'

for ob in list(bpy.context.scene.objects):
 if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.11,.14,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for loc,power,size in [((-2,-3,4),420,3),((2,-1,2),190,2),((0,2,3),330,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';face=Vector((0,.05984,1.54615))
views=[('face',face,.44822,0)]
if mode=='after':views += [('angle',face,.44822,.55),('left',Vector((0,.02,1.15)),1.32,math.pi/2),('back',Vector((0,.02,1.15)),1.32,math.pi)]
for name,target,scale,angle in views:
 camera.location=target+Vector((-3*math.sin(angle),-3*math.cos(angle),.06 if name in ('front','left','back') else 0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;scene.render.filepath=str(P/(mode+'-'+name+'.png'));bpy.ops.render.render(write_still=True);print('RENDERED',mode,name,flush=True)
mat=bpy.data.materials.new('Geometry review');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.38,.38,.38,1);bs.inputs['Roughness'].default_value=.8;scene.view_layers[0].material_override=mat
camera.location=face+Vector((0,-3,0));camera.rotation_euler=(face-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.44822;scene.render.filepath=str(P/(mode+'-clay.png'));bpy.ops.render.render(write_still=True)
