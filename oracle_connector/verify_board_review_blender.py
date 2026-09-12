"""Small actual-Blender integration check; no rendered texture score."""
import bpy
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).parent/'runtime'))
from test_reference_reconstruction import board_fixture
from reference_reconstruction import board_review_report

results=[]

for levels in (1,8):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
    spec,cells=board_fixture(levels)
    materials=[]
    for label in ('light','dark'):
        value=spec['palette'][label]
        mat=bpy.data.materials.new(value['material']);mat.use_nodes=True
        mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*value['linear_rgb'],1.)
        materials.append(mat)
    vertices=[];faces=[]
    for cell in cells:
        x,y,z=cell['center'];base=len(vertices)
        vertices.extend([(x-.04,y-.04,z),(x+.04,y-.04,z),(x+.04,y+.04,z),(x-.04,y+.04,z)])
        faces.append(tuple(range(base,base+4)))
    mesh=bpy.data.meshes.new('board');mesh.from_pydata(vertices,[],faces);mesh.update()
    for mat in materials:mesh.materials.append(mat)
    attr=mesh.attributes.new('board_cell_index','INT','FACE')
    for p,cell in zip(mesh.polygons,cells):
        attr.data[p.index].value=cell['index']
        p.material_index=(cell['x']+cell['y']+cell['z'])&1
    obj=bpy.data.objects.new('board',mesh);bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.update()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'board-spec.json';path.write_text(json.dumps(spec))
        result=board_review_report(td,[obj])
        assert result['passed'],result
        assert result['actual_cells']==64*levels,result
        mesh.polygons[1].material_index=0;mesh.update();bpy.context.view_layer.update()
        result=board_review_report(td,[obj])
        assert 'material_parity' in result['failures'],result
        mesh.polygons[1].material_index=1
        attr.data[-1].value=-1;mesh.update();bpy.context.view_layer.update()
        result=board_review_report(td,[obj])
        assert 'cell_count' in result['failures'],result
        path.unlink()
        assert board_review_report(td,[obj])['status']=='unverified'
        results.append({'levels':levels,'cells':64*levels,'geometry_and_material_checks':'passed',
                        'wrong_material_detected':True,'missing_cell_detected':True,
                        'missing_spec_unverified':True,'texture_pixels_verified':False})
        print(json.dumps(results[-1]))
(Path(__file__).parent/'board-review-smoke.json').write_text(json.dumps({
    'blender_version':bpy.app.version_string,'execution':'actual_Blender_CPU','threads':2,
    'cases':results,'renders_created':False,'weights_trained':False},indent=2))
