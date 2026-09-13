"""Reference-landmark geometry and observed face texture; r6 hair preserved."""
import bpy,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1')
OUT=ROOT/'face-repair';OUT.mkdir(exist_ok=True)
reference=ROOT/'upload/Screenshot_20260912-131922.png'
head=bpy.data.objects['anatomical-head']
def hair_identity():
 h=hashlib.sha256()
 for ob in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  if ob.type=='MESH' and (ob.name.startswith('Reference_') or ob.name.startswith('Repair_fitted')):
   h.update(ob.name.encode());v=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',v);h.update(v.tobytes())
 return h.hexdigest()
hair_before=hair_identity()
# Manually observed correspondences: existing front render pixels -> source pixels.
# These are fitting constraints, not independent proof of exact identity.
matches=[
 ((320,201),(490,325)),((186,244),(352,410)),((450,238),(598,393)),
 ((180,303),(337,466)),((223,280),(381,454)),((285,289),(428,464)),
 ((191,340),(337,506)),((226,329),(380,488)),((266,343),(427,506)),
 ((226,357),(382,523)),((227,342),(383,506)),
 ((300,394),(451,555)),((296,432),(437,596)),((314,429),(461,600)),
 ((320,459),(465,638)),((257,465),(384,644)),
 ((286,479),(421,647)),((319,495),(465,657)),
 ((289,518),(433,692)),((319,530),(465,701)),((267,493),(400,677)),
 ((171,388),(311,555)),((188,470),(329,638)),((220,539),(375,707)),
 ((273,580),(419,746)),((320,597),(462,760)),
 ((350,345),(494,503)),((400,303),(544,465)),((445,348),(589,509)),
 ((404,394),(549,550)),((473,407),(615,560)),
 ((486,538),(583,654)),((429,575),(536,717)),
 ((374,490),(520,668)),((380,522),(517,689)),
 ((335,438),(477,602)),((320,390),(473,547)),
]
def source_world(p):return ((p[0]-320)*.448490095/800,1.54626417+(400-p[1])*.448490095/800)
def target_world(p):
 seam=490-(p[1]-240)*28/520
 return ((p[0]-seam)*.00064,1.8856-p[1]*.0006)
src=np.array([source_world(a) for a,b in matches]);dst=np.array([target_world(b) for a,b in matches])
# Keep the existing accepted hairline and scalp contact fixed.
dst[:3]=src[:3]
pins=np.array([(-.13,1.69),(0,1.73),(.13,1.69),(-.11,1.40),(0,1.40),(.11,1.40),(-.15,1.57),(.15,1.57)])
class Warp:
 def __init__(self,points,values):
  self.origin=points.mean(axis=0);self.points=(points-self.origin)/.1
  delta=self.points[:,None,:]-self.points[None,:,:];r2=(delta*delta).sum(2)
  kernel=.5*r2*np.log(np.maximum(r2,1e-14));kernel+=np.eye(len(points))*1e-5
  p=np.column_stack([np.ones(len(points)),self.points])
  lhs=np.block([[kernel,p],[p.T,np.zeros((3,3))]])
  self.weights=np.linalg.solve(lhs,np.vstack([values,np.zeros((3,values.shape[1]))]))
 def evaluate(self,points):
  outputs=[]
  for part in np.array_split(points,max(1,math.ceil(len(points)/4096))):
   q=(part-self.origin)/.1;delta=q[:,None,:]-self.points[None,:,:];r2=(delta*delta).sum(2)
   kernel=.5*r2*np.log(np.maximum(r2,1e-14))
   outputs.append(np.column_stack([kernel,np.ones(len(q)),q])@self.weights)
  return np.concatenate(outputs)
deformation=Warp(np.vstack([src,pins]),np.vstack([dst-src,np.zeros_like(pins)]))
uvfit=Warp(dst,np.array([b for a,b in matches],float))
photo=bpy.data.images.load(str(reference),check_existing=True);photo.name='Observed_original_face';photo.pack()
def material(name,rgb,rough=.75):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*rgb,1);s.inputs['Roughness'].default_value=rough
 return m
observed=material('Reference_observed_face',(.5,.3,.2));bs=observed.node_tree.nodes.get('Principled BSDF')
tex=observed.node_tree.nodes.new('ShaderNodeTexImage');tex.image=photo;tex.extension='EXTEND'
observed.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
observed['source_photo_sha256']=hashlib.sha256(reference.read_bytes()).hexdigest();observed['reference_lighting_removed']=False
selected=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 if ob.get('anatomical_head') or ob.get('anatomical_eye') or any(s in ob.name.lower() for s in ('brow','lash','liner','orbit','nasal','mandible','zygomatic')):
  selected.append(ob)
  raw=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',raw);xyz=raw.reshape(-1,3).astype(float)
  matrix=np.array(ob.matrix_world);world=xyz@matrix[:3,:3].T+matrix[:3,3]
  dxz=deformation.evaluate(world[:,[0,2]])
  front=np.clip((.075-world[:,1])/.035,0,1);height=np.clip((world[:,2]-1.39)/.055,0,1)*np.clip((1.73-world[:,2])/.035,0,1)
  world[:,[0,2]]+=dxz*(front*height)[:,None]
  inv=np.linalg.inv(matrix);xyz=world@inv[:3,:3].T+inv[:3,3]
  ob.data.vertices.foreach_set('co',xyz.astype(np.float32).ravel());ob.data.update()
  ob['reference_landmark_fit']='observed frontal landmarks; hidden depth inferred'
