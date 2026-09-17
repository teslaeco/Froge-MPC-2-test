# Rooted-hair attachment evidence — 2026-09-17

Scope: review-only source work on `teslaeco/Froge-MPC-2-test`. This is **not** a deployment to the private hosted Froge MPC 2 Studio and it is **not** a photographic-likeness claim.

## Change

`oracle_connector/runtime/rooted_hair.py` now exposes `hair_root_attachment_evidence()`. For meshes authored with `hair_lock()`, it measures the first generated hair ring against the evaluated scalp BVH in world coordinates. The report records the root-ring size, authored root radius, centre-to-scalp gap, minimum and maximum first-ring gap, explicit tolerances, and a boolean structural result. It always records `likeness_assessed: false`.

The helper also stores the first-ring size and root radius on each generated rooted lock so the measurement can be repeated after transforms or export/reimport work. Error diagnostics touched in this helper are now English.

## Real Blender regression

`oracle_connector/verify_camera_hair_runtime.py` contains both a positive and negative control using actual Blender geometry:

1. build a real evaluated head mesh and a closed UV hair lock fitted to it;
2. require the fitted root to pass the attachment metric;
3. move the same hair mesh 0.6 scene units away from the head;
4. require the detached mesh to fail and its measured centre gap to increase;
5. restore the mesh and retain the existing framing/origin checks.

The workflow now runs this script explicitly under the official Blender 4.3 binary in the no-paid-API job. A green workflow therefore means the attachment test actually executed in Blender rather than merely existing in source.

## Truth boundary

This metric can detect the tested class of floating-root geometry for `hair_lock()` output. It does not reconstruct a hairstyle from photographs, score identity, prove every other hair builder uses this helper, prove a visually natural hairline, prove shader equivalence, or establish manufacturing readiness. The separate `portrait_hair.py` path remains outside this specific root-ring metric unless deliberately integrated and validated later.

The private canonical `froge-mpc-2-studio` source remains unavailable in this work stream, so this source patch must not be described as live until intentionally ported to the current Site/runtime and verified there. No paid model/API/GPU call, Oracle installation, merge, Site publication, quota change, secret change, or private archive access was performed for this checkpoint.
