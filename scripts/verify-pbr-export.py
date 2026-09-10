"""Real production texture policy and GLB roundtrip on supplied PBR maps.

blender -b --python verify-pbr-export.py -- /maps/directory /output/directory
The cube is a transport fixture, NOT a generated subject or likeness test.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'oracle_connector/runtime'))
from reference_quality import export_textures, geometry_digest

source,output=map(Path,sys.argv[sys.argv.index('--')+1:])
output.mkdir(parents=True,exist_ok=True)
(output/'reference-photos.json').write_text('[{"textureMaxSize":8192}]')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
obj=bpy.context.object;obj.scale=(.7,.9,1.3);bpy.context.view_layer.update()
mat=bpy.data.materials.new('Supplied-PBR-fixture');mat.use_nodes=True;obj.data.materials.append(mat)
nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=nodes.get('Principled BSDF')
maps={};hashes={}
for channel,suffix in [('color','_texture.png'),('normal','_texture_normal.png'),
                       ('metallic','_texture_metallic.png'),('roughness','_texture_roughness.png')]:
    candidates=list(source.glob('*'+suffix))
    assert len(candidates)==1,(channel,candidates)
    path=candidates[0];image=bpy.data.images.load(str(path),check_existing=False)
    image.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color'
    maps[channel]=image;hashes[channel]=hashlib.sha256(path.read_bytes()).hexdigest()
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    if channel=='normal':
        normal=nodes.new('ShaderNodeNormalMap');links.new(tex.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    else:links.new(tex.outputs['Color'],shader.inputs[{'color':'Base Color','metallic':'Metallic','roughness':'Roughness'}[channel]])

before=geometry_digest([obj]);dimensions={k:list(im.size) for k,im in maps.items()}
os.environ['FROGE_EXPORT_MEMORY_GIB']='4'
try:export_textures(list(maps.values()),output)
except ValueError:pass
else:raise AssertionError('Full 8K PBR set must not be admitted under 4 GiB')
assert dimensions=={k:list(im.size) for k,im in maps.items()}
assert all(im.packed_file is None for im in maps.values())
os.environ['FROGE_EXPORT_MEMORY_GIB']='8'
report=export_textures(list(maps.values()),output)
assert geometry_digest([obj])==before
assert dimensions=={k:list(im.size) for k,im in maps.items()}
model=output/'pbr-roundtrip.glb'
bpy.ops.export_scene.gltf(filepath=str(model),export_format='GLB',export_image_format='AUTO')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(model))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
assert sum(len(p.vertices)-2 for p in mesh.data.polygons)==12
images=[im for im in bpy.data.images if im.users]
assert sorted(tuple(im.size) for im in images)==[(4096,4096),(4096,4096),(8192,8192)]
reimport_hashes={hashlib.sha256(im.packed_file.data).hexdigest() for im in images}
assert hashes['color'] in reimport_hashes
assert hashes['normal'] in reimport_hashes
# glTF packs roughness in G and metalness in B. Verify sampled actual pixels,
# not only image dimensions or the existence of material-node labels.
packed=next(im for im in images if 'roughness' in im.name.lower() or 'metallic' in im.name.lower())
buf=np.empty(4096*4096*4,dtype=np.float32);packed.pixels.foreach_get(buf)
packed_pixels=buf.reshape(-1,4)[::7919].copy();del buf
for channel,index in [('roughness',1),('metallic',2)]:
    im=bpy.data.images.load(str(next(source.glob('*_texture_'+channel+'.png'))),check_existing=False)
    im.colorspace_settings.name='Non-Color'
    buf=np.empty(4096*4096*4,dtype=np.float32);im.pixels.foreach_get(buf)
    source_pixels=buf.reshape(-1,4)[::7919,0]
    assert np.max(np.abs(packed_pixels[:,index]-source_pixels))<=1/255+1e-6
    del buf;bpy.data.images.remove(im)
report.update(reference_maps_only=True,transport_fixture='cube',geometry_unchanged_by_texture_policy=True,
              rejected_4g_without_mutation=True,reimported=True,base_color_and_normal_bytes_preserved=True,
              roughness_and_metallic_channels_verified=True,glb_bytes=model.stat().st_size,
              glb_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),blender=bpy.app.version_string)
(output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('FROGE_NATIVE_PBR_ROUNDTRIP_OK',flush=True)
