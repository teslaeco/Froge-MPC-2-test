from pathlib import Path
import bpy,math,json,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'model.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:o.data.calc_loop_triangles()
triangles=sum(len(o.data.loop_triangles) for o in meshes)
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Queen studio');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.10,.135,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for loc,power,size in (((-2,-3,3.5),420,3),((2,-1,2.2),230,2),((0,2,3),500,2)):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO'
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=2
sc.render.resolution_x=640;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
for name,pos,target,scale in [('front',(0,-4,1.05),(0,0,.96),2.02),('side',(2.8,-2.8,1.13),(0,0,.96),2.02),('upper',(.15,-4,1.7),(-.08,0,1.44),1.16),('back',(0,4,1.11),(0,0,.96),2.02)]:
 if (ROOT/(name+'.png')).exists() and name!='upper':continue
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
missing=[n.image.name for o in meshes for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and min(n.image.size)==0]
(ROOT/'render-verification.json').write_text(json.dumps({'render_source':'actual exported GLB reimport','triangles':triangles,'mesh_objects':len(meshes),'missing_texture_images':sorted(set(missing)),'model_sha256':hashlib.sha256((ROOT/'model.glb').read_bytes()).hexdigest(),'views':['front','side','upper','back'],'face_likeness_verified':False},indent=2))
