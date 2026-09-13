"""Connect retained shells with local triangular mesh bridges, preserving anatomy.
Engineering candidate only: smallest feature diameter and bridge intersections
are not certified. No anatomical/exterior component is removed.
"""
import bpy,bmesh,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_print_candidate import write_binary_stl
root=Path(__file__).resolve().parents[1]/'print';source=root/'FORGE-E19-print-candidate-200mm.blend';before=hashlib.sha256(source.read_bytes()).hexdigest();d=np.load(root/'print-geometry.npz');v=d['vertices'];f=d['faces'];labels=np.load(root/'component-labels.npy');main=int(np.argmax(np.bincount(labels)));mainids=np.where(labels[f[:,0]]==main)[0];tree=BVHTree.FromPolygons(v.tolist(),f[mainids].tolist(),all_triangles=True);removed=set();added=[];repairs=[]
for label in np.unique(labels):
 if label==main:continue
 faceids=np.where(labels[f[:,0]]==label)[0];best=None
 for faceid in faceids:
  point=v[f[faceid]].mean(0);hit,normal,j,distance=tree.find_nearest(Vector(point));mainid=int(mainids[j])
  if mainid in removed:
   hits=tree.find_nearest_range(Vector(point),max(distance+1.0,1.0));hits=sorted((h for h in hits if int(mainids[h[2]]) not in removed),key=lambda h:h[3])
   if not hits:continue
   hit,normal,j,distance=hits[0];mainid=int(mainids[j])
  if best is None or distance<best[0]:best=(distance,int(faceid),mainid)
 if best is None:raise RuntimeError('No unused local bridge patch')
 distance,smallface,mainface=best
 if distance>15:raise RuntimeError('Distant component requires manual anatomical review')
 a=f[mainface];b=f[smallface][::-1];candidates=[np.roll(b,k) for k in range(3)];b=min(candidates,key=lambda c:float(np.linalg.norm(v[a]-v[c],axis=1).sum()))
 for k in range(3):
  j=(k+1)%3;added.extend([[int(a[k]),int(a[j]),int(b[j])],[int(a[k]),int(b[j]),int(b[k])]])
 removed.update([mainface,smallface]);repairs.append({'component':int(label),'removed_patch_triangles':[mainface,smallface],'added_triangles':6,'nearest_surface_distance_mm':float(distance),'bridge_edge_lengths_mm':np.linalg.norm(v[a]-v[b],axis=1).tolist()})
keep=np.ones(len(f),dtype=bool);keep[list(removed)]=False;faces=np.concatenate([f[keep],np.asarray(added,dtype=np.int32)])
bpy.ops.wm.read_factory_settings(use_empty=True);mesh=bpy.data.meshes.new('Preserved anatomy with local print bridges');mesh.from_pydata(v.tolist(),[],faces.tolist());mesh.update();obj=bpy.data.objects.new('FORGE E19 connected print candidate',mesh);bpy.context.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update();bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
stl=root/'FORGE-E19-print-candidate-200mm.stl';write_binary_stl(obj,stl);bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
(root/'print-shell-stitching.json').write_text(json.dumps({'source_blend_sha256':before,'method':'Local triangular-prism surface bridges; every retained component preserved, no anatomical deletion','components_before':len(np.unique(labels)),'bridge_count':len(repairs),'bridge_details':repairs,'minimum_thickness_and_self_intersections_unchecked':True,'manufacturing_ready':False,'final_stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()},indent=2)+'\n')
print('STITCH_DONE',len(repairs),len(faces),flush=True)
