"""Actual r3 model repair using the generator's new rooted-hair helper."""
import sys,math,json,random,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path('/workspace/scratch/584c9d97a5a1')
sys.path.insert(0,str(ROOT/'forge-worker/oracle_connector/runtime'))
from rooted_hair import hair_lock
OUT=ROOT/'model-repair'
head=bpy.data.objects['anatomical-head']
mat=bpy.data.objects['Repair_continuous_back_hair'].data.materials[0]
for ob in list(bpy.context.scene.objects):
 if ob.name.startswith(('Repair_wave_','Repair_continuous_back_hair')):bpy.data.objects.remove(ob,do_unlink=True)
cap=bpy.data.objects.get('Repair_fitted_scalp')
if cap:
 mod=cap.modifiers.new('Smooth fitted hairline','SUBSURF');mod.levels=2
# Slight colour variation between large locks, retaining packed strand albedo.
mats=[mat]
for j in range(2):
 m=mat.copy();m.name='Chestnut hair variation '+str(j)
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.55+j*.06
 mats.append(m)
rng=random.Random(440)
# Overlapping spatial locks replace the continuous rear sheet.
for j in range(64):
 a=-1.78+3.56*(j+.5)/64
 end=1.02+rng.uniform(-.10,.09)+.09*abs(math.sin(a))
 r=.145+rng.uniform(-.008,.014)
 points=[(.045*math.sin(a),.068+.038*math.cos(a),1.713+rng.uniform(-.008,.006)),
         (.100*math.sin(a),.068+.103*math.cos(a),1.655),
         (r*math.sin(a),.068+r*.88*math.cos(a),1.545),
         ((r+.020)*math.sin(a),.085+(r+.022)*math.cos(a),1.36),
         ((r+.012)*math.sin(a),.078+(r+.015)*math.cos(a),1.20),
         ((r-.010)*math.sin(a),.070+(r+.004)*math.cos(a),end)]
 hair_lock('Reference_back_lock_%02d'%j,head,points,mats[j%3],width=rng.uniform(.009,.014),depth=rng.uniform(.010,.016),wave=rng.uniform(.008,.018),turns=rng.uniform(1.3,2.5),seed=440+j,steps=90)
# Individual front locks fill different depths, not a stack of ribbons.
for side in (-1,1):
 for j in range(20):
  layer=j%4;spread=j//4
  end=(.98 if side<0 else 1.14)+rng.uniform(-.075,.07)
  x=.115+.009*spread;y=.008+.012*layer
  points=[(side*(.006+.010*spread),.044+.012*layer,1.714-.007*spread),
          (side*(.067+.012*spread),.024+.012*layer,1.669-.004*spread),
          (side*x,y,1.575),
          (side*(x+.025),-.035+.011*layer,1.45),
          (side*(x+.035),-.089+.009*layer,1.30),
          (side*(x+.005),-.122+.01*layer,1.17),
          (side*(x+.017),-.124+.01*layer,end)]
  hair_lock('Reference_front_lock_%s_%02d'%(side,j),head,points,mats[j%3],width=rng.uniform(.009,.014),depth=rng.uniform(.010,.017),wave=rng.uniform(.011,.021),turns=rng.uniform(1.2,2.1),seed=800+j+(100 if side>0 else 0),steps=100)
# Soften the garment rim; construction/likeness still require further fitting.
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ('gown' in ob.name.lower() or 'sleeve' in ob.name.lower()):
  for poly in ob.data.polygons:poly.use_smooth=True
bpy.context.scene['repair_revision']='direct-model-r4'
bpy.context.scene['reference_likeness_accepted']=False
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FORGE-model-poprawka-r4.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'FORGE-model-poprawka-r4.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
print('REPAIR_R4_SAVED',flush=True)
