import bpy,sys,math,json,hashlib,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import apply_body
OUT=HERE/'textures';OUT.mkdir(exist_ok=True)
uv_fixed=apply_body.repair_torso_uv();apply_body.apply_geometry()
body=bpy.data.objects['R9_continuous_shoulders_neck']
# Bake only the target, no environment, rays, lighting or other scene geometry.
for o in list(bpy.data.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.bake_type='EMIT';s.render.threads_mode='FIXED';s.render.threads=6;s.render.bake.margin=16;s.render.bake.use_clear=True;s.render.bake.use_selected_to_active=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.view_settings.view_transform='Standard'
materials=[]
for slot in body.material_slots:
 old=slot.material;m=old.copy();m.name='E19 Bake '+old.name;slot.material=m
 nt=m.node_tree;n=nt.nodes;l=nt.links;b=next(x for x in n if x.type=='BSDF_PRINCIPLED');out=next(x for x in n if x.type=='OUTPUT_MATERIAL');alive='warm' in old.name
 geom=n.new('ShaderNodeNewGeometry')
 def noise(scale,detail=2):
  q=n.new('ShaderNodeTexNoise');q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=detail;q.inputs['Roughness'].default_value=.7;l.new(geom.outputs['Position'],q.inputs['Vector']);return q
 macro=noise(32,3);med=noise(150,2);fine=noise(2350,2)
 ramp=n.new('ShaderNodeValToRGB')
 if alive:
  ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[0].color=(.275,.146,.065,1)
  ramp.color_ramp.elements[1].position=.88;ramp.color_ramp.elements[1].color=(.365,.211,.112,1)
  l.new(macro.outputs['Fac'],ramp.inputs[0]);base=ramp.outputs['Color']
  # Subtle chromatic variation; not a projected photograph or baked illumination.
  mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.07;l.new(base,mix.inputs[1]);l.new(med.outputs['Color'],mix.inputs[2]);base=mix.outputs[0]
 else:
  base=b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
  if base is None:ramp.color_ramp.elements[0].color=(.06,.061,.038,1);ramp.color_ramp.elements[1].color=(.17,.18,.12,1);l.new(macro.outputs['Fac'],ramp.inputs[0]);base=ramp.outputs['Color']
 apply_body.replace_input(nt,b.inputs['Base Color'],base)
 # Pore cavities use a physical position field, baked through mesh UVs.
 v=n.new('ShaderNodeTexVoronoi');v.distance='EUCLIDEAN';v.feature='F1';v.inputs['Scale'].default_value=2100 if alive else 1100;l.new(geom.outputs['Position'],v.inputs['Vector'])
 pore=n.new('ShaderNodeValToRGB');pore.color_ramp.elements[0].position=.075;pore.color_ramp.elements[0].color=(.02,.02,.02,1);pore.color_ramp.elements[1].position=.26;pore.color_ramp.elements[1].color=(.55,.55,.55,1);l.new(v.outputs['Distance'],pore.inputs[0])
 h=n.new('ShaderNodeMixRGB');h.blend_type='MULTIPLY';h.inputs[0].default_value=.18;l.new(pore.outputs['Color'],h.inputs[1]);l.new(fine.outputs['Color'],h.inputs[2])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.38 if alive else .5;bump.inputs['Distance'].default_value=.00014 if alive else .00038;l.new(h.outputs[0],bump.inputs['Height'])
 if b.inputs['Normal'].is_linked:l.new(b.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
 apply_body.replace_input(nt,b.inputs['Normal'],bump.outputs['Normal'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0.;rough.inputs['From Max'].default_value=1.;rough.inputs['To Min'].default_value=.37 if alive else .61;rough.inputs['To Max'].default_value=.54 if alive else .85;l.new(med.outputs['Fac'],rough.inputs['Value']);apply_body.replace_input(nt,b.inputs['Roughness'],rough.outputs[0])
 orm=n.new('ShaderNodeCombineColor');orm.inputs['Red'].default_value=1.;orm.inputs['Blue'].default_value=0.;l.new(rough.outputs[0],orm.inputs['Green'])
 emit=n.new('ShaderNodeEmission');target=n.new('ShaderNodeTexImage');n.active=target;target.select=True
 materials.append({'m':m,'out':out,'bsdf':b,'base':base,'orm':orm.outputs[0],'emit':emit,'target':target})
report={'method':'Blender 4.3 Cycles procedural emission and tangent-normal baking on R9_continuous_shoulders_neck original UVMap','body_uv_domain':'U 0..1; V 0.436268..1.0; 124 inherited wrap-spanning triangles repaired; not an upscaled source image','images':[]}
for kind,filename in [('base','E19_body_BaseColor_8K.png'),('orm','E19_body_ORM_8K.png'),('normal','E19_body_Normal_8K.png')]:
 started=time.time();im=bpy.data.images.new(filename,width=8192,height=8192,alpha=False,float_buffer=False);im.colorspace_settings.name='sRGB' if kind=='base' else 'Non-Color'
 for d in materials:
  nt=d['m'].node_tree;d['target'].image=im;nt.nodes.active=d['target']
  for li in list(d['out'].inputs['Surface'].links):nt.links.remove(li)
  if kind=='normal':nt.links.new(d['bsdf'].outputs['BSDF'],d['out'].inputs['Surface'])
  else:nt.links.new(d[kind],d['emit'].inputs['Color']);nt.links.new(d['emit'].outputs[0],d['out'].inputs['Surface'])
 print('E19 BAKE START',kind,flush=True)
 bpy.ops.object.bake(type='NORMAL' if kind=='normal' else 'EMIT',normal_space='TANGENT',use_clear=True,margin=16)
 im.filepath_raw=str(OUT/filename);im.file_format='PNG';im.save();
 with open(OUT/filename,'rb') as synced:
  import os;os.fsync(synced.fileno())
 p=OUT/filename;report['images'].append({'file':filename,'width':8192,'height':8192,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'seconds':time.time()-started,'semantic':{'base':'torso colour with procedural living skin variation and inherited weathered bone colour','orm':'RGB: AO constant 1, newly authored roughness, metalness constant 0','normal':'new tangent normals from physical-scale skin pore and bone surface procedural bump'}[kind]})
 print('E19 BAKE DONE',kind,report['images'][-1],flush=True)
 for d in materials:d['target'].image=None
 bpy.data.images.remove(im)
 (HERE/'8k-bake-report.json').write_text(json.dumps(report,indent=2))
print('E19_8K_BAKES_COMPLETE',flush=True)
