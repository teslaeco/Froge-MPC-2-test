"""Bounded independent hair smoothing and base support experiment; not certified."""
import bpy,numpy as np,json,hashlib,sys,time
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=Path('/workspace/scratch/584c9d97a5a1');out=root/'e19/print-smooth';sys.path.insert(0,str(root/'e19/audit'))
from build_print_candidate import write_binary_stl,world_bounds,activate
start=time.monotonic();source=root/'e19/print/FORGE-E19-print-candidate-200mm.blend'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(root/'e19/final/FORGE-E19-web.glb'))
objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];low,high=world_bounds(objs);scale=196/(high[2]-low[2]);origin=np.array([(high[0]+low[0])/2,(high[1]+low[1])/2,low[2]])
# Source-to-print alignment is accurate to<0.1mm; protection margin is2mm.
def make_tree(objects):
 vv=[];ff=[]
 for obj in objects:
  mesh=obj.data;mesh.calc_loop_triangles();coords=np.empty((len(mesh.vertices),3));mesh.vertices.foreach_get('co',coords.ravel());mat=np.array(obj.matrix_world);coords=coords@mat[:3,:3].T+mat[:3,3];coords=(coords-origin)*scale;coords[:,2]+=4;offset=len(vv);vv.extend(coords.tolist());ff.extend([[offset+i for i in t.vertices] for t in mesh.loop_triangles])
 return BVHTree.FromPolygons(vv,ff,all_triangles=True)
hair=[o for o in objs if ('lock' in o.name.lower() or 'scalp' in o.name.lower()) and 'fibers' not in o.name.lower()];protected=[o for o in objs if ('anatomical' in o.name.lower() and not any(w in o.name.lower() for w in ['lash','hair'])) or any(w in o.name.lower() for w in ['shoulders_neck','tailored_split_gown','gathered_sleeve','upper_arm','tooth','tooth','oral','orbit','root bed'])]
print('TREES',len(hair),len(protected),flush=True);ht=make_tree(hair);pt=make_tree(protected)
bpy.ops.wm.open_mainfile(filepath=str(source));obj=[o for o in bpy.context.scene.objects if o.type=='MESH'][0];activate(obj);before=np.empty((len(obj.data.vertices),3));obj.data.vertices.foreach_get('co',before.ravel());group=obj.vertex_groups.new(name='Hair only, protected anatomy margin2mm');selected=[]
for i,point in enumerate(before):
 if point[2]<60:continue
 _,_,_,dh=ht.find_nearest(Vector(point),1.3)
 if dh is None:continue
 _,_,_,da=pt.find_nearest(Vector(point),2.0)
 if da is not None:continue
 selected.append(i)
group.add(selected,1.,'REPLACE');print('HAIR_MASK',len(selected),flush=True)
mod=obj.modifiers.new('Hair micro-surface smoothing only','SMOOTH');mod.factor=.32;mod.iterations=5;mod.vertex_group=group.name;bpy.ops.object.modifier_apply(modifier=mod.name);after=np.empty_like(before);obj.data.vertices.foreach_get('co',after.ravel());disp=np.linalg.norm(after-before,axis=1);mask=np.zeros(len(before),dtype=bool);mask[selected]=True;assert np.max(disp[~mask])<1e-8
# Broad central support reaches20mm inside the filled lower dress and overlaps
# the existing base by3mm, creating an alternative load path to the fingers.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=16,depth=36,location=(0,0,20));support=bpy.context.object;support.name='Trial central16mm radius body pedestal';activate(obj);union=obj.modifiers.new('Local body pedestal exact union','BOOLEAN');union.operation='UNION';union.solver='EXACT';union.object=support
print('BOOLEAN_START',time.monotonic()-start,flush=True);bpy.ops.object.modifier_apply(modifier=union.name);bpy.data.objects.remove(support,do_unlink=True);print('BOOLEAN_DONE',time.monotonic()-start,flush=True)
for face in obj.data.polygons:face.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(out/'FORGE-E19-smooth-support-trial.blend'),compress=True);write_binary_stl(obj,out/'FORGE-E19-smooth-support-trial.stl');obj.scale=(.001,)*3;bpy.ops.export_scene.gltf(filepath=str(out/'FORGE-E19-smooth-support-trial.glb'),export_format='GLB',use_selection=True,export_materials='NONE',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=30,export_draco_normal_quantization=16)
(out/'trial-report.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'hair_vertices_smoothed':len(selected),'maximum_hair_displacement_mm':float(disp.max()),'maximum_protected_vertex_displacement_mm':float(disp[~mask].max()),'protected_margin_mm':2,'pedestal_radius_mm':16,'pedestal_z_range_mm':[2,38],'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-start},indent=2)+'\n');print('TRIAL_DONE',flush=True)
