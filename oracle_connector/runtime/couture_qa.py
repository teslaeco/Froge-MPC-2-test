"""Inspect the exported GLB, then reopen it in Blender before accepting it.

Structural checks never imply photographic likeness or print readiness.
"""
import json
import math
import struct
from collections import Counter
import bpy


def verify_export(path, source_objects):
    data=path.read_bytes();magic,version,length=struct.unpack_from('<III',data)
    if (magic,version,length)!=(0x46546C67,2,len(data)):raise ValueError('Invalid GLB header')
    size,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a:raise ValueError('Missing GLB JSON chunk')
    doc=json.loads(data[20:20+size])
    if any('uri' in b for b in doc.get('buffers',[])):raise ValueError('External geometry in GLB')
    if any('bufferView' not in image for image in doc.get('images',[])):raise ValueError('Missing packed GLB texture')
    expected=Counter(o.get('froge_role') for o in source_objects if o.get('froge_role'))
    anatomy={key:sum(bool(o.get(key)) for o in source_objects) for key in
             ('anatomical_head','anatomical_eye','anatomical_hand','anatomical_nail')}
    # Import into the current scene and isolate the newly created objects.
    # Do not destroy the artist's source scene or save this inspection copy.
    before=set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=str(path))
        imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
        if not imported:raise ValueError('GLB reimport contains no geometry')
        actual=Counter(o.get('froge_role') for o in imported if o.get('froge_role'))
        if actual!=expected:raise ValueError('Export lost couture parts')
        for key,count in anatomy.items():
            if sum(bool(o.get(key)) for o in imported)!=count:raise ValueError('Export lost anatomy: '+key)
        for obj in imported:
            if not obj.data.vertices or not all(math.isfinite(c) for v in obj.data.vertices for c in v.co):
                raise ValueError('Export contains empty or non-finite geometry')
            if obj.get('anatomical_head') and not obj.data.uv_layers:raise ValueError('Export lost portrait UVs')
        return {'reimported':True,'anatomy':anatomy,'roles':dict(actual),'packed_images':len(doc.get('images',[])),
                'likeness_assessed':False,'print_readiness_assessed':False}
    finally:
        for obj in list(bpy.data.objects):
            if obj not in before:bpy.data.objects.remove(obj,do_unlink=True)
