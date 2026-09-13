import bpy,json,bmesh
from pathlib import Path
from mathutils import Vector
P=Path('/workspace/scratch/584c9d97a5a1/correction-e16')
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 if o.name.startswith(('R11_Reference_','R12_root_')):continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 rows.append({'name':o.name,'verts':len(vs),'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'materials':[m.name if m else '' for m in o.data.materials]})
(P/'objects.json').write_text(json.dumps(rows,indent=2))
head=bpy.data.objects['anatomical-head'];bm=bmesh.new();bm.from_mesh(head.data);edges=set(e for e in bm.edges if e.is_boundary);groups=[]
while edges:
 seed=edges.pop();group={seed};todo=[seed]
 while todo:
  e=todo.pop()
  for v in e.verts:
   for n in v.link_edges:
    if n in edges:edges.remove(n);group.add(n);todo.append(n)
 vs={v for e in group for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs);groups.append({'count':len(vs),'center':list(c),'bounds':[[min(v.co[i] for v in vs) for i in range(3)],[max(v.co[i] for v in vs) for i in range(3)]],'degree2':all(sum(e in group for e in v.link_edges)==2 for v in vs)})
(P/'boundaries.json').write_text(json.dumps(groups,indent=2));bm.free()
ims=[]
for im in bpy.data.images:
 if im.has_data:
  ims.append({'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)})
  if im.name=='R13 latest supplied reference':im.save_render(str(P/'reference.png'))
(P/'images.json').write_text(json.dumps(ims,indent=2))
print('INSPECTED',len(rows),len(groups),flush=True)
