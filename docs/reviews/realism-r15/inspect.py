import bpy,bmesh,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
out=Path('/workspace/scratch/584c9d97a5a1/realism-r15');head=bpy.data.objects['anatomical-head'];bm=bmesh.new();bm.from_mesh(head.data);edges=set(e for e in bm.edges if e.is_boundary);components=[]
while edges:
 seed=edges.pop();group={seed};todo=[seed]
 while todo:
  e=todo.pop()
  for v in e.verts:
   for n in v.link_edges:
    if n in edges:edges.remove(n);group.add(n);todo.append(n)
 vs={v for e in group for v in e.verts};a=np.array([v.co for v in vs]);components.append({'edges':len(group),'min':a.min(0).tolist(),'max':a.max(0).tolist(),'centroid':a.mean(0).tolist(),'all_degree_two':all(sum(e in group for e in v.link_edges)==2 for v in vs)})
bm.free();tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons]);rays=[]
for y in [-.05,-.03,0,.04,.08,.12,.16]:
 p,n,_,_=tree.ray_cast(Vector((0,y,1.9)),Vector((0,0,-1)));rays.append({'y':y,'hit':list(p) if p else None})
locks=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name.startswith('R11_Reference_'):
  a=np.array([v.co for v in o.data.vertices]).reshape(-1,8,3);c=a.mean(1);rad=np.linalg.norm(a-c[:,None,:],axis=2).mean(1);locks.append({'name':o.name,'rings':len(a),'root':c[0].tolist(),'tip':c[-1].tolist(),'radius_mean':float(rad.mean()),'radius_max':float(rad.max())})
r={'boundary_components':components,'scalp_top_rays':rays,'locks_count':len(locks),'locks_examples':locks[:6]};(out/'inspection.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
