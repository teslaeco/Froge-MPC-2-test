import bpy,json
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath='/workspace/scratch/584c9d97a5a1/materials-r13/FORGE-model-r13.fbx')
r=[]
for m in bpy.data.materials:
 if m.name.startswith('R13'):
  bs=m.node_tree.nodes.get('Principled BSDF');r.append({'material':m.name,'roughness':bs.inputs['Roughness'].default_value,'roughness_links':[(l.from_node.type,l.from_node.image.name if l.from_node.type=='TEX_IMAGE' else '') for l in bs.inputs['Roughness'].links],'normal_links':[(l.from_node.type) for l in bs.inputs['Normal'].links]})
open('/workspace/scratch/584c9d97a5a1/materials-r13/imported-materials.json','w').write(json.dumps(r,indent=2))
