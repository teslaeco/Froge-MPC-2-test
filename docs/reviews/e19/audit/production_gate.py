"""Fail-closed manufacturing preflight, separate from a visual-model approval.

Host must load a trusted audit file produced by its Blender worker and compute the
current artifact hash itself. Never accept a client/LLM's unverified audit payload.
This v1 audit is deliberately insufficient to authorize a physical order.
"""
import math
import re


def production_preflight(audit, current_sha256, process=None, target_height_mm=None, visual_review=None):
    reasons = []
    if not isinstance(audit, dict) or audit.get('schema') != 'forge.production.preflight/1':
        reasons.append('missing_or_unsupported_production_audit')
        audit = {}
    if not isinstance(current_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', current_sha256):
        reasons.append('invalid_artifact_sha256')
    elif audit.get('source_sha256') != current_sha256:
        reasons.append('stale_or_wrong_artifact_audit')
    if not audit.get('mesh_objects') or not audit.get('triangles'):
        reasons.append('missing_measured_mesh')
    totals = audit.get('totals_position_welded_per_object')
    required = ('boundary_edges', 'nonmanifold_edges_more_than_two_faces',
                'inconsistent_winding_edges_two_faces', 'collapsed_edges',
                'components_including_unused_vertices', 'unused_vertices')
    if not isinstance(totals, dict) or any(type(totals.get(key)) is not int or totals[key] < 0 for key in required):
        reasons.append('missing_or_invalid_topology_measurements')
    else:
        if any(totals[key] for key in required[:4]) or totals['unused_vertices']:
            reasons.append('mesh_topology_requires_repair')
        if totals['components_including_unused_vertices'] != 1:
            reasons.append('assembly_or_solid_union_not_verified')
    if type(audit.get('degenerate_triangles')) is not int or audit['degenerate_triangles'] < 0:
        reasons.append('missing_degenerate_measurement')
    elif audit['degenerate_triangles']:
        reasons.append('degenerate_triangles_require_repair')
    if not isinstance(process, dict) or not all(process.get(key) for key in ('technology', 'machine', 'material', 'profile_revision')):
        reasons.append('manufacturing_process_profile_missing')
    if isinstance(target_height_mm, bool) or not isinstance(target_height_mm, (int, float)) or not math.isfinite(target_height_mm) or target_height_mm <= 0:
        reasons.append('target_height_mm_required')
    else:
        dims = audit.get('dimensions_mm')
        if not isinstance(dims, list) or len(dims) != 3 or not all(isinstance(x, (float, int)) and math.isfinite(x) and x > 0 for x in dims):
            reasons.append('physical_dimensions_missing')
        elif abs(dims[2] - target_height_mm) > 0.01:
            reasons.append('physical_dimensions_do_not_match_order')
    if visual_review is not None:
        if not isinstance(visual_review, dict) or visual_review.get('source_sha256') != current_sha256:
            reasons.append('stale_or_wrong_visual_review')
        elif visual_review.get('accepted') is False:
            reasons.append('visual_or_structural_review_requires_repair')
        elif visual_review.get('accepted') is not True:
            reasons.append('visual_review_incomplete')
    # The preflight schema has no thickness/intersection/toolpath proof. A
    # manufacturing_ready=true string supplied by a model cannot override this.
    reasons.append('process_specific_engineering_checks_and_sample_not_verified')
    return {
        'can_review_visual_model': True,
        'can_order_physical_product': False,
        'status': 'requires_geometry_repair' if any('repair' in r for r in reasons) else 'requires_production_validation',
        'reasons': list(dict.fromkeys(reasons)),
        'next_action': 'repair_targeted_regions_then_reaudit' if any('repair' in r for r in reasons) else 'complete_process_specific_engineering_review',
    }
