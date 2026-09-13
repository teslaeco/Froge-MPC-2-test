"""Dense editable face master and portable FBX, approximately 1M triangles."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'face-repair';DEL=OUT/'delivery';DEL.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
head=bpy.data.objects['anatomical-head']
observed=bpy.data.materials.get('Reference_observed_face')
if observed:
 observed.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.20
 eye=bpy.data.objects.get('anatomical-eye-r')
 if eye:
  eye_mat=observed.copy();eye_mat.name='Observed_brown_eye'
  eye_mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.45
  eye_mat.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.12
  for i,mat in enumerate(eye.data.materials):
   if mat==observed:eye.data.materials[i]=eye_mat
for ob in bpy.context.scene.objects:
 if ob.name.startswith('Anatomical_upper_tooth_'):ob.location.z+=.002
def count(ob):
 me=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
 me.calc_loop_triangles();n=len(me.loop_triangles);ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear();return n
def hair_hash():
 h=hashlib.sha256()
 for ob in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  if ob.type=='MESH' and (ob.name.startswith('Reference_') or ob.name.startswith('Repair_fitted')):
   h.update(ob.name.encode());v=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',v);h.update(v.tobytes())
 return h.hexdigest()
before=hair_hash();others=sum(count(ob) for ob in bpy.context.scene.objects if ob.type=='MESH' and ob!=head)
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
# Densify only the face/scalp surface; the accepted hair is never modified.
sub=head.modifiers.new('Fine facial surface','SUBSURF');sub.levels=1;sub.render_levels=1
bpy.ops.object.modifier_apply(modifier=sub.name);dense=count(head)
ratio=min(1,max(.05,(1000000-others)/dense))
dec=head.modifiers.new('Face detail budget','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier=dec.name)
triangles=others+count(head)
assert before==hair_hash(),'Accepted hair changed'
for image in bpy.data.images:
 if image.has_data and not image.packed_file:image.pack()
bpy.context.scene['reference_likeness_accepted']=False
bpy.context.scene['repair_revision']='reference-face-r8-dense'
bpy.ops.wm.save_as_mainfile(filepath=str(DEL/'FORGE-model-1M.blend'))
bpy.ops.export_scene.gltf(filepath=str(DEL/'FORGE-model-1M.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'uv_order_changes':[],'baked_base_colors':[],'textures':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,DEL,report):
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.fbx(filepath=str(DEL/'FORGE-model-1M.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=triangles,head_triangles=count(head),other_triangles=others,hair_preserved=before==hair_hash(),hair_sha256=before,reference_likeness_accepted=False,fbx_reimport_verified=False)
(DEL/'export-report.json').write_text(json.dumps(report,indent=2));print('DENSE_FBX_SAVED',triangles,flush=True)
