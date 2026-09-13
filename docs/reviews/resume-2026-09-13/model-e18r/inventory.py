import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path('/workspace/scratch/584c9d97a5a1')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public-resume/dist/assets/model.glb'))
items=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(p) for p in o.bound_box]
  items.append(dict(name=o.name,vertices=len(o.data.vertices),triangles=sum(len(p.vertices)-2 for p in o.data.polygons),min=[min(p[i] for p in pts) for i in range(3)],max=[max(p[i] for p in pts) for i in range(3)],materials=[m.name if m else None for m in o.data.materials]))
(R/'resume-model/inventory.json').write_text(json.dumps(items,indent=2))
print('OBJECTS',len(items),'TRIANGLES',sum(i['triangles'] for i in items))
print('BOUNDS', [min(i['min'][k] for i in items) for k in range(3)],[max(i['max'][k] for i in items) for k in range(3)])
for i in items:
 if any(s in i['name'].lower() for s in ('head','scalp','eye','tooth','neck','root','cap')): print(json.dumps(i))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'resume-model/source-recovered.blend'),compress=True)
