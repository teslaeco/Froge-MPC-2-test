"""Render exported GLB assets with repeatable cameras and real pixel dimensions.

Run inside Blender. A camera JSON from an earlier asset fixes before/after framing.
"""
import argparse
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))


def load_model(path,normalize_height=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(path))
    elif path.suffix.lower()=='.obj':bpy.ops.wm.obj_import(filepath=str(path),forward_axis='NEGATIVE_Z',up_axis='Y')
    else:bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bounds = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
    low = Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
    if normalize_height is not None:
        from mathutils import Matrix
        factor=normalize_height/(high-low).z
        transform=Matrix.Scale(factor,4)@Matrix.Translation(Vector((-(low.x+high.x)*.5,-(low.y+high.y)*.5,-low.z)))
        roots=[o for o in bpy.context.scene.objects if o.parent is None]
        for root in roots:root.matrix_world=transform@root.matrix_world
        bpy.context.view_layer.update()
        bounds=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
        low=Vector(tuple(min(p[i] for p in bounds) for i in range(3)))
        high=Vector(tuple(max(p[i] for p in bounds) for i in range(3)))
    # Use the same geometry-based target as the live MCP review.
    from runtime.review_views import face_framing
    face,face_scale,_ = face_framing(meshes)
    return {'full': list((low+high)*.5), 'height': (high-low).z,
            'face': list(face), 'face_scale':face_scale}


def render(asset, folder, views, camera_file=None, width=1080, height=1440, samples=48,normalize_height=None):
    folder.mkdir(parents=True, exist_ok=True)
    targets = load_model(asset,normalize_height)
    if camera_file:
        targets = json.loads(camera_file.read_text())
    (folder/'cameras.json').write_text(json.dumps(targets, indent=2))
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('Neutral comparison studio'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.10,.13,.17,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
    for location, power, size in (((-2,-3,3.5),420,3),((2,-1,2.2),230,2),((0,2,3),500,2)):
        bpy.ops.object.light_add(type='AREA', location=location)
        light = bpy.context.object; light.data.energy = power; light.data.shape = 'DISK'; light.data.size = size
        light.rotation_euler = (Vector((0,0,1.1))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(); camera = bpy.context.object; camera.data.type = 'ORTHO'; scene.camera = camera
    scene.render.engine = 'CYCLES'; scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
    scene.render.resolution_x = width; scene.render.resolution_y = height; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    manifest = {'source': str(asset.name), 'source_kind': 'actual exported '+asset.suffix[1:].upper(), 'width': width, 'height': height,
                'samples': samples, 'engine': 'Cycles', 'upscaled': False, 'views': [],'normalized_height':normalize_height}
    for view in views:
        is_full=view in ('full','back')
        target = Vector(targets['full' if is_full else 'face'])
        offset = {'full': (2,-4,.50), 'back':(0,4,.25), 'front': (0,-3,.01), 'profile': (3,0,.01), 'angle': (1.6,-3,.04)}[view]
        camera.location = target+Vector(offset)
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = (targets['height']*1.14 if is_full else
                                  targets.get('face_scale',.52)*max(1,.8/(width/height)))
        pending=folder/(view+'.pending.png')
        scene.render.filepath = str(pending)
        bpy.ops.render.render(write_still=True)
        data=pending.read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n') or not data.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'):
            raise ValueError('Render did not produce a complete PNG: '+view)
        pending.replace(folder/(view+'.png'))
        manifest['views'].append(view)
        (folder/'render.json').write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cameras', type=Path); parser.add_argument('--views', nargs='+', choices=['full','back','front','profile','angle'], default=['front'])
    parser.add_argument('--normalize-height',type=float)
    parser.add_argument('--width', type=int, default=1080); parser.add_argument('--height', type=int, default=1440)
    parser.add_argument('--samples', type=int, default=48)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not (64 <= args.width <= 8192 and 64 <= args.height <= 8192 and 12 <= args.samples <= 256):
        parser.error('Render dimensions or samples outside supported bounds')
    if args.normalize_height is not None and not .1<=args.normalize_height<=10:
        parser.error('Normalization height outside supported range')
    render(args.asset,args.output,args.views,args.cameras,args.width,args.height,args.samples,args.normalize_height)
