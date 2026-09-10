"""Small, honest review images rendered from the delivered GLB, on CPU."""
from pathlib import Path
import bpy
from mathutils import Vector

LABELS=('front','three-quarter','face')


def render_review(model,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bounds=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
    low=Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
    target=(low+high)*.5;span=high-low
    scene=bpy.context.scene;scene.world=bpy.data.worlds.new('Reference review')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.07,.09,.12,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
    for delta,power,size in (((-2,-3,3),400,3),((2,-1,1.8),200,2),((0,2,3),450,2)):
        bpy.ops.object.light_add(type='AREA',location=target+Vector(delta))
        light=bpy.context.object;light.data.energy=power;light.data.size=size
        light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
    camera.data.type='ORTHO'
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scale=max(span.z,span.x/0.8)*1.12
    eyes=[o.matrix_world.translation for o in meshes if o.get('anatomical_eye')]
    face=sum(eyes,Vector())/len(eyes) if eyes else target
    for label,direction,aim,frame in (
        ('front',(0,-4,.12),target,scale),
        ('three-quarter',(2,-4,.5),target,scale),
        ('face',(.6,-3,.1),face+Vector((0,0,-.025)),max(.40,span.x*1.15) if len(eyes)>2 else .40)):
        camera.location=aim+Vector(direction)
        camera.rotation_euler=(aim-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=frame
        scene.render.filepath=str(folder/(label+'.png'))
        bpy.ops.render.render(write_still=True)
    return [str(folder/(label+'.png')) for label in LABELS]
