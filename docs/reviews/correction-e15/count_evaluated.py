import bpy,json
from pathlib import Path
p=Path('/workspace/scratch/584c9d97a5a1/correction-e15/export-report.json');r=json.loads(p.read_text());n=0
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();n+=len(m.loop_triangles);ev.to_mesh_clear()
r['triangles']=n;r['count_method']='evaluated meshes including modifiers';p.write_text(json.dumps(r,indent=2));print('EVALUATED',n)
