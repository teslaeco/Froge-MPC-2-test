"""Blender integration: real 4K/8K texture export/reimport and unchanged mesh.

blender -b --python scripts/verify-reference-quality.py -- /absolute/output
Synthetic UV test pattern is NOT a reconstructed photographic detail.
"""
import json
from pathlib import Path
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'oracle_connector/runtime'))
from reference_quality import export_textures, geometry_digest

output=Path(sys.argv[sys.argv.index('--')+1]);output.mkdir(parents=True,exist_ok=True)
results=[]
for limit in (4096,8192):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12)
    obj=bpy.context.object;obj.name='UV-and-silhouette-check'
    obj.scale=(1.,.7,1.3);bpy.context.view_layer.update()
    image=bpy.data.images.new('Native-8192-test-pattern',width=8192,height=1024,alpha=False)
    image['reference_surface']=True
    pixels=np.ones((1024,8192,4),dtype=np.float32)
    pixels[:,:,0]=(np.arange(8192)%31)[None,:]/30
    pixels[:,:,1]=(np.arange(1024)%17)[:,None]/16
    pixels[:,:,2]=.35
    image.pixels.foreach_set(pixels.ravel());image.update();del pixels
    mat=bpy.data.materials.new('UV-pattern');mat.use_nodes=True
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    obj.data.materials.append(mat)
    folder=output/str(limit);folder.mkdir(exist_ok=True)
    (folder/'reference-photos.json').write_text(json.dumps([{'textureMaxSize':limit}]))
    before=geometry_digest([obj]);report=export_textures([image],folder)
    assert geometry_digest([obj])==before
    model=folder/'pattern.glb'
    bpy.ops.export_scene.gltf(filepath=str(model),export_format='GLB',export_image_format='AUTO')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    images=[im for im in bpy.data.images if im.users]
    expected=[limit,limit//8]
    assert any(list(im.size)==expected for im in images),[tuple(i.size) for i in images]
    report.update(reimported=True,expected_size=expected,geometry_unchanged=True,glb_bytes=model.stat().st_size)
    results.append(report)
(output/'verification.json').write_text(json.dumps({'blender':bpy.app.version_string,'fixtures':results},indent=2))
print('FROGE_REFERENCE_QUALITY_OK',flush=True)
