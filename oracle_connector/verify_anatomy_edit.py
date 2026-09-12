"""Native portrait-edit regression; authored fixture, no model/API calls.

Run with Blender --background --python verify_anatomy_edit.py -- --output PATH.
Checks the production scene/edit runner, anatomical tags, actionable failures and
a valid asymmetric eye material. This is not a reference-likeness assessment.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile

import bpy

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'runtime'
if not RUNTIME.is_dir():
    RUNTIME = Path('/runner')
sys.path.insert(0, str(RUNTIME))
from portrait import AnatomyValidationError, component_snapshot, verify_components
from run import execute_job, join_meshes


def scene_fixture():
    materials = [
        {'name': name, 'rgb': rgb, 'pattern': 'plain', 'roughness': .7,
         'metallic': 0, 'emission': 0}
        for name, rgb in [('skin', [.64, .42, .32]), ('hair', [.10, .045, .022]),
                          ('eye', [.11, .24, .13]), ('nail', [.30, .025, .025])]
    ]
    parts = [
        {'kind': 'portrait', 'name': 'fixture-head', 'center': [0, 0, 1.65],
         'scale': 1, 'rotation': [0, 0, 0], 'skin_material': 'skin',
         'hair_material': 'hair', 'eye_material': 'eye',
         'presentation': 'feminine', 'hair_style': 'short', 'headwear': 'none',
         'eyewear': 'none', 'face': {key: 0 for key in
             ('nose_width', 'nose_projection', 'mouth_width', 'lip_fullness',
              'jaw_width', 'chin_height', 'cheek_fullness')},
         'makeup': 'none'}
    ]
    for side, sign in [('left', -1), ('right', 1)]:
        parts.append({'kind': 'anatomical_hand', 'name': 'fixture-' + side,
                      'wrist': [sign * .25, 0, 1.1], 'direction': [0, 0, -1],
                      'palm_normal': [0, -1, 0], 'side': side,
                      'presentation': 'feminine', 'scale': 1, 'curl': .3,
                      'nail_length': .001, 'skin_material': 'skin',
                      'nail_material': 'nail'})
    return {'version': 2, 'name': 'anatomy-edit-fixture', 'subject_type': 'person',
            'materials': materials, 'parts': parts, 'reference_views': []}


STYLE_EDIT = """
eyes = sorted([obj for obj in bpy.context.scene.objects if obj.get('anatomical_eye')],
              key=lambda obj: obj.name)
material = make_material('asymmetric-eye-fixture', (.012, .025, .016))
eyes[0].data.materials.clear()
eyes[0].data.materials.append(material)
eyes[0]['artistic_asymmetry_fixture'] = True
head = [obj for obj in bpy.context.scene.objects if obj.get('anatomical_head')][0]
for vertex in head.data.vertices:
    if vertex.co.x < 0:
        vertex.co.x *= 1.003
"""
DELETE_NAIL = """
nails = sorted([obj for obj in bpy.context.scene.objects if obj.get('anatomical_nail')],
               key=lambda obj: obj.name)
