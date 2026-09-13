import bpy, math, random, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1'); OUT=ROOT/'resume-model'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'source-recovered.blend'))
rng=random.Random(13092026)
scalp=bpy.data.objects['R12_asymmetric_scalp']; head=bpy.data.objects['anatomical-head']
removed_front=bpy.data.objects.get('E18 swept frontal individual hair')
removed_triangles=sum(len(p.vertices)-2 for p in removed_front.data.polygons)
bpy.data.objects.remove(removed_front,do_unlink=True)
before={o.name:(len(o.data.vertices),sum(len(p.vertices)-2 for p in o.data.polygons)) for o in bpy.context.scene.objects if o.type=='MESH'}
# Avoid changing shared hair material: darker root substrate only on the scalp.
for i,m in enumerate(list(scalp.data.materials)):
 n=m.copy();n.name='E18R root substrate '+str(i)
 bs=n.node_tree.nodes.get('Principled BSDF')
 if bs:
  c=list(bs.inputs['Base Color'].default_value)
  for k in range(3):c[k]*=.58 if i==0 else .72
  bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.67
 scalp.data.materials[i]=n

# Repair a portable material issue recovered in the web GLB: white full-strength sheen
# overwhelms the genuinely dark cloth BaseColor in Blender's glTF import.
cloth=bpy.data.materials.get('R13 black fine twill')
if cloth:
 bs=cloth.node_tree.nodes.get('Principled BSDF')
 if bs:
  bs.inputs['Sheen Weight'].default_value=.15
  bs.inputs['Sheen Tint'].default_value=(.07,.08,.10,1)

def surf(x,z):
 ys=[]
 for o in [scalp,head]:
  ok,p,n,face=o.ray_cast(o.matrix_world.inverted()@Vector((x,-.5,z)),Vector((0,1,0)))
  if ok:ys.append((o.matrix_world@p).y)
 return min(ys) if ys else None
verts=[]; faces=[]; mids=[]; vertex_uvs=[]
# True tapered meshes on the frontal surface, a restrained geometric root correction.
for side in (-1,1):
 for i in range(480):
  sx=rng.uniform(.0005,.006); startz=rng.uniform(1.658,1.697)
  endx=rng.uniform(.075,.099); endz=rng.uniform(1.609,1.65) if side<0 else rng.uniform(1.625,1.661)
  endz=min(endz,startz-.018)
  radius=rng.uniform(.00010,.00023);phase=rng.random()*math.tau
  points=[]
  for k in range(46):
   t=k/45; x=side*(sx+(endx-sx)*t + .0005*math.sin(t*math.pi*2+phase)*math.sin(math.pi*t))
   z=startz-(startz-endz)*(t**.8)+.0007*math.sin(t*math.pi*3+phase)*math.sin(math.pi*t)
   y=surf(x,z)
   if y is None or y>.115:continue
   lift=.0007+.0070*math.sin(math.pi*t)*(0.65+0.35*math.sin(phase+t*3)**2)
   points.append((Vector((x,y-lift,z)),t))
  if len(points)<12:continue
  start=len(verts);count=len(points);sidecount=5
  for k,(p,t) in enumerate(points):
   tangent=(points[min(k+1,count-1)][0]-points[max(0,k-1)][0]).normalized()
   u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
   rad=radius*(.18+.82*(math.sin(math.pi*min(.999,max(.001,t)))**.28))
   for j in range(sidecount):
    a=j*math.tau/sidecount; verts.append(p+rad*(math.cos(a)*u+math.sin(a)*v));vertex_uvs.append((j/sidecount,t))
  matindex=rng.randrange(6)+(6 if side>0 else 0)
  for k in range(count-1):
   for j in range(sidecount):
    a=start+k*sidecount+j;b=start+k*sidecount+(j+1)%sidecount;c=start+(k+1)*sidecount+(j+1)%sidecount;d=start+(k+1)*sidecount+j
    faces.extend([(a,b,c),(a,c,d)]);mids.extend([matindex]*2)
  faces.append(tuple(start+j for j in range(sidecount-1,-1,-1)));mids.append(matindex)
  faces.append(tuple(start+(count-1)*sidecount+j for j in range(sidecount)));mids.append(matindex)
mesh=bpy.data.meshes.new('E18R true swept root fibers mesh');mesh.from_pydata(verts,[],faces);mesh.update()
uv=mesh.uv_layers.new(name='Root fibers UV')
for loop in mesh.loops:uv.data[loop.index].uv=vertex_uvs[loop.vertex_index]
obj=bpy.data.objects.new('E18R 960 tapered hairline fibers',mesh);bpy.context.collection.objects.link(obj)
for side in ('chestnut','aged silver'):
 for j in range(6):obj.data.materials.append(bpy.data.materials[f'E17 {side} {j}'])
for p,i in zip(mesh.polygons,mids):p.material_index=i;p.use_smooth=True
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
# Preserve head/skull/eyes/neck geometry exactly. No reconstruction claim for unedited parts.
for name,(vc,tc) in before.items():
 o=bpy.data.objects.get(name)
 assert len(o.data.vertices)==vc
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-E18R-recovered-checkpoint.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-E18R.glb'),export_format='GLB',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_apply=True)
stats={'source':'Recovered E18 public web GLB, not original master','source_sha256':hashlib.sha256((ROOT/'public-resume/dist/assets/model.glb').read_bytes()).hexdigest(),'source_triangles':sum(v[1] for v in before.values())+removed_triangles,'removed_flat_root_triangles':removed_triangles,'added_vertices':len(mesh.vertices),'added_triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'targeted_change':'Replace old flat frontal root layer with 960 raised tapered fibers and separate darker scalp substrate; global head/eyes/neck dimensions unchanged','changed_original_geometry':'Removed old hairline mesh only; anatomical meshes untouched','texture_note':'Only recovered web image resolutions; no fabricated restored 4K master','material_fix':'R13 black fine twill: sheen weight .15 and tint [.07,.08,.10]; retain actual dark BaseColor map','artifact_sha256':hashlib.sha256((OUT/'FORGE-E18R.glb').read_bytes()).hexdigest()}
stats['total_triangles']=stats['source_triangles']-removed_triangles+stats['added_triangles'];(OUT/'correction-report.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats))
