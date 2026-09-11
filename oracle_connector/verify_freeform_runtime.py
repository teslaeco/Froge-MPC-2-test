"""Native Blender verification of v23 tools using authored control fixtures.

No OpenAI calls or claims of photo reconstruction. Run via Blender --python.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import bpy

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'runtime'))
from run import make_material,mesh_object,tube,ellipsoid,join_meshes,finish
from build_scene import build_scene
from scene_contract import validate_scene
from photo_projection import apply_projections
from scene_exports import _portable_uvs


def main(folder):
    folder.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    material={'name':'blue','rgb':[.03,.3,.7],'pattern':'plain','roughness':.5,'metallic':0,'emission':0}
    shell={'kind':'surface_grid','name':'curved-panel','material':'blue','samples':4,'thickness':.02,
        'control_grid':[[[x,.15*math.sin(x*math.pi)*math.sin(z*math.pi),z] for x in (-.5,0,.5)] for z in (0,.5,1)]}
    rings=[[[1.3+rx*math.cos(a),ry*math.sin(a),z] for a in [i*math.tau/8 for i in range(8)]]
        for z,rx,ry in [(0,.2,.15),(.25,.3,.2),(.7,.2,.15),(.9,.12,.1),(1,.16,.12)]]
    loft={'kind':'contour_loft','name':'asymmetric-vessel','material':'blue','rings':rings,'samples':4,'caps':True}
    scene=validate_scene({'version':2,'name':'Authored v23 tool fixtures','subject_type':'object','materials':[material],
        'parts':[shell,loft],'reference_views':[]})
    build_scene(scene,make_material,mesh_object,tube,ellipsoid,join_meshes)
    geometry_counts={o.name:{'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in bpy.context.scene.objects if o.type=='MESH'}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        import bmesh
        bm=bmesh.new();bm.from_mesh(o.data)
        try:assert all(e.is_manifold for e in bm.edges),o.name
        finally:bm.free()
    (folder/'geometry').mkdir(exist_ok=True)
    finish(folder/'geometry')
    assert (folder/'geometry/model.glb').stat().st_size>100

    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat=make_material('original-blue',[.02,.1,.5])
    # Two front quads and one rear quad. A separate occluder hides the left front.
    vertices=[(x,0,z) for z in (0,1) for x in (-.5,0,.5)]
    vertices += [(-.5,.4,0),(.5,.4,0),(.5,.4,1),(-.5,.4,1)]
    target=mesh_object('target',vertices,[(0,1,4,3),(1,2,5,4),(9,8,7,6)],mat)
    uv=target.data.uv_layers.new(name='OriginalUV')
    for loop in uv.data:loop.uv=(.1,.2)
    blocker=mesh_object('occluder',[(-.6,-.2,-.1),(0,-.2,-.1),(0,-.2,1.1),(-.6,-.2,1.1)],[(0,1,2,3)],mat)
    metadata=[]
    for i,color in enumerate(((.8,.1,.05,1),(.02,.8,.1,1))):
        image=bpy.data.images.new('synthetic-reference-%d'%i,width=64,height=64,alpha=False)
        image.pixels.foreach_set(list(color)*(64*64));image.file_format='JPEG'
        path=folder/('reference-%d.jpg'%i);image.filepath_raw=str(path);image.save()
        metadata.append({'name':'Authored test colours','view':'front' if i==0 else 'back','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        bpy.data.images.remove(image)
    (folder/'reference-photos.json').write_text(json.dumps(metadata))
    views=[{'photo_index':i,'position':[0,y,.5],'target':[0,0,.5],'up':[0,0,1],
        'projection':'orthographic','vertical_span':2,'fov':1,
        'regions':[{'part':'target','polygon':[[.1,.1],[.9,.1],[.9,.9],[.1,.9]]}]} for i,y in [(0,-3),(1,3)]]
    projection=apply_projections(views,{'target':[target]},folder)
    assert projection['mapped_faces']==2,projection
    assert target.data.polygons[0].material_index==0,'Hidden front was painted'
    assert target.data.polygons[1].material_index!=0 and target.data.polygons[2].material_index!=0
    original=target.data
    original_uvs={layer.name:[tuple(v.uv) for v in layer.data] for layer in original.uv_layers}
    uv_report={'uv_order_changes':[],'uv_binding_limitations':[]}
    with _portable_uvs(bpy,uv_report):
        assert target.data is not original
        assert target.data.uv_layers[0].name.startswith('ExportColourUV')
        for i in target.data.polygons[0].loop_indices:
            assert abs(target.data.uv_layers[0].data[i].uv[0]-.1)<1e-6
        assert any(x['per_face_colour_uvs_consolidated'] for x in uv_report['uv_order_changes'])
    assert target.data==original
    assert original_uvs=={layer.name:[tuple(v.uv) for v in layer.data] for layer in original.uv_layers}
    bpy.context.scene['photo_projection']=json.dumps(projection)
    (folder/'projection').mkdir(exist_ok=True)
    finish(folder/'projection')
    before=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(folder/'projection/model.fbx'))
    after=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons)
    assert after==before
    report={'fixture_only':True,'openai_calls':0,'likeness_test':False,'geometry':geometry_counts,
        'shells_manifold':True,'projection':projection,'fbx_triangles_before':before,'fbx_triangles_after':after,
        'per_face_uv_export_and_restore':True}
    (folder/'verification.json').write_text(json.dumps(report,indent=2))
    print('FROGE_V23_NATIVE_OK',json.dumps(report))


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    main(Path(args[0]))
