import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path('/workspace/scratch/584c9d97a5a1');OUT=ROOT/'realism-r15'
cap=bpy.data.objects.get('R15 scalp undercoat')
if cap:bpy.data.objects.remove(cap,do_unlink=True)
eye=bpy.data.objects['anatomical-eye-r'];c=eye.matrix_world.translation.copy()
for name in ['anatomical-eye-r','R15 living iris','R15 living pupil']:
 ob=bpy.data.objects[name];inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co
  if name!='anatomical-eye-r':w.x=c.x+(w.x-c.x)*1.22;w.z=c.z+(w.z-c.z)*1.22
  w.y+=.004
  v.co=inv@w
 ob.data.update()
for name in ['R14 dark brown recessed iris','R14 shaded orbital sclera']:
 m=bpy.data.materials.get(name)
 if m:
  bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.52;bs.inputs['Specular IOR Level'].default_value=.18
  if not bs.inputs['Base Color'].is_linked:
   col=bs.inputs['Base Color'].default_value;bs.inputs['Base Color'].default_value=(col[0]*.30,col[1]*.30,col[2]*.30,1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stage-refined.blend'),compress=True)
