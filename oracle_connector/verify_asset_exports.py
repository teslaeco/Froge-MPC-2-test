"""Native reimport check of an existing completed model, without regeneration."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import bpy
from mathutils import Vector


def snapshot():
    bpy.context.view_layer.update()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    # OBJ bakes object transforms; transformed local bounding boxes would make
    # identical rotated geometry appear to differ. Compare actual vertices.
    bounds=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    materials={m for o in meshes for m in o.data.materials if m and m.use_nodes}
    images={n.image for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    maps=[]
    for image in images:
        data=bytes(image.packed_file.data) if image.packed_file else Path(bpy.path.abspath(image.filepath)).read_bytes()
        maps.append({'image':image.name,'size':list(image.size),'sha256':hashlib.sha256(data).hexdigest()})
    return {'meshes':len(meshes),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),
            'bounds':[[min(p[i] for p in bounds),max(p[i] for p in bounds)] for i in range(3)],
            'uv_meshes':sum(bool(o.data.uv_layers) for o in meshes),'maps':sorted(maps,key=lambda x:x['image'])}


def verify(folder):
    bpy.ops.wm.open_mainfile(filepath=str(folder/'model.blend'))
    original=snapshot()
    report=json.loads((folder/'result.json').read_text())['interchange_exports']
    skin_hashes={t['sha256'] for t in report['textures'] if t['image'].startswith('baked-base-color-')}
    result={'blender':bpy.app.version_string,'source':original,'formats':{},
            'complete_shader_equivalence_verified':False,'reference_likeness_verified':False}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for format_name in ('fbx','obj','stl'):
            output=root/format_name;output.mkdir()
            name={'fbx':'model.fbx','obj':'model.obj','stl':'model-mm.stl'}[format_name]
            shutil.copy2(folder/name,output/name)
            if format_name=='obj':
                shutil.copy2(folder/'model.mtl',output/'model.mtl');(output/'textures').mkdir()
                for texture in report['textures']:shutil.copy2(folder/texture['path'],output/texture['path'])
            bpy.ops.wm.read_factory_settings(use_empty=True)
            if format_name=='fbx':bpy.ops.import_scene.fbx(filepath=str(output/name))
            elif format_name=='obj':bpy.ops.wm.obj_import(filepath=str(output/name),forward_axis='NEGATIVE_Z',up_axis='Y')
            else:bpy.ops.wm.stl_import(filepath=str(output/name),global_scale=.001,forward_axis='NEGATIVE_Z',up_axis='Y')
            imported=snapshot()
            assert imported['triangles']==original['triangles'],format_name+' triangle mismatch'
            delta=max(abs(a-b) for row1,row2 in zip(original['bounds'],imported['bounds']) for a,b in zip(row1,row2))
            assert delta<.00002,(format_name,'bounds mismatch',delta)
            if format_name in ('fbx','obj'):
                assert skin_hashes.issubset({x['sha256'] for x in imported['maps']}),'Missing baked face colour'
                assert imported['uv_meshes']==original['uv_meshes'],'Missing UV layer'
            result['formats'][format_name]={'passed':True,'bounds_max_error_metres':delta,**imported,
                'baked_face_colour_present':bool(skin_hashes) if format_name!='stl' else False}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);parser.add_argument('report',type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    result=verify(args.folder.resolve());args.report.write_text(json.dumps(result,indent=2))
    print('NATIVE_ASSET_REIMPORT_OK',result['source']['triangles'],'triangles; FBX, OBJ and millimetre STL')
