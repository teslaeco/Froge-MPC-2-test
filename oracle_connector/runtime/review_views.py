"""Small, honest review images rendered from the delivered GLB, on CPU."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

LABELS=('front','three-quarter','face','side','back')


def geometry_bounds(objects):
    """World-space geometry, independent of baked transforms/object origins."""
    depsgraph=bpy.context.evaluated_depsgraph_get()
    points=[]
    for obj in objects:
        evaluated=obj.evaluated_get(depsgraph)
        if evaluated.type=='MESH' and len(evaluated.data.vertices):
            points.extend(evaluated.matrix_world@Vector(p) for p in evaluated.bound_box)
    if not points:raise ValueError('Brak geometrii do kadrowania podgladu.')
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def face_framing(meshes, aspect=.8):
    # A single living eye is off-centre; head geometry frames BOTH halves.
    # Eye origins may be zero after geometry edits and GLB export.
    heads=[o for o in meshes if o.get('anatomical_head')]
    eyes=[o for o in meshes if o.get('anatomical_eye')]
    selected=heads or eyes or meshes
    low,high=geometry_bounds(selected)
    span=high-low
    centre=(low+high)*.5
    if heads:
        # Anatomical heads include a short cervical section: retain the crown
        # and chin, leaving useful context without aiming at an eye origin.
        frame=max(span.z,span.x/aspect,span.y/aspect)*1.20
    elif eyes:
        frame=max(span.x/aspect*2.5,span.z*5,.40)
        centre.z-=frame*.12
    else:
        frame=max(span.z,span.x/aspect,span.y/aspect)*1.12
    return centre,max(frame,.001),selected


def frame_evidence(scene,camera,objects):
    """Geometric framing evidence, not a likeness or occlusion score."""
    from bpy_extras.object_utils import world_to_camera_view
    low,high=geometry_bounds(objects)
    points=[world_to_camera_view(scene,camera,Vector((x,y,z)))
            for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)]
    left,right=min(p.x for p in points),max(p.x for p in points)
    bottom,top=min(p.y for p in points),max(p.y for p in points)
    overlap=max(0,min(1,right)-max(0,left))*max(0,min(1,top)-max(0,bottom))
    visible=all(p.z>0 for p in points) and overlap>.005
    return {'target_bounds':[list(low),list(high)],'projected_bounds':[left,bottom,right,top],
            'frustum_overlap':overlap,'framing_valid':visible,'likeness_verified':False}


def configure_review(scene, allow_denoising=True):
    # The same build capability used by Blender's Cycles denoiser selector.
    try:
        import _cycles
        available=bool(getattr(_cycles,'with_openimagedenoise',False))
    except ImportError:
        available=False
    enabled=available and allow_denoising
    scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.use_denoising=enabled
    scene.cycles.samples=12 if enabled else 24
    if enabled:
        scene.cycles.denoiser='OPENIMAGEDENOISE'
        if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=False
    return {'revision':1,'engine':'CYCLES','device':'CPU',
            'denoiser':'OPENIMAGEDENOISE' if enabled else 'none',
            'samples':scene.cycles.samples,'oidn_build_support':available,
            'reason':'available' if enabled else 'denoising_unavailable', 'views_completed':[]}


def render_frame(scene, path, settings):
    path=Path(path);pending=path.with_name(path.stem+'.pending.png')
    pending.unlink(missing_ok=True)
    scene.render.filepath=str(pending)
    try:
        try:
            bpy.ops.render.render(write_still=True)
        except RuntimeError as error:
            message=str(error).lower()
            if not scene.cycles.use_denoising or 'failed to denoise' not in message or 'openimagedenoise' not in message or 'support' not in message:
                raise
            completed=settings['views_completed']
            settings.update(configure_review(scene,allow_denoising=False))
            settings.update(reason='oidn_runtime_unavailable',views_completed=completed)
            pending.unlink(missing_ok=True)
            bpy.ops.render.render(write_still=True)
        data=pending.read_bytes()
        if len(data)<45 or data[:8]!=b'\x89PNG\r\n\x1a\n' or data[-12:]!=b'\x00\x00\x00\x00IEND\xaeB`\x82':
            raise ValueError('Blender nie zapisal kompletnego podgladu PNG.')
        pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def render_review_checked(model,folder,asset_views=False):
    """Optional previews must never discard an already validated model export."""
    folder=Path(folder)
    try:
        return {'revision':1,'status':'rendered','views':render_review(model,folder,asset_views=asset_views)}
    except Exception as error:
        for label in (*LABELS,'side','back'):
            for suffix in ('.png','.pending.png'):
                (folder/(label+suffix)).unlink(missing_ok=True)
        return {'revision':1,'status':'unavailable','views':[],
                'detail':str(error)[:500],'likeness_verified':False}


def render_review(model,folder,asset_views=False):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    bpy.context.view_layer.update()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    low,high=geometry_bounds(meshes)
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
    settings=configure_review(scene)
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scale=max(span.z,span.x/0.8)*1.12
    face,face_scale,face_objects=face_framing(meshes)
    views = (
        ('front',(0,-4,.12),target,scale),
        ('three-quarter',(2,-4,.5),target,scale),
        ('side',(4,0,.12),target,max(span.z,span.y/0.8)*1.12),
        ('back',(0,4,.12),target,scale),
        ('face',(0,-3,0),face,face_scale))
    if asset_views:
        frame=max(span)*1.6
        distance=max(span)*3
        views=tuple((label,tuple(v*distance for v in direction),target,frame) for label,direction in (
            ('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('three-quarter',(.6,-1,.2))))
    for label,direction,aim,frame in views:
        camera.location=aim+Vector(direction)
        camera.rotation_euler=(aim-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=frame
        bpy.context.view_layer.update()
        evidence=frame_evidence(scene,camera,face_objects if label=='face' else meshes)
        if not evidence['framing_valid']:
            raise ValueError('Nieprawidlowy kadr '+label+': geometria poza obrazem.')
        render_frame(scene,folder/(label+'.png'),settings)
        settings['views_completed'].append({'label':label,'samples':scene.cycles.samples,
                                          'denoising':bool(scene.cycles.use_denoising),**evidence})
        (folder/'render-settings.json').write_text(json.dumps(settings),encoding='utf-8')
    return [str(folder/(view[0]+'.png')) for view in views]
