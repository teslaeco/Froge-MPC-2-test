import bpy,json,numpy as np
from mathutils import Vector
r=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and (any(x in o.name.lower() for x in ['eye','tooth','cavity','orbit','neck']) or o.name=='anatomical-head'):
  a=np.array([o.matrix_world@v.co for v in o.data.vertices]);r.append({'name':o.name,'n':len(a),'min':a.min(0).tolist(),'max':a.max(0).tolist(),'location':list(o.location),'scale':list(o.scale),'materials':[m.name if m else None for m in o.data.materials]})
open('/workspace/scratch/584c9d97a5a1/anatomy-r14/geometry-before.json','w').write(json.dumps(r,indent=2));print(json.dumps(r))
