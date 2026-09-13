"""Reference-directed living-eye, smile and strand-normal experiment."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
OUT=Path('/workspace/scratch/584c9d97a5a1/model-repair')
def gaussian(value,centre,width):return math.exp(-.5*((value-centre)/width)**2)
def warp(point):
 x,y,z=point
 if x>=0 or y>.075 or z<1.43 or z>1.67:return point.copy()
 gate=min(1,-x/.027)*max(0,min(1,(.075-y)/.035))
 eye=gaussian(x,-.043,.036)*gaussian(z,1.578,.030)*gate
 dx=(-.010+(x+.043)*.17)*eye
 dz=(z-1.578)*.28*eye
 # Lift and widen the human mouth corner; open upper/lower lip around seam.
 smile=gaussian(x,-.028,.020)*gaussian(z,1.492,.023)*gate
 dx-=.006*smile
 dz+=.010*gaussian(x,-.033,.014)*gaussian(z,1.493,.020)*gate
 dz+=.0035*math.tanh((z-1.492)/.003)*smile
 cheek=gaussian(x,-.060,.027)*gaussian(z,1.536,.035)*gate
 return Vector((x+dx,y-.004*cheek,z+dz))
changed=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 if ob.get('anatomical_head') or ob.get('anatomical_eye') or any(n in ob.name.lower() for n in ('brow','lash','liner','living_smile')):
  inv=ob.matrix_world.inverted()
  for v in ob.data.vertices:v.co=inv@warp(ob.matrix_world@v.co)
  ob.data.update();changed.append(ob.name)
# Fine tangent-space strand relief survives GLB export as a normal texture.
n=1024;u=np.arange(n)[None,:]/n;v=np.arange(n)[:,None]/n
nx=.40*np.sin(math.tau*(u*155+.035*np.sin(v*25)))+.12*np.sin(math.tau*u*307)
ny=np.zeros((n,n));nz=np.sqrt(np.maximum(.01,1-nx*nx))
pixels=np.ones((n,n,4),np.float32);pixels[:,:,0]=nx*.5+.5;pixels[:,:,1]=ny+.5;pixels[:,:,2]=nz*.5+.5
im=bpy.data.images.new('Fine_strand_normal_1024',width=n,height=n,alpha=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(pixels.ravel());im.update();im.pack()
for mat in bpy.data.materials:
 if mat.name.startswith(('Repair_chestnut_hair','Chestnut hair variation')):
  bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.49;bs.inputs['Specular IOR Level'].default_value=.30
  tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
  normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45
  mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
bpy.context.scene['repair_revision']='direct-model-r6';bpy.context.scene['reference_likeness_accepted']=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-poprawka-r6.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-poprawka-r6.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
(OUT/'r6-execution.json').write_text(json.dumps({'changed_face_objects':changed,'likeness_accepted':False,'source':'r5 .blend','changes':['living eye/lid geometry moved together','human mouth corner lifted; lips separated','portable tangent strand texture'],'remaining':['likeness','hair realism','dental anatomy','garment construction']},indent=2))
print('REPAIR_R6_SAVED')
