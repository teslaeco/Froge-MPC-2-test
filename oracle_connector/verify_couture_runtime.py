"""Real Blender v19 generation/reimport/review. Run with Blender --python.

blender -b --python verify_couture_runtime.py -- --output /absolute/review --render
No AI is called. All PNGs come from the exported GLB after reimport.
"""
import argparse
import json
from pathlib import Path
import runpy
import sys
import time
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
from scene_contract import parse_scene
from build_scene import build_scene


def verify(output,render=False):
    output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    scene=parse_scene((ROOT/'examples/couture-fan-v19.scene.json').read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    runtime=runpy.run_path(str(ROOT/'runtime/run.py'),run_name='couture_fixture')
    build_scene(scene,*(runtime[n] for n in ('make_material','mesh_object','tube','ellipsoid','join_meshes')))
    runtime['finish'](output)
    report=json.loads((output/'result.json').read_text())
    assert report['export_validation']['reimported'] is True
    report.update(blender=bpy.app.version_string,build_seconds=round(time.monotonic()-started,2),
                  source='authored scene using production runtime; no paid AI',visual_reviewed=False)
    (output/'verification.json').write_text(json.dumps(report,indent=2))
    if not render:return report
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output/'model.glb'))
    sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Review studio');sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.13,.17,1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    for loc,power,size in (((-2,-3,3.5),420,3),((2,-1,2.2),230,2),((0,2,3),500,2)):
        bpy.ops.object.light_add(type='AREA',location=loc);obj=bpy.context.object
        obj.data.energy=power;obj.data.shape='DISK';obj.data.size=size
        obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();camera=bpy.context.object;sc.camera=camera;camera.data.type='ORTHO'
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.threads_mode='FIXED';sc.render.threads=2
    sc.render.resolution_x=840;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    reviews=[('full-front',(0,-4,1.2),(0,0,.94),2.08),
             ('full-three-quarter',(2,-4,1.7),(0,0,.94),2.08),
             ('full-back',(0,4,1.3),(0,0,.94),2.08),
             ('face-front',(0,-3,1.65),(0,0,1.64),.42),
             ('face-profile',(3,0,1.65),(0,0,1.64),.42),
             ('face-three-quarter',(1.6,-3,1.7),(0,0,1.64),.42)]
    for label,position,aim,scale in reviews:
        camera.location=position;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale;sc.render.filepath=str(output/(label+'.png'))
        bpy.ops.render.render(write_still=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--render',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(verify(args.output,args.render)),flush=True)
