"""E15: restart from R14; preserve face/eyes, reduce inflated outer hair silhouette."""
import bpy,json,sys,hashlib
import numpy as np
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'correction-e15'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs

def fingerprint(ob):
 a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
 h=hashlib.sha256(a.tobytes()+np.array(ob.matrix_world).tobytes())
 for uv in ob.data.uv_layers:
  d=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',d);h.update(d.tobytes())
 return h.hexdigest()
protected=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith(('R11_Reference_','R12_root_','R12_asymmetric_scalp'))]
before={o.name:fingerprint(o) for o in protected};changed=[];bbefore=[];bafter=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith('R11_Reference_'):continue
 a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a);a=a.reshape(-1,8,3).astype(float);c=a.mean(axis=1);offset=a-c[:,None,:];old=a.copy();b_before=np.array([a.min(axis=(0,1)),a.max(axis=(0,1))]);bbefore.append(b_before)
 # Preserve strands crossing the forehead. Pull only the excessive outer envelope inward.
 x=c[:,0];upper=np.clip((c[:,2]-1.20)/.22,0,1);excess=np.maximum(abs(x)-.108,0);c[:,0]-=np.sign(x)*excess*.35*upper
 # Thinner existing guides; no new polygons and no global head deformation.
 a=c[:,None,:]+offset*.78
 ob.data.vertices.foreach_set('co',a.astype(np.float32).ravel());ob.data.update();bafter.append(np.array([a.min(axis=(0,1)),a.max(axis=(0,1))]));changed.append(ob.name)
 # Matte chestnut response retains the existing reference-led wave pattern.
 for m in ob.data.materials:
  if m and m.use_nodes:
   bs=m.node_tree.nodes.get('Principled BSDF')
   if bs:bs.inputs['Roughness'].default_value=.48;bs.inputs['Specular IOR Level'].default_value=.24
assert all(fingerprint(o)==before[o.name] for o in protected)
tri=0
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
report={'base':'R14; rejected R15 not used','triangles':tri,'head_geometry_and_uv_identical_to_r14':True,'all_non_hair_geometry_and_uv_identical_to_r14':True,'protected_meshes':len(protected),'protected_geometry_uv_sha256':before,'changed_hair_guides':len(changed),'hair_radius_factor':.78,'outer_hair_excess_compression':.35,'hair_bounds_before':[np.array(bbefore)[:,0,:].min(0).tolist(),np.array(bbefore)[:,1,:].max(0).tolist()],'hair_bounds_after':[np.array(bafter)[:,0,:].min(0).tolist(),np.array(bafter)[:,1,:].max(0).tolist()],'likeness_accepted':False,'meshy_comparison_source':'user screenshots only; no Meshy mesh available'}
bpy.context.scene['repair_revision']='E15-R14-likeness-restored'
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-E15.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-E15.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
portable={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _portable_uvs(bpy,portable),_portable_images(bpy,OUT,portable):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-E15.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report['portable']=portable;(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('E15_EXPORTED',tri,len(changed),flush=True)
