"""Local print-copy supports for disconnected voxel-scale fragments.
Removes only shells for which every vertex has three odd parity ray tests inside
the main closed shell. Exterior fragments are thickened and bridged, not deleted.
"""
import bpy,bmesh,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_print_candidate import write_binary_stl,activate,world_bounds
root=Path('/workspace/scratch/584c9d97a5a1/e19/print')
source=root/'FORGE-E19-print-candidate-200mm.blend';before_sha=hashlib.sha256(source.read_bytes()).hexdigest()
data=np.load(root/'print-geometry.npz');v=data['vertices'];f=data['faces'];labels=np.load(root/'component-labels.npy');main_label=int(np.argmax(np.bincount(labels)));mainfaces=f[labels[f[:,0]]==main_label]
print('BVH_BEGIN',flush=True);tree=BVHTree.FromPolygons(v.tolist(),mainfaces.tolist(),all_triangles=True)
dirs=[Vector((1,.371,.227)).normalized(),Vector((.217,1,.463)).normalized(),Vector((.311,.173,1)).normalized()]
def inside(p):
 for d in dirs:
  origin=Vector(p);n=0
  for _ in range(3000):
   hit,normal,index,distance=tree.ray_cast(origin,d,1000)
   if hit is None:break
   n+=1;origin=hit+d*1e-5
  else:return False
  if n%2!=1:return False
 return True
removed=[];bridged=[];keep=labels==main_label;anchors=[]
for label in np.unique(labels):
 if label==main_label:continue
 ix=np.where(labels==label)[0];vv=v[ix]
 contained=all(inside(p) for p in vv)
 row={'component':int(label),'vertices':len(ix),'bounds_min_mm':vv.min(0).tolist(),'bounds_max_mm':vv.max(0).tolist()}
 if contained:row['reason']='Every vertex inside main shell, three independent parity rays each';removed.append(row);continue
 keep[ix]=True
 # Sample fragment at0.8mm spatial separation; thin retained tips get a printable
 # union support to the nearest main shell. Ends overlap the main solid.
 sample=[]
 for p in vv:
  if sample and min(np.linalg.norm(p-q) for q in sample)<.8:continue
  sample.append(p)
 for p in sample:
  loc,normal,index,distance=tree.find_nearest(Vector(p))
  if distance>12:raise RuntimeError('Unexpected distant part; manual anatomy review required')
  anchors.append((p, np.array(loc)-np.array(normal)*.8))
 row['support_samples']=len(sample);bridged.append(row)
print('COMPONENTS',len(removed),'inside',len(bridged),'external','SUPPORTS',len(anchors),flush=True)
# Rebuild retained mesh; no visual-scene changes.
bpy.ops.wm.read_factory_settings(use_empty=True)
keptfaces=f[keep[f[:,0]]];ids=np.where(keep)[0];remap=np.full(len(v),-1,dtype=np.int32);remap[ids]=np.arange(len(ids));mesh=bpy.data.meshes.new('Retained complete outer structure');mesh.from_pydata(v[ids].tolist(),[],remap[keptfaces].tolist());mesh.update();obj=bpy.data.objects.new('FORGE E19 supported print engineering candidate',mesh);bpy.context.collection.objects.link(obj);objects=[obj]
for p,q in anchors:
 direction=Vector(q)-Vector(p);mid=(Vector(q)+Vector(p))/2
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.65,location=p);objects.append(bpy.context.object)
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.65,depth=direction.length+1.1,location=mid)
 cyl=bpy.context.object;cyl.rotation_euler=direction.to_track_quat('Z','Y').to_euler();objects.append(cyl)
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.join();obj.data.remesh_voxel_size=.4;obj.data.use_remesh_preserve_volume=True;print('VOXEL_START',flush=True);bpy.ops.object.voxel_remesh();print('VOXEL_DONE',len(obj.data.polygons),flush=True)
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update();bpy.context.view_layer.update();low,high=world_bounds([obj]);scale=200/(high[2]-low[2]);
for point in obj.data.vertices:point.co.z-=float(low[2]);point.co*=scale
obj.data.update();bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
stem='FORGE-E19-print-candidate-200mm';stl=root/(stem+'.stl');write_binary_stl(obj,stl);bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
(root/'print-connection-repair.json').write_text(json.dumps({'source_blend_sha256':before_sha,'removed_proven_internal_shells':removed,'retained_and_supported_fragments':bridged,'supports_count':len(anchors),'support_radius_mm':.65,'final_voxel_mm':.4,'uniform_dimension_scale':scale,'manufacturing_ready':False,'minimum_thickness_and_intersections_unchecked':True,'final_stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()},indent=2)+'\n')
print('CONNECTION_REPAIR_DONE',flush=True)
