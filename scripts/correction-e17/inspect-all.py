import bpy,json
from pathlib import Path
out=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  a=[o.matrix_world@v.co for v in o.data.vertices];out.append({'name':o.name,'n':len(a),'bounds':[[min(v[i] for v in a) for i in range(3)],[max(v[i] for v in a) for i in range(3)]],'mats':[m.name for m in o.data.materials if m]})
Path('/workspace/scratch/584c9d97a5a1/correction-e17/all.json').write_text(json.dumps(out))
