"""Render actual reimported print GLB in neutral clay; no generated-image edits."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);args.output_dir.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(args.input.resolve()))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    mat=bpy.data.materials.new('Neutral clay — actual production candidate');mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.48,.52,.55,1);bsdf.inputs['Roughness'].default_value=.67
    for obj in meshes:obj.data.materials.clear();obj.data.materials.append(mat)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-2.0
    scene.world=bpy.data.worlds.new('Print review world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    for name,loc,power,size in [('key',(-.5,-.7,.65),100,.45),('fill',(.5,-.2,.3),45,.45),('rim',(.3,.5,.6),90,.4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=loc;aim(light,(0,0,.1))
    camdata=bpy.data.cameras.new('Orthographic production review');cam=bpy.data.objects.new('camera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO'
    views=[('front',(0,-.8,.13),(0,0,.1),.245),('left',(-.8,0,.13),(0,0,.1),.245),('back',(0,.8,.13),(0,0,.1),.245),('face',(.15,-.8,.205),(0,0,.177),.075)]
    views=[v for v in views if v[0] in {'front','face'}]
    rows=[]
    for name,location,target,ortho in views:
        cam.location=location;aim(cam,target);camdata.ortho_scale=ortho
        path=args.output_dir/('print-'+name+'.png');scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
        rows.append({'view':name,'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_location':location,'camera_target':target,'orthographic_scale_m':ortho})
    (args.output_dir/'print-render-verification.json').write_text(json.dumps({'source':args.input.name,'source_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'render':'real Blender Cycles reimport, neutral clay','resolution':[640,800],'samples':24,'views':rows},indent=2)+'\n')
if __name__=='__main__':main()
