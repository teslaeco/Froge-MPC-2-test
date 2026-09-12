"""Real Blender generation/reimport/review. Run with Blender --python.

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


def verify(output,render=False,scene_path=None,views=None,samples=48,threads=8):
    output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    scene=parse_scene((scene_path or ROOT/'examples/couture-fan-v19.scene.json').read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    runtime=runpy.run_path(str(ROOT/'runtime/run.py'),run_name='couture_fixture')
    build_scene(scene,*(runtime[n] for n in ('make_material','mesh_object','tube','ellipsoid','join_meshes')),reference_folder=output)
    runtime['finish'](output)
    report=json.loads((output/'result.json').read_text())
    assert report['export_validation']['reimported'] is True
    report.update(blender=bpy.app.version_string,build_seconds=round(time.monotonic()-started,2),
                  source='authored scene using production runtime; no paid AI',visual_reviewed=False)
    (output/'verification.json').write_text(json.dumps(report,indent=2))
    if not render:return report
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output/'model.glb'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bounds=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
    low=Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
    target=(low+high)*.5;span=high-low
    frame=max(span.z,span.x/(840/1080))*1.12
    eyes=[o.matrix_world.translation for o in meshes if o.get('anatomical_eye')]
    face=sum(eyes,Vector())/len(eyes)-Vector((0,0,.015)) if eyes else target
    hands=[o for o in meshes if 'grip_contact_positions' in o]
    grip=face-Vector((.17,.20,.40))
    if hands:
        values=list(hands[0]['grip_contact_positions'])
        grip=sum((hands[0].matrix_world@Vector(values[i:i+3]) for i in range(0,len(values),3)),Vector())/5
        grip+=Vector((-.030,0,-.018))
    free_hands=[o for o in meshes if o.get('anatomical_hand') and 'grip_contact_positions' not in o]
    free_hand=target
    if free_hands:
        free_hand=sum((free_hands[0].matrix_world@Vector(p) for p in free_hands[0].bound_box),Vector())/8
    sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Review studio');sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.13,.17,1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    for loc,power,size in (((-2,-3,3.5),420,3),((2,-1,2.2),230,2),((0,2,3),500,2)):
        bpy.ops.object.light_add(type='AREA',location=loc);obj=bpy.context.object
        obj.data.energy=power;obj.data.shape='DISK';obj.data.size=size
        obj.rotation_euler=(Vector((0,0,1.1))-obj.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();camera=bpy.context.object;sc.camera=camera;camera.data.type='ORTHO'
    sc.render.engine='CYCLES';sc.cycles.samples=samples;sc.cycles.use_denoising=True
    sc.render.threads_mode='FIXED';sc.render.threads=threads
    sc.render.resolution_x=840;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    reviews=[('full-front',target+Vector((0,-4,.26)),target,frame),
             ('full-three-quarter',target+Vector((2,-4,.76)),target,frame),
             ('full-back',target+Vector((0,4,.36)),target,frame),
             ('face-front',face+Vector((0,-3,.01)),face,.42),
             ('face-profile',face+Vector((3,0,.01)),face,.42),
             ('face-three-quarter',face+Vector((1.6,-3,.06)),face,.42),
             ('upper-three-quarter',face+Vector((1.085,-3,-.14)),face+Vector((-.065,0,-.26)),1.02),
             ('hand-detail',grip+Vector((.65,-3,.14)),grip,.30),
             ('free-hand-detail',free_hand+Vector((2,-3,.20)),free_hand,.36)]
    rendered=[]
    for label,position,aim,scale in reviews:
        if views and label not in views:continue
        camera.location=position;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale;sc.render.filepath=str(output/(label+'.png'))
        bpy.ops.render.render(write_still=True)
        rendered.append(label)
    report.update(rendered_views=rendered,render_source='exported GLB reimport',
                  render_device='CPU',render_threads=threads,render_samples=samples,
                  total_seconds=round(time.monotonic()-started,2))
    (output/'verification.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--render',action='store_true')
    parser.add_argument('--scene',type=Path);parser.add_argument('--views',nargs='+',choices=['full-front','full-three-quarter','full-back','face-front','face-profile','face-three-quarter','upper-three-quarter','hand-detail','free-hand-detail'])
    parser.add_argument('--samples',type=int,choices=range(12,129),default=48)
    parser.add_argument('--threads',type=int,choices=range(1,17),default=8)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    print(json.dumps(verify(args.output,args.render,args.scene,args.views,args.samples,args.threads)),flush=True)

