# E17 reference reconstruction integration

This patch changes the existing planner instructions and exports a structured,
fail-closed review report from the Blender worker. It does not train model weights,
claim improved anatomy from a CPU test, or enlarge the production worker budget.

## Integrated behavior

`runtime/scene_contract.py` appends the reusable E17 correction policy to the actual
scene planner prompt. It prioritizes registered local geometry, differentiated
teeth, root continuity, age uncertainty and explicit anatomical/image sides.
The requested eye inside a skeletal orbit is `present`, not `empty_socket`.
Current strict scene JSON remains compatible; no new required fields are injected.

`runtime/run.py` calls `reference_reconstruction.review_report` before writing
the normal core export checkpoint. Draft model export remains available. The
report is included as `result.reconstruction_review` and written separately to
`reconstruction-review.json`. Missing or malformed reference evidence keeps the
candidate in `needs_correction`, with bounded validation diagnostics; it never marks the model accepted for a catalogue.
Legacy jobs without a sidecar also remain drafts under this new report.

The reviewer/host can supply two data-only sidecars in the job directory:

- `reference-spec.json`: revision 1; reference_image and reference_sha256; age_group (unknown/child/adolescent/adult/older_adult),
  age_evidence; image_sides (frontal_unmirrored/frontal_mirrored/unknown); eyes keyed
  anatomical_left/anatomical_right (living_eye/recessed_eye_in_bone/empty_socket/occluded);
  measurements of name/reference/candidate/tolerance/unit/evidence.
- `reference-evidence.json`: current model_sha256 and reference_sha256, reimport_verified,
  same_camera_as_baseline, critical_defects (empty only after actual review), and
  views keyed front/left/right/back/face_clay/face_textured. Each view carries
  model_sha256, reference_sha256, image_sha256 and nonempty_verified. Its actual file must be
  `review/reference-<view>.png`.

The checked hashes prevent accidental reuse of another export's evidence.
Reviewer attestations are not a substitute for a perceptual measurement. This
module validates the PNG signature, IHDR dimensions (128–8192 px per axis), chunk
CRCs, image-data presence and end marker. It does not decode pixels or discover
defects visually. A ready report means
`ready_for_human_review`, with likeness_verified and catalogue_accepted still false.
The host must not allow a customer prompt to author acceptance evidence.
Sidecar errors preserve usable draft exports and allow the ordinary core checkpoint
to be saved. A missing primary model remains a fatal error.

Run the explicit refresh command below after producing the final evidence; the worker's initial
export checkpoint deliberately does not fabricate the six required review views.
The UI/catalogue approval flow is unchanged by this patch. Connecting an automatic independent visual reviewer and enforcing this report in
the host's existing acceptance endpoint are follow-up integration work, not
claimed completed here.

## Reusable exact checks and scientific boundary

`chess512_checks` transfers the verified board invariant from the existing private
ChessArena code: index X+8*(Y+8*Z), parity ((X+Y+Z)&1)==0, exactly 512 unique cells.
The actual worker now invokes `board_review_report` on every export. A missing
board specification is explicitly unverified, without asserting that the job is a
board. With a `board-spec.json`, checks use evaluated Blender mesh geometry and
actual material assignments, for either [8,8,1] or [8,8,8]. Image mirroring and color jitter must not be applied blindly
to this asymmetric character or exact board colours.

Measurement tolerances are supplied for each case. They are engineering review
tolerances, not medically established age norms. A fictional grey-haired half
does not establish age-dependent cranial proportions. The skull's supporting
structures are a useful modeling framework; observed likeness still comes from
the authorized reference, with hidden surfaces labelled inferred.

- Anatomy reading: [OpenStax, The Skull](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull).
  Reading reference only; no publication text/images copied into a training set.
