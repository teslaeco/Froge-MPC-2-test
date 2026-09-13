"""Real Blender regression for effective head-material atlas detection.

Run Blender --background --python verify_skin_atlas_runtime.py -- --output DIR.
Authored geometry/material fixtures only; not a portrait-likeness benchmark.
"""
import argparse
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'runtime'))
from portrait import verify_components, AnatomyValidationError, skin_atlas_evidence


def material(name, width, height=None, grouped=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    image = bpy.data.images.new(name+'-atlas', width=width, height=height or width)
    tree = mat.node_tree
    if grouped:
        group = bpy.data.node_groups.new(name+'-group', 'ShaderNodeTree')
        group.interface.new_socket(name='Color', in_out='OUTPUT', socket_type='NodeSocketColor')
        out = group.nodes.new('NodeGroupOutput')
        node = group.nodes.new('ShaderNodeTexImage'); node.image = image
        group.links.new(node.outputs['Color'], out.inputs['Color'])
        node = tree.nodes.new('ShaderNodeGroup'); node.node_tree = group
    else:
        node = tree.nodes.new('ShaderNodeTexImage'); node.image = image
    tree.links.new(node.outputs['Color'], tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return mat


def verify(output):
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7)
    head = bpy.context.object; head.name = 'atlas-fixture-head'; head['anatomical_head'] = True
    if not head.data.uv_layers: head.data.uv_layers.new(name='UVMap')
    for sign in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, location=(sign*.4,-.9,.2))
        bpy.context.object['anatomical_eye'] = True
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    low = material('generic-skin', 512)
    high = material('reference-skin', 2048)
    grouped = material('grouped-skin', 2048, grouped=True)
    non_square = material('short-atlas', 4096, 1024)
    head.data.materials.append(low)
    cases = {}

    def check(label, expected_pass):
        try:
            result = verify_components(objects, 1, 0)
            assert expected_pass, label+' unexpectedly passed'
            cases[label] = {'passed_gate':True, 'evidence':skin_atlas_evidence(head)}
        except AnatomyValidationError as error:
            assert not expected_pass, (label, error.report)
            assert error.report['expected'] == error.report['actual']
            assert [v['code'] for v in error.report['violations']] == ['skin_atlas']
            cases[label] = {'passed_gate':False, 'diagnostic':error.report}
            if label == 'unassigned_2k_image_cannot_repair_512px_head':
                (output/'anatomy-failure.json').write_text(json.dumps(error.report, indent=2))

    # A global 2K image exists, but is not assigned to the head. This remains
    # a real failure even though all anatomical component counts match.
    check('unassigned_2k_image_cannot_repair_512px_head', False)
    head.material_slots[0].link = 'OBJECT'; head.material_slots[0].material = high
    assert head.data.materials[0] == low
    check('object_material_override_2k_is_accepted', True)
    head.data.materials[0] = high; head.material_slots[0].material = low
    check('unused_mesh_2k_cannot_hide_low_object_override', False)
    head.material_slots[0].material = grouped
    check('assigned_nested_group_atlas_is_accepted', True)
    head.material_slots[0].material = non_square
    check('shorter_image_edge_must_be_2048', False)
    head.material_slots[0].material = high.copy()
    check('copy_preserves_existing_atlas_for_local_style', True)
    assert head.material_slots[0].material.node_tree.nodes.get('Image Texture').image == high.node_tree.nodes.get('Image Texture').image
    report = {'blender':bpy.app.version_string, 'checks_passed':len(cases), 'cases':cases,
              'scope':'Real Blender geometry and node/slot assignments; no visual likeness or source-job reproduction claim.'}
    (output/'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'checks_passed':len(cases), 'blender':bpy.app.version_string}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    verify(args.output)
