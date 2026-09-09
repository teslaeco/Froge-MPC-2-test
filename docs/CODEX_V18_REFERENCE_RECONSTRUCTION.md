# Codex task — Froge MPC 2 v18 Reference Reconstruction

Implement this task as a senior Blender/3D reconstruction/AI backend engineer. Do not merely rewrite prompts.

## Problem reproduced
The v17 Oracle worker completes the green crystalline fan woman job, but visual fidelity is poor: generic face, thick geometric clothing/armor, simplified dress and fan. The worker is v17 while the UI can still report an older character standard. The goal is a materially better reference-driven 3D pipeline, not a prettier demo.

## Required v18 implementation
1. Preserve the existing trusted data-only scene contract: model output must remain validated JSON; do not restore arbitrary model-generated Python execution.
2. Add an explicit reference-person/couture representation to the trusted runtime. A fitted dress must be generated from the anatomical body surface or a close body-following proxy, with bounded physical offset/thickness. It must not be produced as a bulky torso shell.
3. Add floor-length dress/skirt continuation for cropped references while retaining complete anatomical legs/feet underneath. Missing/unseen geometry is reconstruction, never claimed as observed reference detail.
4. Add thin surface-following decorative/crystalline panels with bounded thickness and no floating geometry. Preserve collar, shoulders, waist/belt and visible garment identity.
5. Add reusable compact prop-detail support suitable for the fan: model one rotor/turbine assembly and instance/copy it around the fan. Preserve handle, fan thickness, repeated devices and pendant/chain when requested. Avoid giant raw vertex arrays and avoid output truncation.
6. Improve feminine updo support without helmet hair. Preserve existing anatomy, five-finger hands, eye alignment and skin UV pipeline.
7. Add explicit characterStandard/version metadata so UI and Oracle cannot misleadingly show worker v18 with character standard v15/v17.
8. Add geometry QA for reference characters: complete head-to-foot bounds, two legs/feet, hands where present, garment thickness bounds, no obviously detached dress panels, and GLB export/reimport. Do not call similarity verified unless a real image-comparison metric was actually run.
9. Keep GLB size/runtime bounded. Do not regress existing rapper, architecture, oak/garland, exports, pairing, API-key privacy or rollback updater.
10. Set connector version to 18 only after tests are updated.

## Acceptance test for the supplied green-fan reference
The generated model must clearly read as an elegant woman in a fitted dark teal/emerald floor-length couture dress, not armor. Torso/waist silhouette stays close to anatomy. Angular shoulder/collar details remain thin accessories. Full legs/feet exist. The large fan has layered green/cyan facets and repeated mechanical rotor details built compactly. Hair is a sculpted brunette updo with a separate emerald ornament. Validate front, 3/4, side and back renders from the actual GLB. Record limitations honestly: one front reference cannot establish exact unseen back/legs or exact identity.

## Tests / evidence required before merge
- Python unit tests for new schema/runtime validation and version metadata.
- Existing Python tests pass.
- Actual Blender generation of a v18 couture fixture.
- GLB export and re-import pass.
- Record bytes, vertices, triangles, objects and generation time.
- Produce review renders front, 3/4, side and back from that exact GLB.
- Do not claim visual similarity percentage without a measured comparison.
- Update docs/WORK_CHECKPOINT.md with exactly what was run and what remains unverified.

Make the smallest architecture change that genuinely enables this quality step. If the existing person primitive cannot support the fitted garment correctly, extend trusted local runtime rather than compensating with more prompt text.