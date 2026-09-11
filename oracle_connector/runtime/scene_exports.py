"""Native exports derived from the saved master scene.

STL is deliberately documented as unitless geometry whose numeric coordinates are
millimetres.  It is not a textured or print-readiness deliverable.
"""
from pathlib import Path


FORMATS = ('glb', 'fbx', 'blend', 'obj+mtl', 'stl', 'froge-scene-json')


def export_interchange(output, scene_source=None):
    import bpy

    output = Path(output)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(
        filepath=str(output / 'model.fbx'), use_selection=True,
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z', axis_up='Y', add_leaf_bones=False,
        bake_anim=True, path_mode='COPY', embed_textures=True,
    )
    bpy.ops.wm.obj_export(
        filepath=str(output / 'model.obj'), export_selected_objects=True,
        export_materials=True, export_uv=True, export_normals=True,
        forward_axis='NEGATIVE_Z', up_axis='Y', path_mode='COPY',
    )
    # STL has no unit metadata. Multiplying metres by 1000 writes millimetre
    # numeric coordinates without modifying the master scene.
    bpy.ops.wm.stl_export(
        filepath=str(output / 'model-mm.stl'), export_selected_objects=True,
        global_scale=1000.0, forward_axis='NEGATIVE_Z', up_axis='Y',
    )
    if scene_source and Path(scene_source).is_file():
        (output / 'model.froge-scene.json').write_bytes(Path(scene_source).read_bytes())
    return {
        'formats': list(FORMATS),
        'same_master_scene': True,
        'fbx': {'axis_forward': '-Z', 'axis_up': 'Y', 'textures_embedded': True,
                'rig_policy': 'existing armatures and animation are exported; no rig is invented'},
        'obj': {'mtl': 'model.mtl', 'uvs': True, 'normals': True,
                'shader_boundary': 'OBJ/MTL cannot reproduce every Blender or glTF PBR shader'},
        'stl': {'numeric_unit': 'millimetre', 'textures': False,
                'print_readiness_assessed': False},
        'scene_json': {'schema': 'Froge scene contract', 'present': bool(scene_source)},
    }
