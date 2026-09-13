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
   n+=1;origin=hit+d*.001
  else:return False
  if n%2!=1:return False
 return True
removed=[];external=[];keep=labels==main_label
for label in np.unique(labels):
 if label==main_label:continue
 ix=np.where(labels==label)[0];vv=v[ix]
 contained=all(inside(p) for p in vv)
 row={'component':int(label),'vertices':len(ix),'bounds_min_mm':vv.min(0).tolist(),'bounds_max_mm':vv.max(0).tolist()}
 if contained:row['reason']='Every vertex inside main shell, three parity rays each, 0.001mm ray advance';removed.append(row)
 else:keep[ix]=True;external.append(row)
print('PROVEN_INTERNAL',len(removed),'EXTERNAL_OR_UNCERTAIN',len(external),flush=True)
# Rebuild retained mesh; no visual-scene changes.
bpy.ops.wm.read_factory_settings(use_empty=True)
keptfaces=f[keep[f[:,0]]];ids=np.where(keep)[0];remap=np.full(len(v),-1,dtype=np.int32);remap[ids]=np.arange(len(ids));mesh=bpy.data.meshes.new('Retained complete outer structure');mesh.from_pydata(v[ids].tolist(),[],remap[keptfaces].tolist());mesh.update();obj=bpy.data.objects.new('FORGE E19 supported print engineering candidate',mesh);bpy.context.collection.objects.link(obj);objects=[obj]
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update();bpy.context.view_layer.update();low,high=world_bounds([obj]);scale=200/(high[2]-low[2]);
for point in obj.data.vertices:point.co.z-=float(low[2]);point.co*=scale
obj.data.update();bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
stem='FORGE-E19-print-candidate-200mm';stl=root/(stem+'.stl');write_binary_stl(obj,stl);bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
(root/'print-internal-shell-cleanup.json').write_text(json.dumps({'source_blend_sha256':before_sha,'removed_proven_internal_shells':removed,'retained_external_or_uncertain_shells':external,'manufacturing_ready':False,'minimum_thickness_and_intersections_unchecked':True,'final_stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()},indent=2)+'\n')
print('CLEANUP_DONE',flush=True)