# Apply dense subdivision before editing the mouth boundary and UV projection.
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
for mod in list(head.modifiers):
 if mod.type=='SUBSURF':mod.levels=2;mod.render_levels=2
 bpy.ops.object.modifier_apply(modifier=mod.name)

def inside(p,polygon):
 x,y=p;hit=False
 for a,b in zip(polygon,polygon[1:]+polygon[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
mouth=[(389,650),(416,650),(466,658),(466,687),(436,685),(407,674)]
# The smile is an actual opening, with teeth behind it. No tooth-painted plane.
import bmesh
bm=bmesh.new();bm.from_mesh(head.data);faces=list(bm.faces)
centres=np.array([f.calc_center_median()[:] for f in faces]);pixels=uvfit.evaluate(centres[:,[0,2]])
remove=[f for f,p,c in zip(faces,pixels,centres) if c[0]<0 and c[1]<.015 and inside(p,mouth)]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(head.data);bm.free();head.data.update()
print('SMILE_OPENING_FACES',len(remove),flush=True)
# Project only observed front-facing facial surfaces; retain original back UVs.
mapped={}
for ob in selected:
 if any(s in ob.name.lower() for s in ('brow','lash','liner','recessed','nasal')):continue
 vertices=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);pixels=uvfit.evaluate(vertices[:,[0,2]])
 layer=ob.data.uv_layers[0] if ob.data.uv_layers else ob.data.uv_layers.new(name='UVMap');ob.data.uv_layers.active_index=0;layer.active_render=True
 ob.data.materials.append(observed);idx=len(ob.data.materials)-1;count=0
 for face in ob.data.polygons:
  ids=list(face.vertices);p=pixels[ids].mean(0);c=vertices[ids].mean(0)
  # Photo skin/bone are used only within the observed face, not hair/background.
  contour=[(490,318),(418,345),(349,433),(316,516),(303,580),(326,659),(380,718),(461,768),(538,734),(591,666),(632,581),(641,474),(611,375),(546,307)]
  normal=ob.matrix_world.to_3x3().inverted().transposed()@face.normal
  if c[1]>.03 or normal.y>-.18 or not inside(p,contour):continue
  face.material_index=idx;count+=1
  for li in face.loop_indices:
   v=pixels[ob.data.loops[li].vertex_index];layer.data[li].uv=(v[0]/899,1-v[1]/2048)
 mapped[ob.name]=count

# New continuous dental arches: rounded incisors, smaller lateral teeth/canines.
for ob in list(bpy.context.scene.objects):
 if 'tooth' in ob.name.lower():bpy.data.objects.remove(ob,do_unlink=True)
enamel=material('Natural ivory enamel',(.40,.35,.25),.42);dark=material('Mouth interior',(.034,.009,.006),.92)
def tooth(name,x,y,z,width,height,depth,angle=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z));ob=bpy.context.object;ob.name=name;ob.scale=(width,depth,height)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bevel=ob.modifiers.new('Rounded enamel','BEVEL');bevel.width=min(width,height)*.19;bevel.segments=3
 ob.rotation_euler.z=angle;ob.data.materials.append(enamel)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
for side in (-1,1):
 cursor=0
 for j,w in enumerate((.0087,.0074,.0068,.0062,.0060,.0056)):
  x=side*(cursor+w*.5);cursor+=w*.97
  y=-.031+.037*(abs(x)/.06)**1.7
  z=1.486+.008*(abs(x)/.05)**1.5
  tooth('Anatomical_upper_tooth_%s_%s'%(side,j),x,y,z,w*.94,.0088 if j<2 else .0098 if j==2 else .007,.008,side*.7*(abs(x)/.06))
  if side>0:tooth('Anatomical_lower_tooth_%s'%j,x,y+.0005,z-.009,w*.87,.006,.007,side*.7*(abs(x)/.06))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(0,.020,1.484))
oral=bpy.context.object;oral.name='Recessed oral cavity';oral.scale=(.052,.025,.023);oral.data.materials.append(dark)

# Remove the old, mismatched brow overlay: the observed brow is registered.
for ob in list(bpy.context.scene.objects):
 if ob.name=='eyebrow-fibres':bpy.data.objects.remove(ob,do_unlink=True)
arch=bpy.data.objects.get('Zygomatic_arch')
if arch:
 for v in arch.data.vertices:v.co.x*=.91;v.co.y+=.016
# Keep the source scene editable and preserve its accepted hair exactly.
assert hair_before==hair_identity(),'Accepted hair geometry changed'
for image in bpy.data.images:
 if image.has_data and not image.packed_file:image.pack()
bpy.context.scene['reference_likeness_accepted']=False;bpy.context.scene['repair_revision']='r8-reference-fit'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-twarz-r8.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-twarz-r8.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
report={'revision':'r8','hair_sha256_before':hair_before,'hair_sha256_after':hair_identity(),'hair_preserved':True,'reference_landmarks':len(matches),'removed_mouth_faces':len(remove),'mapped_front_faces':mapped,'reference_lighting_removed':False,'unseen_depth':'inferred','likeness_accepted':False,'landmarks':matches,'geometry_source_anchors':src.tolist(),'geometry_target_anchors':dst.tolist()}
(OUT/'face-fit-report.json').write_text(json.dumps(report,indent=2));print('R8_FACE_SAVED',flush=True)
