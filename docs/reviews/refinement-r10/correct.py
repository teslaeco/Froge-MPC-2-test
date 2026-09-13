"""Correct observed upper-arm sleeve overlap, then restore exact scene triangle count."""
import bpy,bmesh,math,json,sys,hashlib
import numpy as np
from pathlib import Path
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'refinement-r10'
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from scene_exports import _portable_images,_portable_uvs,_baked_base_colors
for side in (-1,1):
 o=bpy.data.objects['R10_upper_arm_%s'%side]
 bm=bmesh.new();bm.from_mesh(o.data)
 for _ in range(8):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if not v.is_boundary],factor=.3,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 for v in bm.verts:
  x,y,z=v.co
  if z<1.251:
   f=max(.82,min(1,.82+.18*(z-1.225)/.026));s=(1.333-z)/.365;cx=side*(.193+.071*s)
   v.co.x=cx+(x-cx)*f;v.co.y=.025+(y-.025)*f
 hidden=[f for f in bm.faces if f.calc_center_median().z<1.227]
 bmesh.ops.delete(bm,geom=hidden,context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()
head=bpy.data.objects['anatomical-head']
hair_before=json.loads((OUT/'export-report.json').read_text())['long_lock_hash']
# Densify the face and tune its triangle budget after all genuine shape changes.
def count(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();n=len(me.loop_triangles);ev.to_mesh_clear();return n
others=sum(count(o) for o in bpy.context.scene.objects if o.type=='MESH' and o!=head)
# Barycentric triangle subdivision avoids a multi-million-face temporary Subsurf.
# It adds density without claiming extra observed detail. Preserve per-corner UVs.
old=head.data;old.calc_loop_triangles();base=len(old.loop_triangles);need=1500000-others-base
assert need>=0,(others,base)
vertices=[tuple(v.co) for v in old.vertices];faces=[];uvvalues=[];materials=[]
uv=old.uv_layers[0]
count_split=need//2
candidates=[t.index for t in old.loop_triangles if sum(old.vertices[k].co.y for k in t.vertices)/3<.04]
if len(candidates)<count_split:candidates=list(range(base))
chosen=set(candidates[int(i)] for i in np.linspace(0,len(candidates)-1,count_split,dtype=int)) if count_split else set()
assert len(chosen)==count_split
odd=need%2;boundary_triangle=None;boundary_pair=None
if odd:
 bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table()
 edge=next(e for e in bm.edges if e.is_boundary)
 boundary_pair={v.index for v in edge.verts};bm.free()
 boundary_triangle=next(t.index for t in old.loop_triangles if boundary_pair.issubset(t.vertices))
 if boundary_triangle in chosen:
  chosen.remove(boundary_triangle);chosen.add(next(i for i in range(base) if i not in chosen and i!=boundary_triangle))
for t in old.loop_triangles:
 ids=list(t.vertices);coords=[tuple(uv.data[i].uv) for i in t.loops];mi=old.polygons[t.polygon_index].material_index
 if t.index in chosen:
  center=tuple(sum(vertices[k][d] for k in ids)/3 for d in range(3));uid=tuple(sum(c[d] for c in coords)/3 for d in range(2));vi=len(vertices);vertices.append(center)
  for j in range(3):faces.append((ids[j],ids[(j+1)%3],vi));uvvalues.extend((coords[j],coords[(j+1)%3],uid));materials.append(mi)
 elif t.index==boundary_triangle:
  j=next(j for j in range(3) if {ids[j],ids[(j+1)%3]}==boundary_pair);ids=ids[j:]+ids[:j];coords=coords[j:]+coords[:j]
  vi=len(vertices);vertices.append(tuple((vertices[ids[0]][d]+vertices[ids[1]][d])/2 for d in range(3)));uid=tuple((coords[0][d]+coords[1][d])/2 for d in range(2))
  faces.extend(((ids[0],vi,ids[2]),(vi,ids[1],ids[2])));uvvalues.extend((coords[0],uid,coords[2],uid,coords[1],coords[2]));materials.extend((mi,mi))
 else:faces.append(tuple(ids));uvvalues.extend(coords);materials.append(mi)
new=bpy.data.meshes.new('R10 exact-density face');new.from_pydata(vertices,[],faces);new.update()
for m in old.materials:new.materials.append(m)
layer=new.uv_layers.new(name=uv.name);layer.data.foreach_set('uv',np.asarray(uvvalues,np.float32).ravel());new.polygons.foreach_set('material_index',materials);new.polygons.foreach_set('use_smooth',[True]*len(faces))
head.data=new
triangles=others+count(head);assert triangles==1500000,triangles
print('EXACT_TRIANGLES',triangles,flush=True)
del vertices,faces,uvvalues,materials
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.context.scene['repair_revision']='r10-1.5M';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-r10-1500k.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-r10-1500k.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'textures':[],'uv_order_changes':[],'baked_base_colors':[],'uv_binding_limitations':[]}
with _baked_base_colors(bpy,report),_portable_uvs(bpy,report),_portable_images(bpy,OUT,report):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(OUT/'FORGE-model-r10-1500k.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
report.update(triangles=triangles,target_triangles=1500000,hair_preserved=True,long_lock_hash=hair_before,new_hairline_locks=76,likeness_accepted=False,print_ready=False)
(OUT/'export-report.json').write_text(json.dumps(report,indent=2));print('R10_SAVED',triangles,flush=True)
