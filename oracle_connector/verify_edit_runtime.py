"""Native regression for editing a legal sixteen-material scene; no AI calls.

Blender --background --python verify_edit_runtime.py -- [--existing-blend PATH]
uses either a supplied saved model or a deterministic sixteen-material fixture.
Both exercise the real material helpers, export budget, GLB and FBX re-import.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
import tempfile
import traceback

import bpy

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'runtime'
if not RUNTIME.is_dir():
    RUNTIME = Path('/runner')  # The existing read-only production container mount.
sys.path.insert(0, str(RUNTIME))
from run import edit_material_factory, ellipsoid, execute_job, finish, make_material


def cube(name, material, location):
    bpy.ops.mesh.primitive_cube_add(size=.025, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def verify_execution_scope(folder):
    """Exercise the production edit scope with its full eight-material plan."""
    folder.mkdir(parents=True, exist_ok=True)
    scene = {'version': 2, 'name': 'edit-scope', 'subject_type': 'object',
             'reference_views': [], 'materials': [], 'parts': []}
    for index in range(8):
        name = 'scope-plan-%d' % index
        scene['materials'].append({'name': name, 'rgb': [.2, .3, .4], 'pattern': 'plain',
                                   'roughness': .7, 'metallic': 0, 'emission': 0})
        scene['parts'].append({'kind': 'box', 'name': name, 'material': name,
                               'center': [index * .04, 0, .02], 'size': [.025] * 3,
                               'rotation': [0, 0, 0]})
    (folder / 'scene.json').write_text(json.dumps(scene))
    (folder / 'edits.py').write_text(
        'material = make_material("scope-edit", (.7, .2, .1), "fabric")\n'
        'ellipsoid("scope-edit", (.1, 0, .08), radii=(.01, .02, .03), material=material, subdivisions=1)\n')
    execute_job(folder)
    report = json.loads((folder / 'result.json').read_text())
    assert report['edit_palette']['created'] == 1
    assert report['edit_palette']['used_materials'] == 1
    (folder / 'edits.py').write_text('raise ValueError("edit trace marker")\n')
    try:
        execute_job(folder)
        raise AssertionError('The edit diagnostic fixture did not fail.')
    except ValueError as error:
        assert str(error) == 'edit trace marker'
        assert traceback.extract_tb(error.__traceback__)[-1].filename == '/work/edits.py'


def verify(output, existing_blend=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    verify_execution_scope(output / 'scope-check')
    if existing_blend:
        bpy.ops.wm.open_mainfile(filepath=str(existing_blend), use_scripts=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        base = [make_material('plan-%d' % index, (.2, .3, .4)) for index in range(8)]
        for index, material in enumerate(base):
            cube('plan-%d' % index, material, (index * .04, 0, .04))
            # The trusted anatomy renderer also creates material variants.
            variant = material.copy()
            variant.name = 'trusted-variant-%d' % index
            cube(variant.name, variant, (index * .04, .04, .04))
    assert sum(material.users > 0 for material in bpy.data.materials) == 16
    try:
        make_material('not-an-edit', (.8, .4, .1))
        raise AssertionError('The original scene palette limit was removed.')
    except ValueError as error:
        assert 'at most 8' in str(error)

    create, budget = edit_material_factory()
    for index in range(8):
        pattern = 'cotton' if index == 0 else 'denim' if index == 1 else 'fabric'
        material = create('edit-palette-%d' % index, (.7, .25 + index * .025, .1), pattern)
        cube('edit-palette-%d' % index, material, (.42 + index * .04, 0, .25))
    material_count = len(bpy.data.materials)
    try:
        create('edit-over-budget', (.4, .5, .6))
        raise AssertionError('The ninth material was allowed.')
    except ValueError as error:
        assert 'at most 8 new materials' in str(error)
    assert len(bpy.data.materials) == material_count

    material = bpy.data.materials['edit-palette-0']
    positional = ellipsoid('position-compatible', (.42, 0, .3), (.01, .02, .03), material, 1)
    legacy = ellipsoid('scale-compatible', (.48, 0, .3), scale=(.01, .02, .03), material=material, subdivisions=1)
    advertised = ellipsoid('radii-compatible', (.54, 0, .3), radii=(.01, .02, .03), material=material, subdivisions=1)
    bpy.context.view_layer.update()
    assert all(obj.type == 'MESH' and tuple(obj.scale) == tuple(positional.scale)
               for obj in (positional, legacy, advertised))
    try:
        ellipsoid('ambiguous', (0, 0, 0), scale=(1, 1, 1), radii=(1, 1, 1))
        raise AssertionError('Conflicting helper keywords were accepted.')
    except ValueError as error:
        assert 'not both' in str(error)

    # Untracked extra materials cannot claim the edit palette allowance.
    rogue = bpy.data.materials.new('untracked-material')
    rogue_obj = cube('untracked-material', rogue, (1, 0, .25))
    try:
        finish(output, edit_budget=budget)
        raise AssertionError('Final export accepted an untracked extra material.')
    except ValueError as error:
        assert 'Export limit:' in str(error), str(error)
    bpy.data.objects.remove(rogue_obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    bpy.data.materials.remove(rogue)

    finish(output, edit_budget=budget)
    report = json.loads((output / 'result.json').read_text())
    assert report['edit_palette']['created'] == 8
    assert report['edit_palette']['used_materials'] == 8
    assert report['edit_palette']['used_images'] >= 8
    expected = {'edit-palette-%d' % index for index in range(8)}
    data = (output / 'model.glb').read_bytes()
    magic, version, length, json_size, kind = struct.unpack_from('<IIIII', data)
    assert (magic, version, length, kind) == (0x46546c67, 2, len(data), 0x4e4f534a)
    document = json.loads(data[20:20 + json_size])
    assert expected <= {material.get('name') for material in document['materials']}
    assert (output / 'model.fbx').stat().st_size > 1000
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output / 'model.glb'))
    assert expected <= {material.name for material in bpy.data.materials}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(output / 'model.fbx'))
    assert expected <= {material.name for material in bpy.data.materials}
    return {'blender': bpy.app.version_string, 'initial_used_materials': 16,
            'new_edit_materials': 8, 'ninth_edit_material_rejected': True,
            'untracked_export_material_rejected': True,
            'ellipsoid_positional_scale_and_radii_verified': True,
            'production_edit_scope_and_traceback_verified': True,
            'glb_and_fbx_reimport_preserve_edit_materials': True,
            'edit_palette': report['edit_palette'], 'triangles': report['triangles'],
            'scope': 'Runtime and exports only; not a new AI likeness result.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--existing-blend', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    with tempfile.TemporaryDirectory(prefix='forge-edit-runtime-') as temporary:
        result = verify(args.output or Path(temporary), args.existing_blend)
        if args.output:
            (args.output / 'verification.json').write_text(json.dumps(result, indent=2))
        print('FROGE_EDIT_RUNTIME_OK ' + json.dumps(result), flush=True)
