import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15'
ob=bpy.data.objects['anatomical-head'];bm=bmesh.new();bm.from_mesh(ob.data)
regions={
 'nose':[v for v in bm.verts if -.002<v.co.x<.032 and 1.474<v.co.z<1.532 and v.co.y<.041],
 'skeletal_mouth_corner':[v for v in bm.verts if .017<v.co.x<.081 and 1.430<v.co.z<1.475 and v.co.y<.038],
 'living_eyelid':[v for v in bm.verts if -.085<v.co.x<-.024 and 1.535<v.co.z<1.563 and v.co.y<.037 and v.is_boundary],
}
# Preserve topology and texture coordinates; locally relax only pinched vertices.
for name,vs in regions.items():
 for i in range(20 if name=='nose' else 12):
  bmesh.ops.smooth_vert(bm,verts=vs,factor=.42,use_axis_x=True,use_axis_y=True,use_axis_z=True)
# Smooth jagged skeletal upper-mouth edge along its own boundary adjacency.
vs=[v for v in bm.verts if v.is_boundary and 0<v.co.x<.09 and 1.428<v.co.z<1.48 and v.co.y<.04]
for _ in range(20):
 updates=[]
 for v in vs:
  ns=[e.other_vert(v) for e in v.link_edges if e.is_boundary]
  if len(ns)==2:updates.append((v,v.co.lerp((ns[0].co+ns[1].co)/2,.45)))
 for v,co in updates:v.co=co
bm.to_mesh(ob.data);bm.free();ob.data.update()
(OUT/'surface-polish-report.json').write_text(json.dumps({'vertices':{k:len(v) for k,v in regions.items()},'mouth_boundary_vertices':len(vs),'topology_preserved':True,'uv_preserved':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stage-polished.blend'),compress=True)
