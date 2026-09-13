import bpy,numpy as np
from pathlib import Path
root=Path('/workspace/scratch/584c9d97a5a1/e19/print')
bpy.ops.wm.open_mainfile(filepath=str(root/'FORGE-E19-print-candidate-200mm.blend'))
mesh=[o.data for o in bpy.context.scene.objects if o.type=='MESH'][0];mesh.calc_loop_triangles()
v=np.empty((len(mesh.vertices),3),dtype=np.float64);mesh.vertices.foreach_get('co',v.ravel())
f=np.empty((len(mesh.loop_triangles),3),dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',f.ravel())
np.savez(root/'print-geometry.npz',vertices=v,faces=f)
