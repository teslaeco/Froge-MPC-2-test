"""Native Blender regression: baked eye origins and measured rooted UV hair volumes."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent/'runtime'))
from review_views import face_framing,geometry_bounds,frame_evidence
from rooted_hair import hair_lock,hair_root_attachment_evidence
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=24,location=(.4,.2,3))
head=bpy.context.object;head.scale=(.15,.13,.21);head['anatomical_head']=True
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=12,location=(.35,.06,3.04),radius=.014)
eye=bpy.context.object;eye['anatomical_eye']=True
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()
centre,scale,selected=face_framing([head,eye])
assert abs(centre.z-3)<.001 and abs(centre.x-.4)<.001
assert eye.matrix_world.translation.length==0
# Deliberately empty eye sockets must still frame the full head.
centre2,scale2,_=face_framing([head]);assert (centre2-centre).length<1e-6
scene=bpy.context.scene;scene.render.resolution_x=640;scene.render.resolution_y=800
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=scale;scene.camera=camera
camera.location=centre+Vector((0,-3,0));camera.rotation_euler=(centre-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update();assert frame_evidence(scene,camera,[head])['framing_valid']
camera.location=Vector((0,-3,0));camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update();assert not frame_evidence(scene,camera,[head])['framing_valid']
mat=bpy.data.materials.new('Hair')
lock=hair_lock('Root test',head,[(.4,.2,3.21),(.54,.2,3.10),(.59,.18,2.80),(.57,.13,2.55)],mat,seed=22)
bm=bmesh.new();bm.from_mesh(lock.data)
assert all(edge.is_manifold for edge in bm.edges), 'Hair volume must be closed'
assert all(face.calc_area()>1e-12 for face in bm.faces)
bm.free();assert lock.data.uv_layers
assert abs(Vector(lock['hair_root_world']).z-3.21)<.003
attachment=hair_root_attachment_evidence(lock,head)
assert attachment['assessed'] and attachment['passed'], attachment
assert attachment['likeness_assessed'] is False
# The same valid mesh moved away from the head must be detected as detached.
old_hair_matrix=lock.matrix_world.copy()
lock.matrix_world=Matrix.Translation((0,0,.6))@old_hair_matrix
bpy.context.view_layer.update()
detached=hair_root_attachment_evidence(lock,head)
assert detached['assessed'] and not detached['passed'], detached
assert detached['root_centre_gap']>attachment['root_centre_gap']
lock.matrix_world=old_hair_matrix
bpy.context.view_layer.update()
# Moving an origin while preserving geometry must not alter framing.
old=head.matrix_world.copy();head.matrix_world=Matrix.Translation((8,2,-4))
for v in head.data.vertices:v.co=head.matrix_world.inverted()@old@v.co
bpy.context.view_layer.update();new,_,_=face_framing([head]);assert (new-centre).length<1e-5
print('CAMERA_HAIR_NATIVE_PASS',json.dumps({'face_center':list(centre),'face_scale':scale,'hair_vertices':len(lock.data.vertices),'closed':True,'root_attachment':attachment,'detached_control':detached,'empty_old_frame_rejected':True}))
