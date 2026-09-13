"""E19 coherent shoulder/neck/corset correction and authored torso 8K PBR maps.
Run apply() after opening E18R. Changes no head, eyes, teeth or hair geometry.
Maps come from bake_body.py Cycles bakes on the actual torso UVMap.
"""
from pathlib import Path
import bpy, math, json
from mathutils import Vector
HERE=Path(__file__).resolve().parent
TARGET_PREFIXES=('R9_continuous_shoulders_neck','R9_tailored_split_gown','R9_bodice_seam_', 'R9_neckline_', 'R9_gathered_sleeve_', 'R9_sleeve_edge_', 'R10_upper_arm_')

def gauss(x,c,s):return math.exp(-((x-c)/s)**2)
def deform(p):
 x,y,z=p; ax=abs(x)
 front=1/(1+math.exp(min(50,(y+.016)*105)))
 # Gentle corset modelling: broaden the supported silhouette slightly, reduce
 # centre-front projection, do not add a spherical protruding breast primitive.
 breast=gauss(ax,.102,.067)*gauss(z,1.154,.073)*front
 sternum=gauss(x,0,.041)*gauss(z,1.198,.075)*front
 dy=-.005*breast+.010*sternum
 dx=(1 if x>0 else -1)*.0055*breast
 # Clavicular S curve and suprasternal notch, blended into the shoulder surface.
 clav_z=1.297 + .017*math.sin(min(ax/.190,1)*math.pi)
 clav=gauss(z,clav_z,.010)*gauss(ax,.099,.100)*front
 dy-=.0055*clav
 dy+=.0032*gauss(x,0,.026)*gauss(z,1.297,.015)*front
 # Bilateral sternocleidomastoid: narrow high insertion, wider low insertion.
 track=.022 + max(0,min(1,(1.396-z)/.104))*.028
 scm=gauss(ax,track,.010)*gauss(z,1.348,.060)*front
 dy-=.0028*scm
 # Slightly softer neck taper, fully fade before touching jaw overlap.
 dx*=1
 dx+=(1 if x>0 else -1)*.0018*gauss(ax,.049,.024)*gauss(z,1.357,.043)
 # Extend the open upper-neck rim into the existing under-jaw volume.
 t=max(0.,min(1.,(z-1.365)/.048));t=t*t*(3-2*t)
 dz=.028*t
 return Vector((x+dx,y+dy,z+dz))

def replace_input(nt,socket,source=None,value=None):
 for l in list(socket.links):nt.links.remove(l)
 if source is not None:nt.links.new(source,socket)
 elif value is not None:socket.default_value=value

def repair_torso_uv():
 body=bpy.data.objects.get('R9_continuous_shoulders_neck')
 if not body:return 0
 uv=body.data.uv_layers.get('UVMap')
 if uv is None:raise RuntimeError('Torso has no UVMap')
 repaired=0
 for p in body.data.polygons:
  values=[uv.data[i].uv.x for i in p.loop_indices]
  if max(values)-min(values)>.5:
   for i in p.loop_indices:
    if uv.data[i].uv.x<.5:uv.data[i].uv.x+=1.
   repaired+=1
 body['e19_uv_wrap_fixed']=True
 return repaired

def apply_geometry():
 changed=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or not o.name.startswith(TARGET_PREFIXES):continue
  if o.get('e19_body_deformed'):continue
  inv=o.matrix_world.inverted();maxd=0.;n=0
  for v in o.data.vertices:
   p=o.matrix_world@v.co;q=deform(p);d=(q-p).length
   if d>1e-8:v.co=inv@q;n+=1;maxd=max(maxd,d)
  o.data.update();o['e19_body_deformed']=True
  changed.append({'object':o.name,'changed_vertices':n,'max_displacement_m':maxd})
 return changed

def apply_textures():
 body=bpy.data.objects.get('R9_continuous_shoulders_neck')
 if not body:raise RuntimeError('Required E18R torso missing')
 maps={}
 for key,file in [('base','E19_body_BaseColor_8K.png'),('orm','E19_body_ORM_8K.png'),('normal','E19_body_Normal_8K.png')]:
  p=HERE/'textures'/file
  if not p.exists():raise FileNotFoundError(p)
  i=bpy.data.images.load(str(p),check_existing=True)
  i.colorspace_settings.name='sRGB' if key=='base' else 'Non-Color'
  if list(i.size)!=[8192,8192]:raise RuntimeError('E19 8K texture dimension mismatch')
  maps[key]=i
 for slot in body.material_slots:
  original=slot.material
  if original.get('e19_body_8k_applied'):continue
  m=original.copy();m.name='E19 torso living 8K' if 'warm' in original.name else 'E19 torso bone 8K'
  nt=m.node_tree;b=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
  tex={}
  for key,i in maps.items():
   n=nt.nodes.new('ShaderNodeTexImage');n.image=i;n.name='E19 '+key+' 8192';n.extension='EXTEND';tex[key]=n
  replace_input(nt,b.inputs['Base Color'],tex['base'].outputs['Color'])
  sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex['orm'].outputs['Color'],sep.inputs['Color'])
  replace_input(nt,b.inputs['Roughness'],sep.outputs['Green']);replace_input(nt,b.inputs['Metallic'],value=0.)
  normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=1.;normal.uv_map='UVMap';nt.links.new(tex['normal'].outputs['Color'],normal.inputs['Color']);replace_input(nt,b.inputs['Normal'],normal.outputs['Normal'])
  b.inputs['Subsurface Weight'].default_value=.055 if 'warm' in original.name else 0
  b.inputs['Subsurface Radius'].default_value=(1.,.42,.22);b.inputs['Subsurface Scale'].default_value=.0012
  b.inputs['Specular IOR Level'].default_value=.28 if 'warm' in original.name else .22
  m['e19_body_8k_applied']=True
  slot.material=m
 return {key:{'file':i.filepath,'size':list(i.size)}for key,i in maps.items()}

def apply(with_textures=True):
 result={'uv_wrap_triangles_repaired':repair_torso_uv(),'geometry':apply_geometry(),'textures':apply_textures() if with_textures else {},'scope':'torso, neck, upper arms, gown and attached seam geometry; existing face albedo retained unchanged','claims':'authored procedural skin details, not a recovered 8K photograph; no print-readiness claim'}
 (HERE/'body-apply-report.json').write_text(json.dumps(result,indent=2))
 return result