bpy.data.objects.remove(nails[0], do_unlink=True)
"""


def prepare(folder, edit):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'scene.json').write_text(json.dumps(scene_fixture()), encoding='utf-8')
    (folder / 'edits.py').write_text(edit, encoding='utf-8')


def verify(output):
    output = Path(output)
    valid = output / 'valid-edit'
    prepare(valid, STYLE_EDIT)
    execute_job(valid)
    result = json.loads((valid / 'result.json').read_text())
    expected = {'heads': 1, 'eyes': 2, 'hands': 2, 'nails': 10}
    assert {key: result['portrait_quality'][key] for key in expected} == expected
    assert result['portrait_quality']['structural_checks_passed'] is True
    assert result['portrait_quality']['likeness_verified'] is False
    assert (valid / 'model.glb').stat().st_size > 1000
    assert not (valid / 'anatomy-failure.json').exists()
    saved = valid / 'model.blend'
    bpy.ops.wm.open_mainfile(filepath=str(saved), use_scripts=False)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    before = component_snapshot(meshes)
    eyes = [obj for obj in meshes if obj.get('anatomical_eye')]
    assert sum(bool(obj.get('artistic_asymmetry_fixture')) for obj in eyes) == 1

    # The supported helper must reject a destructive merge before mutating it.
    before_count = len(bpy.data.objects)
    try:
        join_meshes(eyes, 'eyes-merged')
        raise AssertionError('The helper merged protected anatomy.')
    except ValueError as error:
        assert 'osobne obiekty anatomii' in str(error), str(error)
    assert len(bpy.data.objects) == before_count
    verify_components(meshes, 1, 2, before=before)

    lashes = [obj for obj in meshes if 'upper_lashes_per_eye' in obj]
    assert len(lashes) == 1
    try:
        join_meshes([lashes[0], eyes[0]], 'lashes-merged')
        raise AssertionError('The helper merged protected eyelash metadata.')
    except ValueError as error:
        assert lashes[0].name in str(error)
    assert len(bpy.data.objects) == before_count

    # Raw bpy edits still reach the same strict final gate. Reproduce actual
    # Blender join metadata loss, instead of modelling it with mock objects.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in eyes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = eyes[0]
    bpy.ops.object.join()
    merged = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    try:
        verify_components(merged, 1, 2, before=before)
        raise AssertionError('The anatomy gate accepted a lost eye identity.')
    except AnatomyValidationError as error:
        assert error.report['expected']['eyes'] == 2
        assert error.report['actual']['eyes'] == 1
        assert error.report['missing']['eyes'] == 1
        assert len(error.report['removed_or_untagged']['eyes']) == 1

    # Exercise real execute_job -> finish -> atomic diagnostic file. The
    # failed revision cannot become a ready GLB by disabling scene counters.
    invalid = output / 'deleted-nail'
    prepare(invalid, DELETE_NAIL + "\nbpy.context.scene['expected_hands'] = 0\n")
    try:
        execute_job(invalid)
        raise AssertionError('The runner accepted a deleted fingernail.')
    except AnatomyValidationError as error:
        assert error.report['expected']['nails'] == 10
        assert error.report['actual']['nails'] == 9
        assert error.report['missing']['nails'] == 1
        assert len(error.report['removed_or_untagged']['nails']) == 1
        assert 'paznokcie 9/10' in str(error)
    diagnostic = json.loads((invalid / 'anatomy-failure.json').read_text())
    assert diagnostic['expected'] == expected
    assert diagnostic['missing']['nails'] == 1
    assert diagnostic['structural_checks_passed'] is False
    assert not (invalid / 'model.glb').exists()
    assert not (invalid / 'anatomy-failure.json.tmp').exists()

    # Losing a skin UV layer remains an error, with the affected object named.
    bpy.ops.wm.open_mainfile(filepath=str(saved), use_scripts=False)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    head = [obj for obj in meshes if obj.get('anatomical_head')][0]
    while head.data.uv_layers:
        head.data.uv_layers.remove(head.data.uv_layers[0])
    try:
        verify_components(meshes, 1, 2)
        raise AssertionError('The anatomy gate accepted a missing skin UV map.')
    except AnatomyValidationError as error:
        issue = [item for item in error.report['violations']
                 if item['code'] == 'anatomy_topology_or_uv'][0]
        assert issue['object'] == head.name and issue['has_uv'] is False

    return {'blender': bpy.app.version_string, 'actual_counts': expected,
            'production_asymmetric_edit_exported': True,
            'protected_join_rejected_before_mutation': True,
            'raw_join_tag_loss_reproduced_and_rejected': True,
            'deleted_nail_identified_by_name': True,
            'expected_counts_cannot_be_disabled_by_edit': True,
            'missing_skin_uv_rejected': True,
            'failed_revision_has_no_glb': True,
            'scope': 'Authored structural regression; no paid AI or likeness claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    with tempfile.TemporaryDirectory(prefix='forge-anatomy-edit-') as temporary:
        result = verify(args.output or Path(temporary))
        if args.output:
            (args.output / 'verification.json').write_text(json.dumps(result, indent=2))
        print('FROGE_ANATOMY_EDIT_OK ' + json.dumps(result), flush=True)