- Optimization: [OpenAI, Model optimization](https://developers.openai.com/api/docs/guides/model-optimization).
  Evaluations, prompt/context improvements and actual fine-tuning are distinct.
- Private evidence and limitations: `docs/reviews/e17/research/CHESS-TRAINING-TRANSFER-E17.md`
  (parent release may map this dossier to another path).

## Verification and remaining scope

Run `python oracle_connector/test_reference_reconstruction.py` from repository root.
Sixteen CPU tests exercise recessed-vs-empty-vs-occluded eyes, unknown age, head-ratio
regression, invalid measurements, 3D board parity, missing evidence, stale hashes,
actual planner-policy import, malformed/oversized sidecars, invalid PNG containers
and mismatched image hashes. These are behavioral regression tests with
synthetic fixtures, not scored renders or trained model performance.

No paid API run, GPU allocation, neural checkpoint, medical validation, Blender
visual regression suite or production deployment was performed by these tests.
The manually corrected E17 model is a separate artifact, reviewed through its
actual exported renders. More triangles do not automatically pass any gate.


## Board worker integration

`run.py` stores `result.board_review` and `board-review.json` before its core
checkpoint. Supply a data-only `board-spec.json` with revision 1, size [8,8,1]
or [8,8,8], origin (world-space centre of cell 0), positive spacing XYZ,
position_tolerance in world units, color_tolerance in linear RGB, and palette
light/dark entries with material name and linear_rgb. Tolerances are explicit
case settings, not silently inferred. The CPU fixture in the test file is a
complete executable example.

Expose cell membership on actual geometry using either integer object custom
properties board_x, board_y, board_z (one object per cell), or a consolidated
mesh with an INT/FACE attribute board_cell_index. Values are X+8*(Y+8*Z), with
-1 for unmarked non-cell faces. Consolidated membership supports 512 cells
without exceeding the existing 256 mesh-object cap. Geometry is evaluated with
modifiers before collecting marked-face bounding-box centres and materials.

The checks detect absent/duplicate fields, invalid index, incorrect level parity,
displaced cell geometry, wrong material and incorrect flat base colour. Only a
direct active Principled surface with unlinked Base Color, or a flat non-node
material, is eligible for numeric RGB checking. Image/procedural textures and
complex shaders remain unverified; actual texture-pixel appearance still requires
rendered region checks. Do not claim this as a learned texture reconstruction model.

The planner policy is supplemented by this host-owned contract; scene JSON schema
is unchanged. The host must provide the board specification and assign cell tags
in the build/edit step. Untagged legacy boards stay unverified, not automatically
accepted by their appearance or name.

Verification on 2026-09-12: 16 CPU tests passed. Additionally,
`verify_board_review_blender.py` ran in Blender 4.3.0 on consolidated 64-cell and
512-cell meshes: measured geometry/material checks passed for valid cases and
both detected a deliberately wrong material. No screenshot similarity, texture
pixel grade, full production job, paid API or GPU training was tested.


This anatomy sidecar currently represents one character. Multi-character exports
remain available but require separate per-character reference contracts before
this gate can pass (`single_character_reference_required`). The model hash, source reference-image hash and actual review-image hashes are
bound. Every view attestation must name the same current source reference.

The updater allow-list in `apply_update.py` includes the new runtime module.
The Blender smoke report is saved as `oracle_connector/board-review-smoke.json`;
valid cases, wrong material, removed cell and missing spec were all exercised for
both supported board sizes. This is not a production deployment.


Packaging source inspection at base 5c02f9ff1243b88876fef2631346c480a70cfffa:
`scripts/package-worker.py` and `scripts/package-v33.py` both derive their payload
file lists from `apply_update.py:FILES`, so the new allow-list entry propagates
to both package types. An additional CPU check evaluates only ASSETS/FILES AST
assignments and verifies the runtime dependency is present exactly once. Existing
ZIPs were not rebuilt and Oracle was not updated.


## Explicit refresh after review

The anatomy specification must name `reference_image`, a safe PNG/JPEG/WebP
basename directly in the job folder, and its lowercase `reference_sha256`.
Path traversal, directory components and symlinks are rejected. The actual file
must be nonempty and at most 64 MiB. Its SHA256 must match the specification,
top-level evidence and each view attestation. A missing or changed reference
keeps the draft unaccepted; it does not prevent saving the draft export.

After generating the review images and recording an actual reviewer attestation,
the operator or host explicitly runs:

```sh
python oracle_connector/runtime/reference_reconstruction.py --refresh-review /work
```

`refresh_review` reads the existing result, hashes the current model/reference and
review images, reruns the gate, and updates both `reconstruction-review.json` and
`result.json.reconstruction_review`, retaining other result metadata. Each file is
replaced atomically; this is not a multi-file database transaction. It never grants
catalogue acceptance or claims perceptual grading. Missing primary model/result
remains fatal to this explicit metadata refresh. The export worker's initial report
is still a draft until evidence exists; rendering does not invent reviewer approval.

CPU regressions additionally cover changed/missing references, unsafe paths,
symlinks and refresh from incomplete to current evidence without auto-acceptance.
