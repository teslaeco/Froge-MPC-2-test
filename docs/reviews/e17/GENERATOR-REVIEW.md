# Independent review of reconstruction workflow changes

Review scope: local `generator-upgrade/oracle_connector/runtime/reference_reconstruction.py`, the integration in `run.py`, and policy inclusion in `scene_contract.py`. This document reports code inspection; it is not a completed production training run or an end-to-end Blender execution log.

## What the inspected implementation does

- Supplies reference-reconstruction instructions to the scene-generation contract.
- Validates explicit side/age/eye-state specifications and author-supplied measurements with per-case tolerances.
- Compares required measured values and checks model/reference/render hashes, required review views and explicit reviewer attestations.
- Reports `needs_correction` or `ready_for_human_review`, while keeping `likeness_verified` and `catalogue_accepted` false.
- Records the learning method as instructions, constraints and evaluations, with `weights_updated: false`.

The distinction matters: a reviewer-authored measurement or nonempty-image attestation is evidence supplied to the workflow. The current module does not itself infer all anatomical landmarks, decode human likeness or teach Astra new weights. PNG container checks protect the review file path/structure; they are not a perceptual image grader.

## Review observations raised to the implementing agent

| Observation | Why it matters | Review status |
|---|---|---|
| Review report is generated before requested new render views | The first report can remain incomplete until reviewer evidence is written and explicitly refreshed | Fixed with explicit `--refresh-review JOB_FOLDER` operator/host entry point after evidence creation; it updates result/review and does not grant acceptance |
| Model hash was bound but reference hash was absent | A changed reference should invalidate a stale comparison | Fixed: safe reference basename, actual file SHA, specification/evidence/view reference bindings; absent or changed input cannot pass |
| Boolean values can equal integer board indices in Python | An exact board contract should reject `true` as index `1` | Fixed in both board helpers with strict integer typing; inspected in updated source |
| A single-head count is applied by the reference review helper | Multi-character exports need explicit scope | Scope is one reference character; groups remain unverified/unsupported and cannot be accepted by this gate |

The updated source also invokes `board_review_report` from the actual worker. It reads tagged evaluated Blender geometry, including consolidated meshes with a face-level cell index, and verifies exact 64/512 cell counts, positions, parity and eligible flat material colours. Untagged boards and image/procedural texture colours remain unverified. This does not infer cell identity from arbitrary Meshy geometry without the host-supplied contract and tags.

The implementing agent reports 16 passing CPU behavioral tests and a Blender integration smoke on 64/512-cell meshes. The Blender report covers valid geometry, wrong material, missing cells and absent specification. The added CPU cases cover changed references and explicit review refresh. These are constructed test fixtures, not a measured improvement in reference-to-character generation. The review provenance file records the inspected source/report hashes.

The final inspected implementation addresses the specific hash/refresh/type issues raised during this review. Remaining integration boundaries are explicit: single-character reference scope, host/reviewer-authored visual evidence and no automatic pixel/likeness grader. The refresh entry point does not itself generate the missing evidence or accept a catalogue item.

## Claims suitable for publication

“The workflow now carries explicit reference constraints and retains failed correction cases for future prompts. It checks export/review evidence and keeps visual approval separate.”

Claims not established here: retrained Astra weights, completed L4 training, automatic full-anatomy recovery, measured improvement on worldwide datasets, production-ready game animation, or an accepted manufacturing asset.

The model E17 edit and this generator policy are separate deliverables. A render from a local correction script demonstrates that edited asset, not the general success rate of the generator for new references.
