"""Separate catalog preview; keep the full geometry and master untouched.

Run in Blender: --python this.py -- master.glb preview.glb [512|1024]
No AI call. This does not lower production generator quality or its source maps.
"""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector


def snapshot():
    bpy.context.view_layer.update()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    vertices=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    return {'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),
            'bounds':[[min(v[i] for v in vertices),max(v[i] for v in vertices)] for i in range(3)]}


args=sys.argv[sys.argv.index('--')+1:]
source,target=map(Path,args[:2]);max_edge=int(args[2]) if len(args)>2 else 1024
if max_edge not in (512,1024):raise ValueError('Unsupported preview resolution')
if source.resolve()==target.resolve():raise ValueError('Preview must be a separate file')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
before=snapshot();maps=[]
for image in bpy.data.images:
    width,height=image.size
    if not width or not height:continue
    scale=min(1.,max_edge/max(width,height))
    size=[max(1,round(width*scale)),max(1,round(height*scale))]
    if scale<1:image.scale(*size);image.pack()
    maps.append({'name':image.name,'source':[width,height],'preview':size})
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',
                         export_extras=True,export_yup=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(target))
after=snapshot()
assert after['triangles']==before['triangles'],'Preview changed geometry'
delta=max(abs(a-b) for r,s in zip(before['bounds'],after['bounds']) for a,b in zip(r,s))
assert delta<.000001,'Preview changed scale or placement'
assert target.stat().st_size<24*1024*1024,'Preview exceeds current catalog limit'
target.with_suffix('.json').write_text(json.dumps({'kind':'catalog preview only','max_texture_edge':max_edge,
    'master_file':source.name,'geometry_decimated':False,'triangles':after['triangles'],
    'bounds_max_error_metres':delta,'bytes':target.stat().st_size,'textures':maps},indent=2))
print('CATALOG_PREVIEW_OK',target.stat().st_size,'bytes;',after['triangles'],'triangles unchanged')
