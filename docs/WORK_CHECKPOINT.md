# 2026-09-12 — v33 reference anatomy correction in native verification

Live Oracle is v32 (confirmed in Studio), not v29. Incident job 49ac337d-0a00-4c94-96ef-d8dfa716d435 is the half-living/half-skull photo with the correct brief. Added explicit sided eye intent, living-eye preservation, human-landmark fitting exclusion for declared nonhuman face, and actual orbit ray checks before acceptance. See docs/reviews/v33/STATUS.md and POLECENIE-CODEX.txt. Package built; native CI pending. No paid generation, completed skull reconstruction or Oracle v33 installation claimed. Site47 unchanged.

# 2026-09-12 — v32 repair tested and saved; installation and Site fix pending

Verified worker source: 2c4ca6e78b4f77a2011e6c7a3211caf923ca18f3.
CI run34685206191 passed Python3.9 and3.12 (98 tests each), real pinned Codex
roundtrip, delayed final MCP read, real Blender4.3 build/render/GLB/FBX,
material edits and anatomy diagnostics. See docs/V32_RESUME_REPAIR.md.
No paid generation or likeness approval. Oracle live v29; Site47 unchanged.
Canonical Site clone fails HTTP500; its UI race patch/tests remain unapplied.
Oracle console navigation and refresh timed out; no terminal session obtained.
Saved download froge-v32.zip (366626bytes), Library libfile_5c8bbf0e8f7c819190baf5788d6a05d1 v0.
Saved FORGE-v32-instrukcja.md, Library libfile_579ab5195a508191b2705d47db36ada8 v0.
Both saves succeeded, local identity applied. Package is NOT installed on Oracle.
Next: restore Site source/apply UI tests/deploy; install v32 on existing Oracle;
restore intended brief from its original source; test distinct paid generations
only within approved budget. Current saved job prompt contains a status message.

## 2026-09-11 — v24 timeout recovery fix packaged

- User reported the generic timeout screenshot. Live Studio confirms Oracle v23.
  The v23 catch-all erased the failing stage; the precise incident stage and
  failed job ID cannot be recovered from that screenshot. No new paid job run.
- Responses streaming now returns at response.completed, independently of HTTP
  socket closure; incomplete responses remain failures with retained draft data.
- Photo planning: 900 s (was 600); text planning remains 600; visual review keeps
  240 s. Token caps and no automatic retry after timeout are unchanged.
- Blender writes atomic, hash-bound checkpoints after core GLB and interchange
  export. On timeout the current verified GLB can survive unfinished exports or
  review. Each build clears its old checkpoint; stale/corrupt files are rejected.
- Identical retries after a timeout reuse a valid saved scene without new AI.
  Error messages and failure.json identify the phase; failure timings persist.
- 58 Python test executions passed, including real local SSE with an open HTTP
  connection, partial-stream failure, current/stale model checkpoint behavior,
  saved-plan recovery and updater rollback. Native Blender 4.3 verified exports,
  projection and checksums of geometry/projection model checkpoints.
- Complete froge-v24.zip: 55 source-verified files, 15,510,834 bytes, SHA-256
  523ffc25787a4aab7a4baa6f6ce733e21280597c6055969b9b1dc53c82af7e58.
  ZIP and FORGE-v24-instrukcja.md successfully saved for download.
- v24 is NOT installed on Oracle in this session; Site remains unchanged.
  No claim of successful recovery of the user's live job or improved likeness.
- Runtime source parent: 93720297e3f07c5b4c5beb7c916ca4555b9eee68.
  Install command is in docs/V24_TIMEOUT_FIX.md. PR #9 remains unmerged.

## 2026-09-11 — v23 download delivered after explicit user retry

- User explicitly requests the v23 download and Oracle command again, with an
  urgent contest deadline and limited funds. Reused the already verified ZIP.
- Confirmed successful saves for froge-v23.zip and FORGE-v23-instrukcja.md;
  both ordered results succeeded and local identity metadata was applied.
  No regeneration or archive change: 15,508,252 bytes, SHA-256
  f83e549f9aad15ba521a0f2e017c1c8dc2f8702a989ac9a0fdaf7661de9e792c.
- Delivered the actual ZIP link and the two Cloud Shell install commands.
  Installation remains user-side; no FROGE_V23_OK confirmation this turn.
- Current Sites metadata confirms Site version 38. Fresh canonical-source
  clone with a refreshed credential exceeded the 45 s limit (exit 124).
  No Site source modification/deployment or audience change occurred.
  The publication does not declare a Sites HTTP MCP server; existing WebMCP
  page tools are a separate integration.
- No new paid AI generation, new model or additional limit increase was made.
  Next required evidence: Oracle FROGE_V23_OK and actual v23 reference renders.
- Runtime source is saved in PR #9 at 335409a4587295f9534e8e6d4c99d3b3410d6e81.
  Package is available; visual acceptance and PR merge remain pending.

## 2026-09-11 — v23 freeform and photo projection update prepared

- User requests broader, more faithful reconstruction for different uploaded
  objects while retaining Astra + Blender. Meshy remains removed.
- Scene v2 adds bounded surface_grid and contour_loft geometry. New photo jobs
  require camera/mask reference_views, with source hash checks, multiple views,
  face orientation and BVH depth tests. Hidden faces retain their materials.
- Added per-face colour UV consolidation for FBX/OBJ, private quality reports,
  600 s planning + 240 s visual assessment, and 600+300 s Blender budgets.
  A successful file is never promoted to automatic likeness acceptance.
- 62 Python test executions passed. Native Blender 4.3 verified manifold
  surfaces, front/back image assignment, occlusion rejection, UV restoration
  and FBX reimport. The separate installer fixture has 196 vertices / 364
  triangles and correctly projects two faces. These are authored test assets,
  not new Astra generations or proof of universal reconstruction quality.
- Full froge-v23.zip: 54 source-verified files, 15,508,252 bytes, SHA-256
  f83e549f9aad15ba521a0f2e017c1c8dc2f8702a989ac9a0fdaf7661de9e792c.
  Packaging compiles the Python files, verifies payload hash and ZIP integrity.
- Oracle v23 is NOT installed; last confirmed worker v22 and Site v38 remain.
  No new Site source checkout/deployment was attempted here after the prior
  canonical Git HTTP 500. No new paid AI generation was started this stage.
- Artifact save returned HTTP 502 with uncertain commit outcome; filename
  lookup found no matching new artifact. No duplicate write was attempted.
  Complete ZIP and instructions remain in scratch/deliverables; source and
  packager are being saved to the authorized GitHub PR.
- Source starts from PR head 592710412a96c972c0437ab016aab3967428445b.
- Report: docs/V23_UPDATE.md; execution receipt: docs/V23_EXECUTION.json.
  After installation, real Astra tests on a person, hard-surface object and
  organic object remain necessary. PR #9 remains open pending visual acceptance.

## 2026-09-11 — actual Astra v22 reference test completed; visual acceptance failed

- Native FBX review found colour loss from vertex-colour/photo shader mixes.
  Local emission bake to a new 4096px atlas and explicit UV ordering restored
  main colours. The atlas adds no source detail; fine texture/shader differences
  remain. Final local FBX is 31,402,300 bytes; actual-model reimport retains all
  594,064 triangles and 103 UV objects, bounds error 8.94e-8 m.
- Fixed invalid RNA references when removing UV layers in scene_exports.py;
  native actual-model export/reimport and 11 export/material tests pass.
  This small code fix is not installed on Oracle or in the prior v22 ZIP.
  Original installer verification applies to its packaged source snapshot.

- Live job 1dc26a4a-f8f4-480b-ba51-524d558ff355 succeeded in 824.4 seconds:
  AI 600.0 s, Blender 224.1 s. Additional Astra visual review did not finish
  within the shared budget; the original generated model was retained.
- Downloaded actual Oracle GLB, 26,650,972 bytes, SHA-256
  2cc3c67497a55e9c1d967ceba84d21b6cd5172cb4529759392134c4aaca63fb2.
  594,064 instantiated triangles (589,492 in unique meshes), 103 mesh objects,
  94 unique meshes, 102 unique UV primitives, 12 embedded image assets;
  maximum edge 2048 px. The supplied reference remains 1229x1536 in the GLB.
  This result has no 4K or 8K texture maps.
- Independently rendered actual GLB front/profile/back/full in Blender 4.3,
  640x800, Cycles 24 samples. Visual quality is NOT accepted: generic face,
  helmet-like updo, skin-colour contamination on the collar, simplified rear
  cape and material response/proportions differing from the reference.
- GLB metadata confirms registered_reviewed_reference, 478 saved measurements,
  live_face_detection=false. This successful known-image fit is not evidence
  of arbitrary-photo reconstruction. Unseen back/lower body are inferred.
- PR #9 remains open: user asked to merge when green, but visual acceptance
  failed and GitHub has no CI workflows/check-runs. Functional local tests
  passed, including 11 additional export/material tests in this review.
- Site source clone with a renewed repo-scoped credential again failed with
  HTTP 500 / expected packfile. No Site deployment or audience change. Site
  remains v38; its /exports route returns not found although the GLB exists.
- Download acknowledgement failed in Browser, but the original job-named GLB
  was transferred to the shared downloads directory and its complete GLB
  length/header were validated. API identity-less access returned 401; no
  authentication rules were changed. No duplicate paid generation occurred.
- Saved MCP2-test-Astra-v22.zip (71,859,937 bytes, 40 files) and three actual
  GLB render images. The package contains original GLB, local FBX, original
  and FBX texture images, verification data and the review. Follow
  docs/reviews/astra-v22-live-2026-09-11.md for findings and next changes.

## 2026-09-11 — v22 installation confirmed; live reference generation and PR review

- User screenshot shows FROGE_V22_OK. Live Studio independently confirms Oracle
  v22, photo support and gpt-6-astra using the existing OpenAI connection.
- Uploaded the exact supplied 1229x1536 emerald character image through Studio;
  submitted one new photo job: 1dc26a4a-f8f4-480b-ba51-524d558ff355.
  View is three-quarter; prompt is 1326 characters. The job is generating.
  No Meshy connection, repeated submission or replacement by an older model.
- PR #9 title/body now describe v22 and actual validation. Head at review was
  da985b79a4fd080bf25b019473584ee5bc9571ad; GitHub reports clean/mergeable,
  zero reviews, zero check runs/statuses/workflow runs. No .github workflows
  exist in this tree. User explicitly authorizes merge when checks permit.
- 11 focused export/material-repair tests additionally passed in this review.
- Source review: face has seven bounded parameters plus optional landmark fit;
  couture uses authored garment tools. Max effort is not native image-to-3D.
- WebMCP tools expose local scene editing, not the Oracle job lifecycle/export
  report. The current browser reports modelContext unavailable; UI works.
  Recommend authenticated job/status/cancel/export/quality tools and CI, then
  broader image-conditioned geometry/UV/material fitting for general likeness.
- Site remains v38. No Site deployment or audience change performed here.
  Await the live job, inspect its actual GLB/textures and save the outcome before
  claiming likeness. Do not submit a duplicate while this job is active.

## 2026-09-11 — user correction: Astra only; Meshy integration retired in v22

- User explicitly clarified: Meshy was a quality comparison, not permission to
  replace Astra. Current requirement is Astra + Blender using existing OpenAI.
- User screenshot confirms FROGE_V21_OK on Oracle; Meshy was not connected.
- Removed the external provider implementation/UI and photo-readiness requirement.
  Retired configuration/resume endpoints reject without forwarding credentials,
  uploading images or calling another provider. Existing assets remain.
- Restored Astra photo planning, identical-input offline render recovery,
  per-image facial measurements and original texture/portrait compatibility gates.
- Official gpt-6-astra docs confirm max effort; image calls now use max and a
  24000-token ceiling, retaining the cumulative 600-second AI budget. This is
  not a newly trained 3D model or proof of photographic output quality.
- Actual review set now includes front, three-quarter, face, side and back.
  Original/candidate backup and bounded single refinement remain in place.
- 58 Python test executions and 63 UI/API tests passed; generator typecheck
  passed. Native Blender rendered five real 640x800 test-cube views. No paid
  AI generation, new character, likeness acceptance or Site deployment here.
- Complete froge-v22.zip contains 48 byte-verified payload files and passes ZIP
  integrity. Installer uses saved OpenAI, no third command or additional key;
  progress appears every 15 seconds. See docs/ASTRA_EXECUTION.json.
- V22 is not installed on Oracle yet. Previous Site source Git HTTP 500 was not
  claimed fixed. Source changes build on PR #9 head 14701654a8de83fb8b90605f2175d5ddde6a2902.
- Prior Meshy notes below are historical and superseded by this explicit request.

## 2026-09-11 — v21 image-to-3D integration and installer completed; live execution blocked

- General photo path now uses Meshy 7 Ultra (single/multi view, actual JPEG
  bytes, preserved pose, no image enhancement or remesh, 4K/8K PBR requested).
  No new photo-to-template fallback; text and explicit historical replay remain.
- Meshy is configured separately via authenticated settings or getpass over SSH.
  Readiness is independent of Astra. Remote task intent/ID persists; ambiguous
  paid submissions are not repeated, and free result/export resume is explicit.
- Original GLB and PBR maps retained, native FBX/OBJ/STL/BLEND exported, preview
  textures reduced only in a separate GLB when necessary. Added authenticated,
  streamed downloads for master, FBX, PBR archive and other completed formats.
- 50 Python tests plus a new PBR-download test and 66 UI/API tests passed.
  Typecheck of the materialized generation modules/dependencies passes. Full
  deployed Site build was not run: its canonical Git clone returns HTTP 500.
- Native Blender 4.3 check: 732 triangles retained across master/preview/FBX/OBJ/
  STL, distinct-axis bounds preserved within 0.000001 m; texture 8192x64 remains
  full size in master/FBX/OBJ while preview is 4096x32. These are authored TEST
  objects, not neural generation or photographic likeness evidence. Separate
  12-triangle textured installation fixture also passes native import/exports.
- Full v21 installer: 49 payload files, rollback-safe worker install, secure
  optional --connect-meshy. It tests a cube without calling paid AI. The update
  package is not an installed worker. See IMAGE3D_EXECUTION.json for results.
- No Meshy API connection found locally or in Site settings. 0 paid AI calls.
  Oracle browser reports Site Unavailable; no SSH key available in this session.
  Site source clone with renewed credential returned HTTP 500. Site stays v38;
  no Oracle install, Site deployment, audience change or neural model produced.
- Backend checkpoint is 759ac60f169ca7d694064a0cd56b5c0f8cb1a85f on PR #9.
  Final integration source follows on the same branch. Do not regenerate or
  re-deliver the old template model as a successful image-to-3D result.

## 2026-09-11 — image-to-3D backend saved; integration in progress

- User rejected procedural/composition-specific results. Photo path now requires
  Meshy 7 Ultra and sends each subject's actual image bytes; no template fallback.
- 37 offline provider/HTTP/render/export tests pass, as does Python compilation.
- Full input GLB preserved; native Blender export stage added with separate
  preview textures. Native import/export fixture and frontend wiring still pending.
- Backend source saved on PR #9 as 759ac60f169ca7d694064a0cd56b5c0f8cb1a85f.
- No Meshy connection found. No paid API call, neural model or likeness proof.
- No Site deployment, Oracle install or access change. Site remains v38.
- Continue docs/CODEX_IMAGE_TO_3D.md, frontend settings/downloads and v21 installer.

## 2026-09-11 — geometry r2: model, exports and installer verified and saved

- Implemented the user's requested repair, starting from the actual completed
  Site job 3960f64c-eb60-432b-b1aa-8f831f7bf613 and its exact 1122x1402 photo.
  Original GLB (23,801,248 bytes, 588,028 triangles) is retained locally.
  Node metadata confirms the user's model had no measured face fitting.
- New shared cervical pivot keeps the skull, eyes, hair and jewellery together;
  lower neck remains anchored. Rear/side cape now has a curved cross-section,
  shaped hem, fitted shoulder yoke, thin seams and a softer shared cloth finish.
  Existing 16-material budget is retained. The first extra-material variant was
  rejected by the real runtime, then corrected and regenerated successfully.
- Registered 478-point measurement is reused only after the frame, face, fan and
  garment agree with this previously measured composition, with SHA binding.
  This is explicitly NOT live face detection for arbitrary photos. Different
  compositions do not inherit these points. Face likeness remains approximate.
- Final native Blender 4.3.0 build: 34.47 s, 305,299 vertices, 594,064 triangles,
  103 objects, 14 image datablocks; 38,915,808-byte GLB. No paid AI request.
  Measured residual RMS 2.3776 -> 0.3020 mm, no inverted fit triangles. This is
  control-fit error, not proof of identity. Rear/lower body remain reconstructed.
- Actual exported GLB rendered from front, profile, back and full three-quarter;
  actual FBX front rendered after import. Neck/face/cape improvement inspected.
  Remaining: exact facial likeness, updo and lip refinement, source lighting in
  colour maps, inferred hidden shape, multi-material shader differences in FBX.
- Native FBX, OBJ and STL reopen with exactly 594,064 triangles; world-bound
  error below 0.0000003 m. FBX/OBJ include the actual baked face-colour texture.
  This verifies exports, not full shader equivalence or commercial print readiness.
- 43 unique focused Python tests passed across runs. The dependency/package test
  was rerun successfully after rebuilding the final archive. Full v20 installer
  has 46 byte-matched files, compiles and passes ZIP integrity; capability gate
  requires portraitGeometryRevision=2 and registeredReferenceRevision=1.
  Payload SHA256: 8ab5c5e795dd83dc8e46ab8714780b7497460cc28af6235f1d2b93c9af88f415.
- Durable source checkpoint parent e0ad28a7903745404238e3b293b76cbeed0b2747
  is on existing PR #9. Final source correction and preview helper follow it.
  No merge, Oracle installation, Site source deployment or access change here.
- Four artifact saves succeeded with local identity metadata:
  froge-v20.zip (15,492,429 bytes): libfile_13dffd55f64c819193134b69232c0de0 v3;
  MCP2-model-geometria-r2.zip (153,448,370 bytes): libfile_211a340af5a48191b419584acb9f05c4 v0;
  MCP2-model-geometria-r2.glb: libfile_fbccd9fab5c48191b45f296ab7f9f33c v0;
  MCP2-porownanie-geometrii-r2.html: libfile_29a7cceab9fc819181c7293cc557e5d8 v0.
  The ZIP includes every model format, textures, provenance and native reports.
  HTML has nine complete embedded images, actual 640x840 renders, matching
  cameras/lights and normalized 1.88 m comparison height (24 vs 32 samples).
- Authored replacement scene uses the exact user-job photo; the original Oracle
  plan JSON could not be accessed. This distinction is recorded with the model.
- Full model imports successfully in the existing Site v38. Catalog rejects
  files above its 24 MB cap, including re-export of a separate 1024 px preview.
  Separate 512 px preview (19,790,144 bytes, same 594,064 triangles) successfully
  saved as a draft named Szmaragdowa postac - poprawiona szyja i plecy (podglad).
  Save and name confirmed after reloading the Site catalog. Download route:
  /api/commerce/models/a6483e30-bd26-4e65-945a-ab528fd079f8.glb
  Full masters retain their original textures. No store listing was published.
  Oracle Console remains unavailable here; installing the saved update package
  is still needed for future generations.

## 2026-09-11 — OpenImageDenoise review failure: verified fix

- Screenshot and current Site DB confirm failed job
  4c950a69-8729-4162-ab80-c9860fa76648, updated 2026-09-11T14:10:30.420Z:
  runtime/review_views.py forced denoising, but the Oracle Blender build has no
  OpenImageDenoise support. This occurs after the export stage in runtime/run.py;
  the actual Oracle artifact files have not been inspected from this session.
- Parent remote PR #9 head: a88207de480a5f982edc0ac69032a19e41c0be69.
- Added OIDN build detection; CPU OIDN/12 samples when supported and 64 CPU
  samples without denoising otherwise. Recognized capability failure retries only
  that frame once. Atomic PNG publication and explicit review settings report.
- Optional preview failure no longer discards validated model exports. It records
  an unavailable review and removes stale PNGs; missing views stop visual AI calls.
- Exact retry after the latest matching OIDN failure now reuses its validated saved
  plan and original photos, with no AI request even if AI is offline. Different
  prompt/photo metadata/bytes do not reuse it. Original failed job stays intact.
- Worker health and installer require reviewRenderRevision=1. Installer now also
  exercises three real GLB preview renders, retaining the existing resource budget.
- 56 focused Python tests PASSED, including identical-photo/offline recovery,
  changed-input rejection and idempotency. Native Blender 4.3.0 PASSED: three
  actual 640x800 PNGs at 64 samples/2 CPU threads with the unsupported-OIDN
  branch forced; all images decoded. GLB/BLEND/FBX/OBJ/STL remain valid files
  after an injected optional preview failure. Local Blender includes OIDN;
  this is a tested compatibility branch, not an Oracle ARM installation test.
- Complete updated froge-v20.zip verified: all 45 embedded source files match,
  Python compiles, ZIP integrity passes, health revision and three-view installer
  gate are present. Archive bytes: 15481101.
  Payload SHA256: 7ca25b99f5ca0eb9ae07e7090bf09a17e9190def3c660bd053080e01d2f38ab8.
- No paid AI calls, Oracle installation, Site deployment or public access change
  performed here. Existing installation-access block persists. Complete and save
  the package, install on Oracle, then retry the unchanged failed request.

## 2026-09-11 — missing material error repaired (materialRepairRevision 1)

- User screenshot and the existing Site DB both confirm failed job
  6fe3f4c4-93ce-4e00-b66c-e0cb9f01bb8c: `Nieznany material: eyes_grey_green`.
  The raw Oracle scene response was not accessible; do not claim its exact palette.
- Based on PR #9 head d98c38dc507b8d88019020b94fd285f7dbf3bc1a. Validator now
  reports all missing bindings. The existing second planning attempt repairs only
  an eight-slot palette and required bindings; original geometry is retained,
  then full scene/anatomy validation runs. Original request/photos are retained.
  Invalid repairs fail without a third planning attempt. Both AI providers receive
  the constrained repair schema; no paid API requests were made during this fix.
- 53 focused Python tests PASSED, including exact eyes_grey_green reproduction,
  original geometry preservation, nine references sharing eight slots, invalid
  bindings/colors/duplicate fields, anatomy enforcement, both providers, and real
  SQLite worker lifecycle with mock AI/Blender. The test FROGE_UPDATE_OK output is
  from a mocked update test, NOT proof of an Oracle installation.
- Worker health advertises materialRepairRevision=1; generated installer requires
  this value from the running service. Original scene, palette response and
  material-repair.json remain in job state. Color fidelity is not independently
  verified. Existing failed jobs are not automatically rerun.
- Complete froge-v20.zip rebuilt; all 45 embedded files exactly match source,
  Python files compile, ZIP integrity and installer capability check pass.
  Payload SHA256: ccc8064d1a836d9673c379aed6739dfe684f82862e4cec81dd77717057145182.
- This source/package fix is NOT installed on Oracle. Existing Site remains v38
  and owner-only. Prior source-clone HTTP 500 and inaccessible Oracle Console
  prevent installing/deploying here; the current worker did respond to this job.
  Preserve current Site and authorized public-release goal. Next: install updated
  worker, verify materialRepairRevision=1, then retry and inspect the real model.

## 2026-09-11 — generator and downloadable exports executed (after 5138178)

- Continued at the user's instruction to execute the work directly. Parent remote
  commit: 51381781f42130e0508afb7ac0e0ccd5db98bf20, same PR #9, no merge.
- Changed the reusable portrait/couture runtime: neutral lid-template alignment,
  raised/swept crown, finer procedural hair fibres, darker hair and closer collar.
  Rebuilt the original authored scene with 478 measured reference landmarks in
  native Blender 4.3.0. No paid AI request or new Astra-generated scene was made.
- Actual new GLB: 39,043,816 bytes, 591,960 triangles. Initial measured build was
  31.27 s / 1,339,412 KiB peak RSS, before the later standalone skin-bake exports;
  this is not an Oracle performance measurement. Inspected equal-camera front
  renders before/after and profile. Visual improvement remains modest; this is
  not accepted photographic likeness or newly recovered 8K texture detail.
- Native export now additionally bakes the single-material anatomical head's
  image-times-vertex colour via EMIT into a 2048 atlas, without new scene lighting.
  Source illumination remains. Other complex shaders and projected garment UVs
  are not declared equivalent; they need separate texture baking/unwrapping.
- Actual FBX render exposed blank eyes despite correct texture bytes. Fixed native
  FBX's missing UVSet bindings by temporarily placing the colour UV channel first
  on single-material meshes. Actual render caught a fan regression when doing this
  across multi-material meshes; those keep original UV order and report a limitation.
  Extended the packed-image native fixture with a decoy first UV layer; exact
  geometry/UV/texture/material comparisons, original-state restoration and STL
  millimetres pass. New reusable existing-asset reimport and rendering scripts added.
- Added authenticated completed-job export listing and downloads (FBX, OBJ ZIP,
  STL, BLEND, scene JSON). OBJ includes only declared texture files. Hash/size,
  state, missing-file and symlink checks reject incomplete or changed output.
  Downloads never call AI. Existing GLB 48 MiB gate remains; interchange aggregate
  download limit is 256 MiB. Health now reports interchangeRevision=2.
- Fixed visual-refinement rollback/cancellation to restore every format, texture
  folder and review view, and remove candidate-only artifacts.
- 78 focused Python tests passed, including real HTTP, archive integrity, queue,
  rollback, update, photo fit and geometry checks. A mocked update test prints
  FROGE_UPDATE_OK; that message is NOT evidence of a real Oracle installation.
- Added scripts/package-worker.py to build complete fresh/update/one-file worker
  packages independently of frontend/add-on assets. Installer compiles and payload
  bytes match all 45 runtime files; installation also checks all generated formats
  and the new health revision. Reproducible binary packages are deliverables, not
  committed source. Packages have not been installed on the actual Oracle VM.
- Existing Site still v38/owner-only, source 868131794689da730f851a8845ff951f2da8c92b.
  Valid fresh-credential source clone attempts (including protocol v0) return
  HTTP 500 / expected packfile. Oracle Console browser access returns Site
  Unavailable. The source-access and installation blocks persist; no existing UI
  was replaced, no Site deployed and no public access switch was performed.
- Publication authorization persists after required fixes. Remaining: recover
  current Site source, connect export downloads and explicit example selection,
  install worker, perform a real new-prompt generation, inspect materials and
  likeness, then publish the same Site to the authorized public audience.

## 2026-09-11 — export texture repair executed in PR #9

- User explicitly asked this assistant to execute the continuation, not just draft it.
- Starting remote head: a8089e19f20eadc4b25cc54d23a9c7c26193da68, PR #9 branch
  codex/przygotuj-i-opublikuj-mcp-2, base codex/reference-fidelity-4k-8k.
- Reproduced original native FBX image aliasing and missing OBJ textures using the
  unchanged model.blend from FORGE-modelka-4K.zip. Repaired packed/generated image
  transfer with unique files and temporary file-image bindings; original node
  bindings and selection are restored. Optional failures preserve GLB/BLEND and
  produce an explicit partial report. JSON is listed only when written; runtime
  uses the current output folder's scene.json.
- Native Blender 4.3.0 two-image fixture PASSED: FBX with only the FBX file available,
  relocated OBJ+MTL+textures, exact image bytes/materials, vertices, UVs, triangles,
  master state and STL millimetres. Five focused failure-handling tests PASSED.
- Actual unchanged character: FBX, OBJ and STL reimport with 592136 triangles.
  FBX/OBJ now recover 13 distinct material image entries instead of aliased/missing
  maps. Fourteen original images are delivered. The skin atlas behind a complex
  shader is not directly bound by these native exporters; this is still an
  appearance limitation, not a claim of complete PBR or reference likeness.
- Native fixture and verification report are committed with this checkpoint.
- Current Site remains owner-private v38. Another authorized clone of its source
  repository failed with HTTP 500 / expected packfile. Do not overwrite current UI
  with this older GitHub mirror. Sites reports no server-MCP declaration; existing
  browser WebMCP and the product name MCP 2 are separate from that capability.
- No Oracle installation, Site deployment, paid AI call or visual geometry fix is
  claimed in this checkpoint. Continuing generator/model work next; source access
  and Oracle installation remain to be resolved before public release.

# Generator upgrade verified — follow-up to 2dd0fb9

## 2026-09-11 — interchange export source checkpoint; deployment still blocked

- Added one-master-scene worker export paths for FBX, OBJ+MTL and millimetre-valued
  STL alongside the existing GLB/BLEND and validated Froge scene JSON. The export
  report states axis, rig, texture and shader boundaries and does not call STL
  textured or print-ready. `scene_exports.py` is included in the worker manifest.
- Two isolated unit tests pass and production typecheck passes. Native Blender is
  absent from this restored workspace, so FBX/OBJ/STL reopen tests and an updated
  worker ZIP were **not** completed here; this source checkpoint is not an Oracle
  installation or a verified multi-format artifact delivery.
- The checkout has no Git remote or GitHub credentials. The available toolset has
  no Sites or Oracle operation. Current Sites v38 source therefore could not be
  recovered, renamed, made public or redeployed, and Oracle health/capabilities
  could not be queried. Preserve v38 rather than publishing this older UI.
- The requested GPT-6 Astra runtime/reasoning setting is not exposed to this
  session and was not claimed. No AI API call and no new cost were incurred.
- Next required stage: recover Sites v38 source and native Blender, run every
  export/reimport comparison (FBX importer identified), generate a second prompt,
  then install with rollback, verify Oracle health/generation, and only afterward
  publish the same Site publicly as MCP 2 and test anonymous desktop/mobile access.

## 2026-09-11 — requested model preview; website update blocked

Sebastian confirmed the Oracle v20 installation with FROGE_V20_OK and a passing GLB test. His next studio screenshot reports Oracle v20 connected, but still displays a previous chess king. He requested the model from FORGE-modelka-4K.zip to be added to the website preview.

Verified this turn:
- The supplied ZIP contains the expected FORGE model. GLB: 39,711,312 bytes; SHA256 63d9924795454898e60f52fe8bce87c5906e60016f06211c19b0f2f88078b99b.
- Native Sites get_site confirms the same owner-private site and version 38. Version 38 source is 868131794689da730f851a8845ff951f2da8c92b. No newer version was saved or published this turn.
- The previous local checkout was removed by workspace maintenance. Three attempts to clone the existing Site's returned source repository (normal, shallow, and filtered shallow) all failed with HTTP 500 / expected packfile. The server reported that filtering was unsupported. No access policy was changed and no replacement Site was created. The Site commit is not available in the GitHub mirror either.
- Consequently, the button and direct link proposed for the website were NOT added. Restoring current Site source access is required before editing/publishing its existing viewer. Do not overwrite it with the older ModelStudio.tsx from the GitHub mirror; that file lacks controls visible in the user's current screenshot.
- Prepared a standalone offline HTML viewer containing the exact GLB, bundled Three.js 0.185.1, OrbitControls and GLTFLoader, studio lighting, whole-body/face/back views, and download of the unchanged GLB. No photo enlargement, geometry regeneration, decimation or AI call.
- Real headless Chromium test completed: modelLoaded=true, faceSelected=true, downloadEnabled=true, pageErrors=[]. Source/bundle syntax passed. This verifies the standalone viewer, not the hosted page.
- Saved deliverables with successful durable write receipts:
  - FORGE-modelka-podglad-3D.html, 55,078,078 bytes, libfile_e434f79462dc8191a29452691e3ffe85 (version 0).
  - FORGE-modelka-4K.glb, libfile_20ecc730588481919bfb5095dbd7fab3 (version 0).
  - FORGE-modelka-podglad.png, libfile_a7b1f4fe52a08191aeb9774825d430f0 (version 0); unchanged 840x1080 render from the ZIP.
- PR #8 remains draft and unmerged. Original reference likeness and commercial print readiness are still not accepted.

Next necessary work: recover the current Site checkout; add this asset to its existing viewer and explicit example selection, preventing auto-restore of an earlier job from replacing it; preserve the current site UI and audience; verify the resulting load and publish the requested preview. User authorization to add this preview to their studio is present in this turn.


Implementation tested: 123 Python tests, 70 focused Vitest tests, successful
production build. Real 4K-profile generated GLB: 39711312 bytes, SHA256
63d9924795454898e60f52fe8bce87c5906e60016f06211c19b0f2f88078b99b.
304329 pre-export vertices, 592136 triangles, 100 meshes, 14 images.
Actual GLB face/front/profile/full renders inspected; the first ear-cap
regression was corrected and generation repeated. Native 8K + 3x4K
PBR export/reimport passed exact color/normal bytes and ORM pixel checks.
Details: docs/reviews/generator-upgrade/README.md. Capability is
referenceQualityRevision=1 + materialQualityRevision=2. History now exposes
textureMaxSize; replay test caught and fixed that omission.
Rebuilt v20 installer with current source and rollback checks. It is still a
package, not an installed Oracle worker. No paid AI calls or Site deployment;
Site 38 remains live. Draft PR remains open because likeness is not accepted.
Reproducible large download/face-fit assets are generated during build, not
committed. Keep test fixtures and runtime source tracked. Standalone model
and installer deliverables are saved separately; see handoff below/next commit.
A reconstructed checkout had unrelated whitespace differences from PR;
restored those files from the PR after keeping scratch backups. No unrelated
commerce/game changes are part of this generator follow-up.

---

# Generator fidelity implementation in progress

Current authorized PR: #8, codex/reference-fidelity-4k-8k. Base before this work:
fb1733171d79fb6897296388bf695e5281f58b7d. Site 38 remains live.
Actual runtime changes: continuous updo nape/temple coverage, rigid eyeball
photo fitting, native procedural detail up to 4K, separate material memory
policy (8K+3x4K admitted under 8 GiB, rejected under 4 GiB), per-job isolated
4/8 GiB container and RAM preflight before AI, worker capability + UI gating,
no position quantization for 4K/8K master GLB.
Task: docs/CODEX_GENERATOR_UPGRADE.md. Validation and renders are pending.
No likeness acceptance, paid generation, Site deployment or Oracle install.
Continue until real export/renders and build pass, then rebuild update payloads.
Working checkout: /workspace/scratch/485945b1aaf2/pr-review (API reconstructed).
Blender: /tmp/blender-4.3.0-linux-x64/blender. Original reference fixtures:
/workspace/scratch/485945b1aaf2/model-check-final-reference.

---

# Meshy texture ZIP verified — PR #8 follow-up

Reupload received: 290,480,457 bytes; ZIP CRCs passed. SHA256:
10b7e8892cda8a8447ab749dab465967135a28a41eed9472a4595f2189536ab8.
External PNG maps: base color 8192x8192; normal/metallic/roughness 4096x4096.
Textured FBX: one UV mesh, one connected material, 1,539,459 vertices and
3,079,530 triangles. Embedded color/normal are JPEG; external PNGs were
bound without modifying geometry/UVs/material assignments for a native GLB test.
GLB 195,389,204 bytes; SHA ed3cd1eebe0f2db141d20b43c5d4ac6228862660253e3b5476f92b645ed61aa7.
Reimport preserved base-color/normal PNG bytes and triangle count; 1,596,454
vertices after attribute splitting. Three actual textured renders inspected.
Untextured/textured FBX indices differ. Spatial matching plus triangle/winding
comparison passed at 1e-6 scene units (max distance 8.775253377280023e-07).
Five existing inspector tests and four geometry regression tests passed.
The complete 112 Mi-pixel source set exceeds the current FORGE 80 Mi-pixel
export budget. Native Blender test success is NOT worker admission success.
Do not claim full PBR benchmark support until memory policy/worker are updated.
Source checkpoint on draft PR #8: 9f090751db489f23650df47f75d198ef5351ba95;
final reports/renders follow on the same branch. Fetch its head before resuming.
See docs/reviews/meshy-reference/TEXTURES.md and updated Polish Codex task.
No new model training, paid AI, geometry reconstruction, Site deploy or Oracle
install. Site38 remains live. The missing texture ZIP status below is historical.

---

# Meshy geometry benchmark for PR #8 — 2026-09-10

Inspected the supplied Meshy_AI_Emerald_Prism_Empress_0910195448_generate.fbx
(SHA256 8c517ff85e83284a06e16b3db705c17fa60372b1b7501ff061e433a71224c086).
Actual Blender import: 1,539,459 vertices, 3,079,530 triangles, one object,
no UVs/materials/images. Texture ZIP upload failed and has NOT been read.
The last FORGE GLB f1d5383bf1ab8cf112e59028d7e41294dba6cac1e374833f1d718548e6757cd8
reimports as 351,497 vertices (UV/attribute splits), 592,396 triangles, 100
objects, 14 images, maximum 2048x2048. The older 304,459 vertex figure is
pre-export, not the raw GLB reimport count.
Added scripts/inspect-reference-asset.py and five passing native Blender
regression cases. Saved six actual clay renders with source/render hashes;
front, three-quarter and back of both inputs inspected. FORGE upper-half
framing is approximate, not pixel registration. Meshy better retains visible
face, ear/hair flow, collar and folds. Current generator quality is NOT accepted.
Docs/reviews/meshy-reference contains the comparison; the Polish Codex task now
requires geometry acceptance, preserved master/separate LOD and verified PBR
maps after the missing ZIP arrives. Strict optional all-material texture gates
must not replace production checks for valid constant-color materials.
Benchmark source checkpoint on authorized draft PR #8:
e0d44bd4356412107d005cfef50aa82ab0735bf1. Six clay render files are versioned
with this review. Fetch the current remote head when resuming. This stage adds benchmark tooling,
not a newly trained model or Meshy-quality reconstruction. No source FBX asset
is embedded into the generator. Site38 and installed Oracle are unchanged.

---

# PR #8 prepared and checked — 2026-09-10

https://github.com/teslaeco/Froge-MPC-2-test/pull/8 is OPEN/DRAFT, targeting main,
branch codex/reference-fidelity-4k-8k. Remote implementation commit:
7f407cbf774e88623930450d6b7d6199c4b8ade6. GitHub mergeable=true, state=clean.
Full Codex command: docs/CODEX_REFERENCE_FIDELITY_4K_8K.md.
The PR retains #6/#7 work and imports the current v20/v25 worker plus photo
UI/API dependencies, not unrelated Site gallery/commerce source. Exact assembled
PR passed production build, 88 focused Vitest and 119 Python tests. Native
Blender textures and production couture export/reimport/four renders passed
technical checks. Latest four final renders inspected; face/hair/outfit likeness
is NOT accepted. See the final model SHA and limitations in
 docs/reviews/reference-fidelity-4k-8k/model-verification.json.
The PR provides a verified reference/texture foundation. Further geometry
reconstruction, visual acceptance and Oracle deployment remain separate work.
No additional paid AI request, weights training, merge, Site deployment or
Oracle install. Published Site38 remains the live version.

---

# Reference fidelity / 4K–8K verified source — 2026-09-10

Implemented browser/API/worker textureMaxSize (2048/4096/8192), bounded 2 MiB
per prepared JPEG / 6 MiB per job / 80 MP total, explicit capability gating,
quality metadata preserved on replay, aspect-preserving export without
upscaling, exact geometry/UV/pose/material assignment guard and measured
texture report. Re-encoded copies of the reviewed emerald composition are
matched using frame + face + fan + garment signatures. Altered composition
is rejected; this is not identity recognition. SHA binding remains mandatory.
Current attached image was checked: the matching source composition passed.

119 Python tests passed after package rebuild. Canonical Site production build
and 14 focused frontend tests passed. Native Blender 4.3.0 texture fixtures
exported/reimported 4096x512 and 8192x1024 without geometry changes. Actual
couture generation exported/reimported 304459 vertices, 592396 triangles,
100 objects, 14 images; four CPU renders inspected. Face/gaze, hair, collar
and glove remain approximate; lower-gown photo reflections are stretched.
Review evidence and reproduction: docs/reviews/reference-fidelity-4k-8k/.
No likeness acceptance. Actual photo/skin textures remain below 4K because
source pixels are below 4K. PR will remain draft for visual reconstruction.
GitHub PR staging is based on #7 (72f4689), importing current worker and only
required frontend/asset preparation dependencies. Exact assembled PR production build, 88 focused Vitest tests and 119 Python
tests passed. No unrelated gallery/commerce changes were imported. Draft PR: https://github.com/teslaeco/Froge-MPC-2-test/pull/8
Implementation commit: 7f407cbf774e88623930450d6b7d6199c4b8ade6.
GitHub confirmed an open draft with clean mergeability. Final review evidence
was refreshed after all PBR maps were preserved at the selected limit. High quality also retains normal/roughness maps
up to the selected edge; legacy exports keep the old category limits. No paid AI, Site deployment or Oracle
installation. Installed worker must expose referenceQualityRevision=1.

---

# Active reference fidelity / 4K–8K PR — 2026-09-10

Source base: Site Git 48ef03013bc5c67e93e3ff35a9925b5e4bea6683.
GitHub main bac2827 is v18; unmerged PR #7 is v19. Current v20/v25 runtime
is newer and must be preserved in the implementation PR. The attached HTML
is r6; r8 standalone edits exist but were not integrated into the generator.
Inspected actual before/after renders: facial likeness, hairline, glove and
outfit remain visibly different. Do not claim 1:1 or training of AI weights.
Confirmed source causes: 1600 px upload clamp, 2048/1024 px export clamps
that also distort nonsquare images, and exact-file-SHA-only couture guide.
Implement bounded 4K/8K source preservation with no fake upscaling, a
composition-checked guide for re-encoded copies, measured texture provenance,
and exact geometry preservation during texture export. Include Codex task
and reproducible verification. No paid model request or Oracle installation.
Published Site38 remains unchanged. PR is requested; deployment is not.

---

# Glove/armhole/portrait iteration delivered — 2026-09-10

Final runtime d78ecbe: five edit/review attempts, then four actual GLB reimport
renders at 48 samples/8 CPU threads. Parent inspected every final view.
Glove wrist crescent and accidental strip fixed; real fingerless shell with
16 metal facets, narrow upper-arm skin opening, .28 m fan, chain/pendant,
smaller lids, fuller brow fibres, varied lashes, bounded authored facial
depth and darker asymmetric hair crest. Blue collar/teal cloth mapping.

All 116 Python tests passed. Worker archive CRCs and 40 manifest entries plus
updater match source bytes. GLB: 304459 vertices, 592396 triangles, 100 objects,
14 images. Glove closed-shell, fan apertures, free-hand clearance and gown
containment checks pass. Local thumb signed depth 4.601 mm remains reported;
complete hand collision is not verified. Face, hair and textured garment
reflections still differ from original. No 1:1, print readiness or AI-training
claim. Original and previous deliverables preserved.

Three new standalone files saved successfully at version 0: couture-rekawiczka.glb,
froge-v20-rekawiczka.zip and podglad-rekawiczka.html. Hashes, receipts, five
attempts, final views, measured reference metadata and reproduction notes:
docs/reviews/v25-glove/. HTML images, toggle state, JS syntax and installer
paths checked. No browser run. No Site deployment, Oracle install or PR change.
Confirm final documentation push before ending the turn.

# Glove wrist correction visually checked — 2026-09-10

R3 still exposed a wrist crescent. R4 rotated glove rays with the bent wrist;
this closed the crescent but accidentally sampled a curled finger. R5 confines
those rays to wrist/proximal palm triangles. Parent reviewed its actual GLB
hand render: the crescent and stretched strip are gone. Fan fixture radius is
restored to .28 to satisfy the unchanged reference-relative-size gate.

Final four-view 48-sample render, package rebuild and 116-test suite pending.
New packaging script preserves previous deliveries and shows original/final
first. No source image changes, paid AI, installation or publication.

# Glove and reference R3 validation pending — 2026-09-10

R1 and R2 actual export/reimport renders reviewed and rejected for specific
remaining glove/cape/collar defects. R3 keeps 16 larger triangular facets,
short lateral glove edge, extends only dorsal coverage, and closes the exposed
wrist crescent with a matching dark cuff. Upper-arm opening is reduced by cape
placement. Blue collar mapping, darker teal garment vertex tint and reference-
only bounded cheek/nose/lip depth are retained. Hair crest now asymmetric;
brown pigment reduced after the overly reddish R1/R2 renders. This is authored
pigment correction, not an image-encoding fix.

New reference-depth isolation test passes. Actual closed glove shell guard
added without weakening existing contact/containment checks. R3 GLB and four
CPU renders next. Package and full tests must be rebuilt after source freeze.
No likeness acceptance, deployment or Oracle installation yet.

# Active glove, armhole and portrait correction — 2026-09-10

User rejects cbc6bf4 and requests the reference glove, smaller eyes, makeup,
hair, exposed upper-arm cutout, fan/hand grip and collar. Current unreviewed
pass replaces the broad wrist plate with a ray-fitted closed dark glove and
8 raised silver diamonds; adds bare upper arm below the shoulder cape,
shortens the black fan handle, adds pendant and enlarges the example fan
radius .280 to .305 m. Collar uses a corrected reference quadrilateral.
Astra asset patch narrows lids, thickens brow fibres and varies lash lengths;
reference-only authored brown hair palette. Initial encoding-bug diagnosis
was rejected: make_material stores display/sRGB in diffuse_color; existing
atlas encoding remains unchanged. No other portrait palette changed.

Initial actual GLB export/reimport and renders next: review-v25-glove-r1.
Source compiles, but geometry and appearance are not accepted yet. Preserve
v24 deliverables. Do not install/deploy, change QA thresholds or claim 1:1.

# Three reference cycles R3e verified — 2026-09-10

Three actual edit/render/reference-review cycles are complete. Final source:
review-v24-reference-r3e. Parent inspected original and all four final views;
gpt-6-astra confirmed the rejected R3d stepped neckline regression is gone.
Accepted for intermediate review only; likeness and 1:1 correspondence remain
unverified. Do not describe this as trained AI weights or completed realism.

Skin exposure .34, restrained pore/roughness maps, 11 narrow crown-swept rolls,
root clearance, ellipse-fitted collar, anatomical wrist fit, shorter knuckle
transition, forearm-aligned holding wrist, 3 mm thumb padding, continuous
front-cloth UVs and restored upper-hip proportions are in the final runtime.
Local signed thumb depth is 4.689 mm; gap contacts pass, but complete hand
collision is not verified. Hair, gaze, face shape and stretched photo reflections
remain visual limitations. The free-hand pose is inferred from unseen anatomy.

Actual GLB export/reimport: 300285 vertices, 584300 triangles, 95 objects and
14 packed images. Four CPU renders, 48 samples, 8 threads. Fan opening/frame,
body containment and free-hand clearance checks pass. Final 115 Python tests
passed in 12.275 s. Both worker ZIPs have valid CRCs and match all 40 manifest
files. A truncated fresh-install ZIP was caught; archives now use verified
atomic replacement. No validation threshold was relaxed.

Three standalone files are saved successfully at version 0: couture-trzy-proby.glb,
froge-v20-trzy-proby.zip, and trzy-proby-porownanie-z-oryginalem.html. Exact hashes,
save receipts and source commit 6777d6c are in docs/reviews/v24-reference-cycles/verification.json.
The HTML contains 10 verified embedded images and three selectable stages.
Prior files remain intact. Confirm the final Site Git push before handoff.
No Site publication, Oracle installation or PR change.

# Third-cycle grip gate corrections — 2026-09-10

R3 stopped before rendering: thumb surface gap4.636mm exceeded unchanged3.5mm contact gate after6mm padding. Experimental local pad projection (R3b/R3c) did not solve it and was removed; do not ship or claim that feature. R3d uses3mm thumb padding, the lower-curl anatomical wrist fit, knuckle blend.25 and forearm-aligned wrist. Four actual final views pending. The signed-local-depth metric remains reported and is not a complete collision check. R1/R2 render reviews are preserved. Source recipe for three-cycle comparison created; rebuild final package and tests after final runtime freeze. No deployment/installation.

# Third reference comparison cycle pending — 2026-09-10

R1 rendered and rejected for excessive pore normals and skin holes at hair roots. R2 corrected these, but actual hand detail exposed a wrist skin strip and4.576mm thumb-local penetration; altered lower-skirt UV scale stretched photographed belt highlights. R3 fixes wrist direction into sleeve, thick-thumb padding, knuckle swing blend .55→.25of finger length and restores observed waist/hip UV proportions while preserving full front mapping. Lower neck is contained under gown. Astra makes rolls18%slimmer/40%shallower and sweeps ends over crown. New anatomical wrist fit solves two translations from five finger contact lengths, within3.5cm; does not train AI. R3 final actual render/reimport pending. Prior artifacts preserved. No deployment/install.

# Active three reference comparison cycles — 2026-09-10

User rejects R6 and explicitly requests three edit/render/reference-review cycles. Current first pass: smoother ellipse-based tailored collar; vertex-corresponding shoulder photo UVs; remove jagged lower texture cutoff; restrained photo-surface reflections. Astra: exact-reference skin exposure .34 and packed pore/roughness maps; 11front rolls,204filaments and revised hairline. Not visually accepted. Hand curl fitting is next, with no relaxed QA thresholds. Preserve prior artifacts. No training of AI weights, no deployment or Oracle installation.

# Hands, head pose, complexion and groom R6 reviewed — 2026-09-10

Final actual GLB: review-v23-pose-skin-r6; runtime/installer source c886606.
Parent and gpt-6-astra inspected four final views; accepted as an improved
intermediate, not1:1. Free hand moved clear of cape/gown; cut wrist smoothly
follows forearm into sleeve. Holding wrist upright with revised finger bends,
five prop contacts and fitted palm glove. Smooth anchored neck preserves
measured eye-line roll and reduced authored chin pitch(-.18). Known-reference
skin exposure.45 and warm balance[1,.90,.80] shared by head/hands. Astra groom:
seven rounded front rolls,36shallower locks,156fitted fibres,roughness variation.

115Python tests passed in20.493s. New actual free-hand collision guard rejects
R4 with337crossing edges; R6 source+reimport:20198edges,zero crossings,
minimum skin-vertex clearance15.886mm from gown/cape. This is a scoped check,
not a complete hand/clothing collision solver. Five grip gaps0–.573mm;
local signed depths up to1.07mm. Fan130clear/60junction/10filled rays and
11774body containment samples pass. 290781vertices,565500triangles,95objects,
12packedimages. Four actual CPU48sample renders,8threads. Full package and
worker CRC plus byte-matched source manifest passed. HTML embeds8images.

Prior files preserved. Three new standalone deliverables are
couture-poza-dlonie-karnacja.glb, froge-v20-poza-dlonie.zip,
porownanie-pozy-dloni-karnacji.html; all3saves succeeded at version0; exact hashes and receipts are in
docs/reviews/v23-pose-skin/verification.json. Final source push must be
confirmed before handoff. No Site publication, Oracle install or PR7 update.

Remaining: curled holding fingertips, slightly splayed inferred free-hand
pose, regular sculpted hair/broad pale crown highlight, facial shape/gaze/
complexion not1:1, stretched/bright garment photo textures and preexisting
sawtooth lower texture boundary. Hidden geometry and photo illumination remain
inferred/baked. Do not describe as finished photorealistic reconstruction.

# R4 neck fixed; free hand rejected; R5 verification running — 2026-09-10

R4 parent/Astra review found the free hand inside the shoulder cape, thumb clipping gown, only two fingers visible. R5 moves it forward/outward and turns its dorsum toward the camera; relaxed unseen pose remains inferred. New actual edge-ray intersection and vertex-clearance checks on skin versus gown/cape run before and after GLB reimport. Pitch reduced from -.24 to -.18; measured eye-line roll retained. Smooth neck anchor and fitted tessellated glove retained. R5 four-view render running, not accepted yet; source package must be rebuilt before delivery. No deployment/install.

# R2 real render rejected at neck boundary; corrective R3 next — 2026-09-10

Upright wrist was repositioned to preserve anatomical finger lengths; R2 passes all5contact checks and115Python tests, actual GLB export/reimport. Visual R2 exposed rotated cut neck boundary and palm glove triangle chords sinking into hand. Pinning lower neck to neutral body placement with smooth skull transition and chin protection; tessellated glove is fitted to actual posed palm. Reference-only skin .45diffuse scale plus inferred linear warm balance[1,.90,.80]. Actual R3 four-view review next. Source skull fit and eyes unchanged; head pose inferred from eye-line roll with authored pitch/yaw. No deploy/install.

# Active hands, measured head roll, complexion and groom — 2026-09-10

User requests both hands, hair, skin and head angle closer to reference. Known-reference guide now measures eye-line roll (previous authored tilt had wrong sign); pitch/yaw remain inferred. Holding wrist is upright, finger curls/contacts revised, free hand relaxed toward thigh; fitted palm glove added. Known-reference skin exposure .65→.45 shared by atlas, preserving eye patch/other subjects. Astra rebuilt seven rounded front rolls and36shallow locks with variable roughness. Next: real GLB export/reimport and face/upper/hand renders in review-v23-pose-skin-r1. Not yet accepted. Prior photo-surfaces-r4 preserved; no deployment/install.

# Original-surface R4 delivered as intermediate — 2026-09-10

Accepted review source: /workspace/scratch/95d608cd4d09/review-v22-photo-surfaces-r4.
Runtime source b14fff1; packaged installer digest ddb5c54. Parent inspected
all3 actual GLB renders; gpt-6-astra inspected final face/upper body against
previous grip-r3 and original. 114 Python tests passed in14.640s. Both worker
archives match40 manifest files; CRC and full installer syntax/equality pass.
289869vertices,563696triangles,94objects,12packedimages. Build+3CPU48sample
renders82.02s,8threads. Existing320k vertex budget retained; inlay subdivisions
32→20 and4–6mm lift passed triangle interior clearance checks.

New: original unchanged1229x1536 photo bound to7 objects via guided UVs,
including lower fan leaves, visible upper dress, spatial shoulder lapels,
collar and physically pleated shoulder cape. Exact referenceSHA gates the
profile; this is NOT automatic reconstruction of arbitrary uploads. Existing
face478/112controls preserved. Photo lighting remains baked in colour; hidden
surfaces are inferred. Collar lower; handle13mm shorter;42 uneven swept locks
and156 fitted filaments plus roughness maps. 130openfan/60junction/10lowerpanel
rays,11774containedbody samples and5actual fingertip proximity checks pass.
No complete hand collision check, likeness or print-readiness claim.

Rejected candidates:R1vertex-colour-only QA incompatible with photo-textures;
R2skin-colour source patch/stretching, tall groom;R3groom width variable
shadowed body width and collapsed UVs. R4fixes shadowing and adds guard/test.
Remaining: bright stretched/blurred collar/shoulder/cape highlights, too-pale
shoulder, stylized cap-like groom and stiff hand. Face and complexion were
NOT improved this stage. Visible detail improved, but 1:1 and GTA6 quality
remain unmet. Do not describe this as finished photorealistic reconstruction.

Three files saved successfully at version0: couture-tekstury-oryginal.glb,
froge-v20-tekstury-oryginal.zip,porownanie-tekstur-i-fryzury.html. Exact sizes,
hashes/receipts are in docs/reviews/v22-photo-surfaces/verification.json.
Seven real/reference images embedded in standalone mobile-aware HTML.
Prior files preserved. Source final push must be confirmed before handoff.
No Site publication, PR7 update, new paid AI/GPU call or Oracle installation.

# R3 rejected: hair variable overwrote garment UV scale — 2026-09-10

Real R3 export/reimport passed structure but visual inspection found horizontal texture smearing. Root cause: new groom loop reused width, replacing body scale .94 with a roughly .005m strand width before garment UV binding. Renamed lock_width; new projection guard and regression test reject this mismatch. R4 is the next real export/reimport/render. Preserve R3 only as a failed candidate. Source original-image material/UV checks now pass;114 test target after packaging. No deployment/installation.

# Original-surface R2 reviewed; corrective R3 next — 2026-09-10

R1 was blocked by the vertex-colour-only QA assumption. New QA verifies actual original-image material and its exported UV set before permitting white multiplier colours. R2 exported/reimported and rendered. It reveals clothing detail but has an armpit-colour patch in the bodice, vertically stretched hip texture and an overly tall regular groom. Correcting sampled clean regions, limiting photo skirt mapping to the visible upper part, adding a physically pleated shoulder cape and refining groom. Inlay clearance now passes all 15 numerical couture tests at20 subdivisions with4mm offset, preserving the320k vertex cap. Packaging/tests still pending; R2 not accepted for delivery.

# Active original-surface and groom revision — 2026-09-10

User rejected minor incremental differences and requests substantial geometry/texture improvement. Astra changed asymmetric pompadour volumes, 42 locks and 156 fitted fibres, directional roughness. Parent adds exact-image-bound original-photo UV mapping to fan leaves, visible garment, folded shoulder lapels and collar; hidden continuations are inferred and photographed lighting remains. Reduced excessive inlay tessellation to free the existing vertex budget. Shorter handle, lower collar. Numerical tests and real GLB export/reimport/render are pending; do not claim accepted or 1:1. Previous accepted artifacts are grip-r3. No deployment or Oracle installation.

# Grip, collar and complexion R3 accepted for review — 2026-09-10

Final candidate: review-v21-grip-r3. Parent and gpt-6-astra inspected three
actual exported/reimported GLB renders: face, upper body and hand detail.
R1 was rejected for pale skin/excessive blue. R2 stopped at the new fingertip
proximity gate (index gap 3.746 mm). Distal joints are close to the skin, so
contact padding was reduced from 4 to 2 mm; R3 passes all five contacts.

Changes: completed-prop contact fitting, per-finger curls/root swings, turned
wrist/forearm, actual handle and faceted cuff; taller fitted sapphire collar
with front/diagonal silver edges; emerald/teal/navy fixture palette; slightly
raised chin. Original 478-point/112-control face deformation and gaze remain.
Skin colour uses sampled lower/mid-cheek ranks and explicitly inferred .65
linear diffuse exposure, scoped to couture. Atlas gain [0.7318,0.7770,0.8515].
This is not physical inverse rendering; photo illumination remains in colour.

Final GLB: 316,603 vertices, 612,208 triangles, 93 objects, 9 packed images.
Actual Blender 4.3 export/reimport passed; 110 Python tests in 26.384 s; both
worker archives match all 39 source files, CRC and installer syntax verified.
Grip gaps mm: [0.162,1.942,1.203,1.188,0.001]. Local signed penetration up to
0.861 mm; complete hand collision checking was NOT performed. Fan130/60/10,
gown11774, 420 brow fibres/side, 2 hands/10 nails/44 lashes per eye passed.
Final build and 3 CPU renders:81.09 s,8 threads,48 samples. No new paid call.

Accepted as an improved intermediate model, not 1:1. Astra notes fingers
remain somewhat stiff, collar too tall/open, skin still lighter/pinker than
the golden reference; hair and clothing remain simplified. Three standalone artifacts saved successfully at version0: couture-chwyt-kolnierz.glb,
froge-v20-chwyt-kolnierz.zip and porownanie-chwytu-kolnierza.html. Runtime
source is caf6adf. Final images/hashes/receipts are in docs/reviews/v21-grip/.
Confirm final source push before handoff. Previous files remain.
Site version38, Oracle and PR7 unchanged; no production publication.

# Grip R1 reviewed and colour corrected; R2 running — 2026-09-10

R1 actual render improved finger orientation and collar, but was rejected for
excessive blue and lighter skin (atlas gain [1.4165,1.9831,2.0]). Restored
emerald-balanced gem colour. Astra now selects lower/mid-cheek luminance
percentiles 20–45 and an explicitly inferred diffuse exposure .65; the atlas
gain cannot brighten. Parent applies the same exposure to sampled photo tint
and scopes it to couture, preserving other photo portraits. R2 snaps five
finger contacts to completed prop surfaces, adds a cuff and smooth collar
edging, and checks actual fingertip mesh distances on source/reimported GLB.
Full collision checking is not claimed. New hand-detail camera added.
R2 is rendering; source changes not yet accepted or packaged. Face warp and
measured gaze unchanged; the fixture chin tilt is slightly raised. Production
Site/Oracle/PR7 unchanged. Prior accepted files are junctions-r2.

# Active grip, collar and colour revision — 2026-09-10

Sebastian requested fan holding, collar, posture, garment palette and face
complexion changes. Parent added a prop-contact hand pose: wrist/forearm
orientation, separate finger bends and smooth anatomical-root swings towards
five contact targets, with a real handle below the fan. Collar is taller,
front-tapered, sapphire-tinted and has fitted silver side/diagonal edging.
Fixture has more teal/navy/cyan and a slightly raised chin. Astra verified
Blender JPEG pixels are sRGB and kept the correct conversion; shared skin
atlas now calibrates cheek midtones from the measured reference, while the
central photo-colour pass and face warp remain. Real render/fit validation
PENDING in review-v21-grip-r1. Previous accepted junctions-r2 untouched.
No deployment or Oracle installation. New source is not yet visually approved.

# Fan frame filling and measured eyebrow finishing verified — 2026-09-10

Accepted candidate: review-v21-junctions-r2; runtime source 062878e (pushed).
Both exported/reimported GLB views were inspected by parent and gpt-6-astra.
The crystal surface fills the space outside each polygonal turbine opening.
A new closed-sector generator avoids Boolean deletion and fits complete
housing extents at all supported counts. Eyebrow fibres now follow measured
photo contour pairs instead of the old shorter/higher authored arc: 420/side.
The grey double arc is reduced. Also: makeup after photo colour transfer,
softer asymmetric hairline, higher swept crown, 83 root wisps, shoulder
silver perimeter and convergent waist ribbons. Earlier assets are preserved.

Final GLB: 315,643 vertices; 610,312 triangles; 87 objects; 9 packed images.
Actual Blender 4.3 export/reimport passed: 130 empty-window rays, 60 filled
frame junctions, 10 retained lower panels, 11,774 garment containment samples,
420 aligned brow fibres per side, 2 hands, 10 nails, 44 upper lashes per eye.
478-point/112-control photo fit and gaze unchanged; zero inverted triangles.
110 Python tests passed in 20.990 s. Both worker archives match all 39 manifest
files byte-for-byte; ZIP CRC and full installer equality/syntax passed.
HTML has 6 embedded real/reference images and a mobile viewport. No browser QA.
CPU rendering: 8 threads/48 samples; final build+two views 52.55 seconds.

Standalone files: couture-ramki-brwi-r2.glb, froge-v20-ramki-brwi-r2.zip,
porownanie-ramki-brwi-r2.html. Final images, source revision, hashes and Astra
assessment: docs/reviews/v21-junctions/verification.json. All three standalone saves succeeded at version 0; exact file IDs are in
that verification report. Verify the final receipt/source push before handoff.
Site stays version 38. Oracle and GitHub PR7 unchanged; no new paid GPU/AI call.

Remaining, explicitly NOT 1:1: face proportions and baked photo lighting;
brow density/pigment and sharper green makeup; helmet-like hair sheen and
flow; spatial collar, shoulder geometry, folded dress and accurate hand grip.
Do not claim print/commercial readiness. Next refinement should use this r2,
not the earlier junctions-r1 whose brows still followed the old contour.

# Fan junction render passed; brow contour correction next — 2026-09-10

Source 38f2dcc pushed. Candidate junctions-r1 exported/reimported and both
views inspected: unwanted large gaps around frames are filled, while turbine
openings remain empty (130 clear/60 junction/10 lower panel probes passed).
315,643 vertices; 610,312 triangles; 87 objects; 9 packed images. Existing
478-point face fit unchanged, zero inverted triangles; gown containment passed.
A grey second brow arc remained. Astra traced it to photo colour versus the
shorter, higher authored fibre arc, and now aligns fibres AND pigment to the
measured upper/lower eyebrow contour before the existing warp. Export QA also
preserves brow counts/alignment. Junctions-r2 is the final integrated candidate
next. No new files delivered yet; old files and live services remain unchanged.

# Active fan junction and portrait finishing — 2026-09-10

Sebastian supplied four screenshots identifying missing crystal wedges around
fan housings and unfinished brows, makeup, hair and clothing. The fan now has
closed annular crystal sectors fitting every hexagonal aperture, without
Boolean subtraction. Rotor size is bounded by actual sector clearance. New
numerical tests cover full sector-minus-hole area, winding and manifoldness
at all supported rotor counts and spread limits (15 couture tests passed).
Export QA now also probes six filled junctions per frame, as well as empty
windows and retained lower panels. Astra updated portrait.py: 420 lifted
fibres per brow, independent matte pigment, restrained finish after photo
colour transfer. Parent softened the hairline, raised the asymmetric crown,
added root wisps, shoulder edging and converging waist ribbons.

Actual integrated GLB/export/reimport/render is NEXT, using the unchanged
original photo and saved 478 measurements in review-v21-junctions-r1. These
source changes are not yet visually approved or packaged. Prior delivered
models remain valid and untouched. Site version 38, Oracle and PR7 unchanged.
Do not claim 1:1, natural reconstructed hair, or printable readiness.

# Integrated reference details delivered for review — 2026-09-10

Accepted real candidate: review-v21-details-r3. Runtime source: 99c1a6e.
Astra (gpt-6-astra) implemented eyebrow fibres and measured gaze, then reviewed
r1, r2 and final r3 with the parent. Both final GLB views were inspected: no
blocking regression, but this remains an intermediate stylized model, NOT 1:1.
R1 was rejected for a nearly deleted fan. R2 restored filling. R3 reduces frame
bulk and protruding tips and adds a continuous dark polygonal outer contour.

New functions: gaze from calibrated 2D iris positions (reject unreliable iris
Z depth); 360 closed brow fibres per eye; closed crystal fan leaves with an
open turbine strip, dark polygonal frames and hub braces; dual export checks
for empty windows AND retained opaque panels; convergent diagonal torso seams;
portable 2048px hair strand maps and 1024px crystal microfacet maps. Texture
maps are procedural, while face colour/measurements use the original photo.
Local rendering: CPU, 8 threads, 48 samples; no exposed GPU or paid cloud call.

Final GLB: 311,131 vertices, 601,860 triangles, 83 objects, 9 packed images.
Real Blender 4.3 export/reimport passed, including 10 windows / 130 clear rays,
10 retained filling samples, 11,774 garment containment samples, 2 hands,
10 nails and 44 upper lashes per eye. Face fit: zero inverted triangles.
109 Python tests passed in 17.173 s before the final cosmetic frame/outline
adjustment; that final adjustment passed actual export/reimport/render and
all worker-file archive equality checks. ZIP CRC and installer syntax/equality
passed. No frontend source changes, browser-session or live Oracle test.

Frozen files: couture-detale-astra.glb, froge-v20-detale-astra.zip,
porownanie-detali-astra.html. Final views/hashes/Astra verdict are in
docs/reviews/v21-details/. All three standalone saves succeeded at version 0.
Source and reviewed render/report push through abe86ec succeeded. Receipt
checkpoint is the final commit; confirm that last push before handoff.
Prior deliverables preserved. Site remains version 38; Oracle and GitHub PR7
were not updated. Main remaining problems: face identity/proportions, thin
brows relative to reference, helmet-like hairline/crown, oversimplified
couture surfaces and splayed hand grip. Do not label this commercial or 1:1.

# Integrated detail review correction — 2026-09-10

Source 35b9f4f was pushed. Astra and parent inspected candidate details-r1 and
REJECTED it: Boolean windows removed almost all fan filling, brows were pale,
hair highlights too bright and the crystal texture looked like a printed grid.
Do not distribute r1. Two earlier startup issues were fixed: shared turbines
must reuse a UV map; orphan meshes must be removed before material counting.

Correction builds closed crystal leaves below an open window strip plus solid
shards between the dark frames, avoiding Boolean subtraction. The export gate
now requires both empty window rays AND retained opaque fan panels. Brows use
darker, thicker fibres at unchanged count. Hair specular is reduced and small
crystal colour variations are subtler. Candidate details-r2 will now render.
Current tests: full 109 reached three failures in an outdated bpy mesh mock;
that mock is corrected and final packaging/tests are pending. Source save now.
No production deployment, Oracle install or prior deliverable overwrite.

# Active integrated reference details — 2026-09-10

Sebastian requested more work on hair, brows, gaze, true open turbine housings,
and original diagonal couture/textures, explicitly using Astra. An Astra agent
implemented brows made of individual closed hairs and gaze from 2D iris/corner
measurements (not unreliable iris depth). Parent adds actual Boolean fan holes,
black polygonal frames with hub braces, converging front dress panels, packed
microfacet textures, finer hair normal/albedo and less bulky locks. Rendering
now supports 8 CPU threads / 48 samples locally; no GPU is exposed here.

No 1:1 claim: unseen geometry and surface detail remain estimated. Integrated
GLB/render and package tests are pending. Prior files and live Site/Oracle are
preserved. Save this source before generation; current final delivered source
was 1173972. Do not use unfinished candidate as a validated deliverable.

# Fan refinement reviewed — 2026-09-10

Runtime source 4f87a5f is pushed. Actual candidate review-v21-fan-r1 uses the
same original photo and 478 measurements as accepted face-fitting r4. Both
reimported GLB views were inspected: broader crystal facets, less silver wire,
slender outer rim and ten smaller six-blade rotors. Fan/face are still stylized;
face geometry was not changed. Splayed grip and the original likeness remain
unresolved. Do not present this fan stage as a new face-likeness improvement.

GLB: 301,869 vertices, 584,536 triangles, 83 objects, five packed images. Ten
rotors, two hands, ten nails and paired 44 lashes survived reimport. Garment
containment passed on 11,774 samples. Measured face: zero inverted triangles.
All 107 distinct Python tests passed after archive recovery: initial full suite
had 103 successes and four ZIP-related errors; the affected installer/photo
suites reran with 11 successes. The canonical local update ZIP was truncated;
an existing alias was checked against every worker source file and restored
atomically, then CRC and affected tests passed. No frontend source changed.

Frozen deliverables: couture-wachlarz-r2.glb, froge-v20-wachlarz-r2.zip,
porownanie-wachlarza-r2.html. ZIP CRC, embedded installer equality and syntax
passed. Renders and hashes: docs/reviews/v21-fan/. All three standalone artifact saves succeeded at version 0.
Runtime and reviewed-render source pushes through ac3d2ba succeeded; final
receipt/checkpoint commit is the last push gate. Existing distributed versions are preserved.
Site publication, Oracle install and GitHub PR7 remain unchanged.

# Active fan refinement — 2026-09-10

The user requested further likeness work and specifically a better fan. This
stage replaces dense silver triangle outlines with broad folded kite facets,
slender radial ribs and a scalloped outer rim. Ten smaller six-blade turbines
are centred on their own leaves in the reference fixture. Shared gemstone
reflections are reduced. Existing measured face fitting is retained unchanged;
this fan edit does not establish further facial likeness.

Candidate review-v21-fan-r1 will use the accepted r4 original photo and the same
478-point measurements. Actual GLB export/reimport and visual review are pending.
Previous delivered GLB/ZIP/review files are preserved. No production publication,
Oracle install or GitHub PR change. Save this source before the longer render.

# Photo face fitting delivered — 2026-09-10

Runtime source 4eb4639, complete-install packaging source a29fee8. Accepted
actual candidate: review-v21-photo-fit-r4. All three reimported GLB views were
inspected. 478 points measured on the real reference drive 112 fitted controls
and photo colour on 30,602 face vertices. Geometry moved up to 11.38 mm with
zero inverted triangles. Eyes, brows, lashes and bound makeup move coherently.

The browser upload has a bundled local detector and sends measurements bound
to the JPEG SHA256 through private storage/retries. Oracle advertises the
capability; the Site gates old workers before submitting measured-photo jobs.
New files are included in both fresh-install and update archives via one
authoritative worker file manifest. No paid AI call was made.

107 Python tests passed in 17.039 s after final packaging; 45 focused photo/API/UI
tests passed; final production build passed. GLB: 310,329 vertices, 598,736
triangles, 83 objects, 5 packed maps. Reimport preserves 10 turbines, 2 eyes,
2 hands, 10 nails, 44 lashes per eye, COLOR_0 and the exact source-photo hash
on the fitted head. Garment check: 11,774 samples, passed. ZIP CRC and embedded
installer equality passed. Mock FROGE_UPDATE_OK is not a real Oracle install.

Saved standalone files, all version 0, in scratch deliverables/:
- couture-twarz-ze-zdjecia.glb — libfile_99d27dcae5308191b763385dfa22c376
- froge-v20-twarz-ze-zdjecia.zip — libfile_76432b2d67248191a9af04df634cff34
- porownanie-twarzy-ze-zdjecia.html — libfile_a63003d35fc88191921f7f85e7e25f55
Renders, measurements, checksums and receipts: docs/reviews/v21-photo-face/.

Current limit is one feminine subject; no cross-person fitting. Hidden depth
and far-side colour are estimated/symmetrized. Photo illumination remains in
colour, and likeness, natural hair, garment reconstruction, rig and commercial
print readiness remain unverified. Browser-session and live Oracle/Astra tests
were not performed. Production Site, Oracle and GitHub PR7 were unchanged.
Final source/render/document push is the handoff gate. Earlier artifacts were
preserved; r2/r3 photo-colour trials were rejected and not distributed.

# Photo fitting final visual review — 2026-09-10

Source checkpoint 8b9095b was pushed successfully. The actual first photo-fit
GLB was exported/reimported and inspected. Measured residual moves up to
11.38 mm of skin with zero inverted triangles; eyes/lashes and makeup follow.

Colour trial r2 was rejected for background contamination at the temple.
Trial r3 added piecewise interpolation inside measured facial triangles but
still exposed unreliable far-side pixels. Final candidate r4 mirrors colour
from the better observed cheek in turned-head photos and feathers the face
outline; it is rendering now. Inspect its own views before distribution.

106 Python tests and 45 focused upload/API/UI tests passed before the last
colour-boundary adjustment. Frontend production build passed. Tests explicitly
cover private measured-photo retries and capability gating before submission.
No browser session or live Oracle/Astra call was exercised. Source supports one
feminine face; different subject labels/groups are not mixed.

Final model/ZIP/comparison, final source push and artifact saves remain pending.
No Site publication, Oracle installation or GitHub PR changes.

# Active photo landmark fitting — 2026-09-10

User authorized replacing seven-parameter facial approximation with measured
photo geometry. MediaPipe 0.10.21 detected 478 points on the actual emerald
reference and a newly rendered neutral feminine Blender head. Source adds a
112-control regularized, pose-normalized deformation to the existing closed
head, eyes, brows, lashes and their bound makeup. Hidden depth remains estimated.

Browser model/runtime are bundled locally; measurements follow the exact JPEG
through storage/retry to Blender. Hash, dimensional and coordinate validation
prevent stale measurements. One feminine character is currently supported;
groups/ambiguous labels explicitly skip the fit. No new paid provider.

Candidate review-v21-photo-fit-r1 is generating; it is NOT visually accepted yet.
Remaining: inspect actual GLB renders, resolve geometry issues, add regression
checks, finish build/package and save deliverables. Runtime starts neutral for
measured fitting, so seven authored face controls do not double-deform it.
No production publication, Oracle install or GitHub PR change.

# Reference geometry correction delivered — 2026-09-10

Final runtime revision `d52905d`, already pushed to canonical Site Git.
Accepted technical candidate: `review-v20-reference-r4`; all four final GLB
reimported views were inspected (full front, face front, face 3/4, upper 3/4).
The last upper view frames the full fan and shows the holding fingers.

Completed: separate upper/lower lip volumes and vertex-bound lipstick;
reference-authored nose, cheek and jaw proportions/head pose; outer brow arch;
smoother asymmetric front hair roll; pointed earrings, hair jewels and waist
clasp; denser faceted fan with portable corner colours; 10 visible turbines
with six curved blades, hexagonal housings and fitted mounts; smaller fan and
raised/front-shifted holding hand. These are approximations, not recovered
original face geometry. Face, hair, garment panels and grip remain stylized.

99 tests passed in 18.740s after the final installer rebuild. Exact r4 GLB has
310,305 vertices, 598,688 triangles, 83 objects, 5 packed images. Reimport keeps
1 head, 2 eyes, 2 hands, 10 nails, 10 turbines, 3 hair ornaments, 2 earrings,
paired 44 upper lashes and fan COLOR_0. Gown containment: 11,774 samples, worst
ratio 0.98224, passed. The unchanged shared portrait code also passed actual
three-person export/reimport (3 heads, 6 hands, 30 nails); no group render claim.
ZIP CRC, installer syntax/byte equality, Cloud Shell filenames and six embedded
images checked. The reference is JPEG bytes despite its .png filename; the
comparison now embeds it as image/jpeg without altering the original image.

Saved standalone artifacts in `/workspace/scratch/95d608cd4d09/deliverables/`:
- `couture-v20-referencja.glb`: `libfile_8c99f968deb881918344045ba432e082`, v0;
- `froge-v20-referencja.zip`: `libfile_1fef6dea71c881919145df7cc69db64f`, v0;
- `przeglad-referencja-v20.html`: `libfile_60e7eeaccef8819193400eff0d85b72f`;
  corrected MIME replacement confirmed at v1.
Checksums and four review PNGs: `docs/reviews/v20-reference/verification.json`.

Final documentation/render push remains the handoff gate. Production Site,
Oracle and GitHub PR7 have not been updated. No paid AI, image generation,
new scheduled task or permission/audience change occurred. The improvement
is not identity likeness, exact reconstruction, or print/commercial readiness.

# Reference geometry final candidate r4 — 2026-09-10

The actual r3 GLB and all four views were inspected. Lip volume, lipstick
registration, brows, nose/cheek/jaw controls, triangular jewels, fan facet
geometry, ten six-blade turbines and their surface-fitted mounts are present.
A final visible defect remained: fingers were behind the fan and the upper
review camera clipped its left tip. Source now moves the holding wrist forward,
pans/widens the upper-body camera and replaces the remaining oval waist clasp
with a pointed cut stone. Scratch `review-v20-reference-r4` is the final
candidate being generated; inspect its own four views before distribution.

99 Python tests passed in 19.919s before this last wrist/clasp change. Final
package rebuild and the same suite are rerunning in `reference-tests-r4.log`.
Three-character fashion regression exported and reimported with 3 heads,
6 eyes, 6 hands, 30 nails and three paired 44-lash sets (no group visual claim).

The example is still a stylized approximation: face and hair do not preserve
the reference identity/photorealism; dress panels and grip remain simplified.
No Site publication, Oracle install, GitHub PR edit or paid model request.
Previous deliverables remain unchanged.

# Reference correction second visual iteration — 2026-09-10

First actual r1 GLB exported/reimported and its three renders were inspected.
Lips, cut jewels and denser fan facets are visibly changed, but the initial
crystal palette was too cyan. The source restores deep emerald, softens the
conical crown into a wider frontal hair roll and moves the brow arch toward
the outer eye. Both brow fibres and their underlay share one curve function.
Fan radius is now .28 m against a 1.88 m character, and forearm/grip are raised
coherently. Ten turbines use six curved blades and hexagonal housings.

All 98 tests passed after the first package rebuild. The current final source
adds a brow regression plus surface-fitted turbine mounts; rebuild the ZIP
and run tests again. Scratch r2 renders were started before the mount fix, so
final deliverables must use a newly generated r3 GLB and its own renders.
Do not distribute r1/r2 as the final installed-source example.

Source-only save; no Site deploy, Oracle install, PR edit or paid AI.

# Active reference geometry correction — 2026-09-10

Sebastian rejected hair-r3 as insufficiently faithful and explicitly asked
to preserve the reference face, hair, fan and accessory shapes. New source
corrects upper/lower lip deformation and keeps lipstick attached to the
pre-sculpt vertices. The authored reference fixture uses fuller lips, a
narrower nose/jaw, stronger cheek contour and the visible chin-up head pose.

Fan geometry now uses denser angular ridges and corner facet colours, ten
visible turbines instead of fourteen, curved six-blade rotors and hexagonal
housings. Triangular cut jewels replace rounded earrings/hair decorations.
The updo silhouette has an asymmetric lifted front roll and a softer hairline.

This source is a candidate; real Blender generation and visual inspection
are pending in scratch `review-v20-reference-r1`. The first run stopped at
scene validation because one observed-feature label exceeded the text limit;
the label was shortened without relaxing the validation rule. No accepted
model or installer from this stage exists yet. Do not distribute prior r3
files as if they contain these geometry changes.

No Site publication, Oracle installation, paid AI or GitHub PR update.

# Hair r3 final delivery — 2026-09-10

Runtime revision: `8302849`. Accepted reimported GLB: scratch
`review-v20-hair-r3b`, archived as `couture-v20-wlosy-r3.glb`.
304,565 vertices, 588,684 triangles, 85 objects, 5 packed images; within the
single-character export budget. All 95 Python tests passed after installer
rebuild. Final ZIP CRC, installer syntax/byte equality, filename-correct
Cloud Shell instructions and four embedded review PNGs passed.

Source, three inspected PNGs, verification and self-contained comparison
`public/przeglad-wlosy-v20-r3.html` are saved in canonical Site Git. Standalone
GLB and complete Oracle installer have confirmed durable saves (version 0):
- `/workspace/scratch/95d608cd4d09/deliverables/couture-v20-wlosy-r3.glb`,
  `libfile_a7ae52219cd48191b0b0aaa49d80e233`, SHA256
  `aba1ff3d3941544d72d2f94e93490b0be1e75ddf86c19e7b1d1f33cb14ce8a0a`;
- `/workspace/scratch/95d608cd4d09/deliverables/froge-v20-wlosy-r3.zip`,
  `libfile_2171c3a7df0c8191813a7dffd2a4c4f9`, SHA256
  `99df524174cfb723dcd5b241265bb9b8baf7e7f163d6836935f4223330599781`.

Final source push is the handoff gate; confirm it succeeds before claiming all
source saved. No production deployment: live Site remains version 38 and no
Oracle install, paid Astra call or GitHub PR edit occurred.
Next artistic limitation is generic facial anatomy and simplified crystal
accessories; hair remains stylized despite improved flowing relief. The rear
cape remains a broad procedural drape. No reference likeness or commercial
print readiness is established. Do not present code tests as visual approval.

# Swept updo r3 accepted after actual render review — 2026-09-10

Final candidate is scratch `review-v20-hair-r3b`. Source replaces the cap's
thin wire paths with 38 closed oval locks following the scalp, 15 overlapping
bun rolls, 112 fine filament paths and 53 tapered hairline wisps. Crown is
lower, dark-brown material values are coherent and strand UV flow follows the
real sweep. The first r3a trial was rejected for bright separated leaf-like
locks and a crossing herringbone texture; do not deliver that trial.

Actual Blender 4.3 export/reimport succeeded, and face-front, face-three-quarter
and full-back PNGs were inspected. The final look is still a smooth stylized
procedural updo, not realistic strand simulation or verified reference likeness.
Face, gown, collar, hands and fan were not reshaped in this stage.

All 95 Python tests passed in 17.451s after rebuilding the complete installer.
The earlier test run correctly caught the old embedded installer payload; it
was rebuilt, not bypassed. Gown clearance, 10 nails, 14 rotors and paired 44
upper lashes remain intact after reimport. No new paid AI or Oracle request.
Final render/model and additive update-package archiving are being completed.
No Site deployment, Oracle installation, GitHub PR or audience change occurred.
Previous public models and frozen packages are unchanged.

# Active swept updo reconstruction — 2026-09-10

Sebastian requested further refinement against the attached emerald couture
reference. This source candidate lowers the rigid crown, adds 26 closed oval
scalp locks, 15 diagonal bun folds, 112 fine filament paths and tapered hairline
wisps. Two existing hair material slots retain portable strand normal maps.
Other portrait, garment, collar, fan and hand geometry is unchanged.

Real Blender 4.3 generation/export/reimport and three close-up views are running
in scratch `review-v20-hair-r3a`. This candidate is NOT yet visually accepted.
Inspect its output and correct visible artifacts before delivering a GLB or ZIP.
Source compiles; full tests and package rebuild remain pending. The previous
verified model `couture-v20-dopracowana.glb` remains available and unchanged.
No production Site publication, Oracle installation or paid AI call occurred.

# Portrait and couture refinement completed — 2026-09-10

Final runtime source: `1ac6311`, pushed to canonical Site Git. The final accepted
technical candidate is scratch `review-v20-polish-r5`, copied additively to
`public/models/couture-v20-dopracowana.glb`. Do not distribute r1–r4 trials.

Completed changes: round tapered lashes (44 per eye), fuller matte brows,
higher surface density for bounded emerald eye makeup and terracotta lips,
subtler satin coat/specular, 180 surface-following silver couture seam paths,
front-facet fan outlines, and a thin collar fitted to the transformed neck.
The first collar fitting was visually rejected for a chin-level ring; the final
version has a wider front opening and an anterior rim below the chin.

Final GLB was exported/reimported in Blender 4.3.0. All four current images
(full front, face front, profile, face three-quarter) were inspected. They show
this exact final model, including the corrected collar. 277,188 vertices,
534,338 triangles, 84 objects, five packed images. Ten nails and fourteen rotors
preserved; garment check remains 11,774 samples at worst ratio 0.98224.
The three-character fashion regression also exported/reimported: three heads,
six eyes, six hands, thirty nails, all three paired lash sets. That group was
checked structurally only; no group visual claim.

Final package rebuild and all 95 Python tests passed (17.114 s). ZIP CRC,
installer byte equality, installer syntax, five embedded PNGs and review-page
JavaScript syntax passed. No frontend code changed, so no frontend build or
browser QA was claimed. No production Site or Oracle installation was performed;
no paid AI, background scheduling, GitHub PR edit, or access change occurred.
Mock installer messages in test output must not be reported as a real install.

Saved deliverables:
- `public/przeglad-v20.html` — embedded before/after comparison and current views;
- `public/models/couture-v20-dopracowana.glb` — 18,666,588 bytes;
- `froge-v20-dopracowana.zip` — 15,349,381 bytes, full installer; saved at `/MCP2/froge-v20-dopracowana.zip` as `libfile_a53866371f708191b9fa675d97e37375`, version 0; current local delivery copy is `/workspace/scratch/95d608cd4d09/deliverables/froge-v20-dopracowana.zip`;
- `docs/reviews/v20-polish/` — four current PNGs and detailed verification/SHA256s.

The frozen ZIP contains a filename-correct CZYTAJ.txt for Cloud Shell. The
installer still runs `froge-v20.py` internally and preserves prior pairing,
keys, models and rollback logic. The live Site remains version 38. Source push `1ac6311`, review push `3d9a2dd` and final GLB push `a7bdb4c` succeeded. The model push required a retry after HTTP 500 and completed after several minutes; no force push or history rewrite occurred. Runtime, renders, comparison and GLB are in canonical Site Git. The installer
is a standalone Library deliverable; GitHub PR7 was not synchronized.

Remaining quality limits: generic parametric anatomy and smooth procedural hair
still do not match the reference's photorealism. Skin, hair strands, garment
facet language and the fan grip need further artistic work. No identity likeness,
commercial readiness, print preparation, rig, or live Astra/MCP call is verified.
A working export or passing test suite is not evidence for those claims.

# Active refinement after morning v20 handoff — 2026-09-10

Sebastian requested further refinement now. The canonical checkout is
`/workspace/scratch/95d608cd4d09/froge-mpc-2-studio-r3`, resumed at `dcc5f23`.
Sites confirms live version 38. The reference `docs/references/emerald-couture.png`
and actual hair-r2 renders were inspected. Blender 4.3 works from the scratch
installation; the retained `/opt` binary exits with SIGBUS and was not used.

Source checkpoint `753a62b` was pushed successfully. Subsequent refinement adds
denser cosmetic surface sampling, serrated/tapered brow outlines, surface-fitted
eyeliner wings, emerald eyelid shadow and terracotta lips. Seams follow the same
curved coordinates as gemstone panels; thin metal traces actual fan facets.
Both eye lash counts now survive an explicit GLB export/reimport check.

All 95 Python tests passed in 18.221 seconds; the new seam regression samples
segment interiors, not just endpoints. The actual three-character fashion group
also exported/reimported successfully with the new portrait runtime. The r2
front and three-quarter face renders were inspected. The r3 full-front render
showed the added gown and fan details; a pre-existing collar/neck intersection
was noticed in the three-quarter close-up and is being corrected.

Current final-candidate r4 fits the collar to the transformed anatomical neck
with horizontal clearance and retains a real thin shell. A fresh GLB and five
reimported views are being generated in scratch `review-v20-polish-r4`. Finish
visual inspection and regenerate the package after this collar edit before
distributing. Earlier trials remain scratch only. No Site publication, Oracle
installation, PR modification or paid AI call has been made. FROGE_UPDATE_OK in
the test log is mocked installer output, not a real Oracle installation.

# Morning v20 handoff prepared — 2026-09-10

The bounded overnight sequence is complete. A Polish morning review with exact
commits, inspected Blender renders, cumulative GLB, frozen package, test results
and honest remaining limitations is saved in `docs/MORNING_HANDOFF_V20.md`.
This documentation-only handoff does not publish Site 38, modify GitHub draft
PR7, install Oracle or run a paid Astra request.

# Surface-fitted swept hair locks r2 rendered and tested — 2026-09-10

Workspace maintenance removed the earlier Sites checkout while it was being
restored. Two complete clone attempts then received transient HTTP 500 packfile
errors; a depth-one clone of the same canonical Site Git succeeded at clean
`6bc5f6f`. Sites confirmed live version 38 and no overlapping Blender/test
process was present. This bounded stage changes only the swept-updo surface.

The accepted generator projects eleven real tapered lock paths onto the fitted
scalp, flips any inward BVH normal against the head centre and half-embeds smooth
closed tubes into the hair shell. Their root/middle/tip radii are bounded by a
pure data-only helper and regression test. Hair base roughness was increased and
specular reduced; the locks use the same dark brown with high roughness, so they
read as shadowed swept grooves rather than chrome wires.

Several trials were honestly rejected: the first taper produced a complex number
at the floating-point endpoint and stopped before export; flush ribbons were
invisible; outward ribbons made bright planar shards; lighter tubes resembled
wires. None of those renders or GLBs is copied into public review artifacts.

Production Blender 4.3.0 exported and reimported the accepted GLB before actual
front and three-quarter Cycles renders. Both views were inspected. The former
unbroken cap now has visible diagonal lock direction without floating plates.
The result remains a smooth parametric updo and is not natural strand simulation,
reference likeness, commercial quality or print readiness.

New additive model: `public/models/couture-fan-v20-hair-r2.glb`, 13,097,248
bytes, SHA256 `31f79f93ea96fa49e75f6a9561f81c924481ee1d1019e80c30143a30905d9051`.
It has 179,232 vertices, 339,374 triangles, 81 objects and 5 packed images.
Reimport found one head, two eyes, two hands, ten nails, eleven joined swept
locks and fourteen fan rotors. Gown containment still passes 11,774 samples at
worst envelope ratio 0.98224.

Package was rebuilt before the complete suite. All 94 Python tests passed in
17.073 seconds. ZIP CRC, frozen/current byte equality and `git diff --check`
passed. Frozen package: `public/downloads/froge-v20-hair-r2.zip`, 15,345,993
bytes, SHA256 `e67ac7102590a9bc424c3d955207a60f3f1a08b5330f2ece4ed2430e1988fe11`.
No frontend source changed, so no redundant frontend build was run.

Site 38, GitHub draft PR7 and Oracle remain unchanged. No publication, SSH,
paid Astra request or installation occurred. Photos/history/keys/pairing,
cancellation, 600s AI planning, 900s Blender execution, JSON data-only and
limits are unchanged. Next bounded stage: couture seam density or final morning
handoff; preserve every earlier additive GLB.

Durable canonical Site Git saves confirmed: accepted runtime source/tests
`03a60be`, two inspected Blender renders and review record `a2a7168`, additive
GLB `6cf526a`, frozen review package `53acab2`. All pushes to `main` succeeded.

# Thin shoulder couture plates r1 rendered and tested — 2026-09-10

The same canonical Site Git project was restored at clean `6454efb` after local
workspace maintenance. Sites confirmed version 38 and no overlapping Blender or
test process was present. This bounded stage changes only the shoulder jewellery.

The prior single crystal plate extended 18.5 cm horizontally and 11.4 cm high,
reading as a thick triangular spike. A pure data-only geometry function now makes
each closed plate 14 cm wide and 7 cm high, anchored closer to the anatomical
shoulder. Its four broad front/back faces remain emerald crystal; only boundary
walls use the silver material, so metal no longer fills the decoration.

A new geometry test verifies both plates are manifold, consistently wound,
positive-volume shells with the required dimensions and material-slot split.
The initial exact 0.07 m assertion observed normal floating-point representation
at 0.07000000000000006; the tolerance was corrected by one micrometre without
changing the geometry. All 23 focused tests then passed.

Production Blender 4.3.0 exported and reimported the accepted GLB, then rendered
actual front and three-quarter Cycles views. The right plate no longer dominates
the shoulder and remains connected in both views. New additive model:
`public/models/couture-fan-v20-shoulder-r1.glb`, 12,993,056 bytes, SHA256
`90f9dcc1927e534ebe897c4369a03bf520828a4d2c96ff4eddccdf5321720689`.
It has 176,904 vertices, 334,762 triangles, 80 objects and 5 packed images.
Reimport checks found two shoulder inlays, one head, two eyes, two hands, ten
nails and fourteen rotors; gown containment passed 11,774 samples at 0.98224.

Package was rebuilt, then all 93 Python tests passed in 16.642 seconds. Frozen
and current ZIPs are byte-identical; ZIP CRC and `git diff --check` passed.
Frozen package: `public/downloads/froge-v20-shoulder-r1.zip`, 15,344,989 bytes,
SHA256 `6a5cf211e56055748986a371fc8980893937c9c8875f6aef9e3d38d1365afb0f`.
No frontend source changed, so no redundant frontend build was run.

Visual acceptance is limited to shoulder scale/thickness/edging. This does not
establish likeness, commercial quality or print readiness. Site 38, GitHub draft
PR7 and Oracle remain unchanged; no publish, SSH, paid Astra call or install.
Photos/history/keys/pairing, cancellation, 600s AI, 900s Blender, JSON data-only
and limits remain unchanged. Next stage: natural hair detail or couture seams.

Durable canonical Site Git saves confirmed: source/test/two actual renders
`9a46ca9`, additive GLB `55d58a2`, frozen installer `2b26585`. Push succeeded.

# Face proportion controls r1 rendered and tested — 2026-09-10

Workspace maintenance again removed the local checkout; the same canonical Site
Git project was restored at clean `10deea9`. Sites confirmed version 38 before
editing and no overlapping Blender/test process was present. This bounded stage
changes only the existing reference-guided nose, lips, cheeks, jaw and chin
controls; the orbit region remains protected.

The former coefficients made valid non-neutral plans almost indistinguishable
from the generic head: the fixture's nose projection moved about 0.7 mm and lip
fullness about 0.5 mm. The bounded deformation range is now visibly useful at
figure scale while remaining inside the existing 25 mm topology envelope. The
reference fixture uses a narrower, more projected nose, fuller lips, narrower
jaw and stronger cheek definition, all through the data-only scene controls.

The actual bundled female head topology test passed all three checks: neutral
byte-equivalent vertices, preserved orbits, finite coordinates, displacement
below 25 mm and no inverted existing faces at both control extremes. Production
Blender 4.3.0 exported and reimported the accepted GLB, then rendered actual
front, profile and three-quarter Cycles views. Nose/profile and lip volume are
clearer without a visible eye, jaw or makeup regression. The result is still a
generic parametric face and does NOT establish identity likeness, commercial
quality, print readiness or user approval.

New additive model, preserving every earlier GLB:
`public/models/couture-fan-v20-face-r1.glb`, 12,991,544 bytes, SHA256
`d6d09d97c467aeda12011f27c7dca408d7e55221481df62cac6204ce58889671`.
It has 176,904 vertices, 334,762 triangles, 80 objects and 5 packed images.
Reimport checks found one head, two eyes, two hands, ten nails and fourteen fan
rotors; gown containment passed 11,774 samples, worst ratio 0.98224.

Package was rebuilt, then all 92 Python tests passed in 16.770 seconds. Frozen
and current ZIPs are byte-identical; ZIP CRC and `git diff --check` passed.
Frozen package: `public/downloads/froge-v20-face-r1.zip`, 15,344,699 bytes,
SHA256 `a0af812274c835be19ff4b837217c359f6c2b88cf97864b98ef0e9486688c543`.
No frontend source changed, so no redundant frontend build was run.

Site 38, GitHub draft PR7 and Oracle remain unchanged. No publication, SSH,
paid Astra call or installation occurred. Photos/history/keys/pairing,
cancellation, 600s AI, 900s Blender, JSON data-only and limits are unchanged.
Next stage should improve couture detailing or natural hair surface language.

Durable canonical Site Git saves confirmed: source/tests/three actual renders
`b6657eb`, additive GLB `1434a07`, frozen installer `decc058`. Push succeeded
after a transient history-fetch HTTP 500; no force push or rewrite was used.

# Emerald/navy material retention r1 rendered and tested — 2026-09-10

Workspace maintenance removed the local checkout after the eye stage. The same
canonical Site Git project was cloned again at clean `01e4102`; no overlapping
Blender/test process or conflicting edit was found. Site version 38 was confirmed
through Sites before work. This bounded stage addresses colour loss only.

The exported eyes-r1 GLB proved the cause numerically: satin dress metallic 0.15
and transmissive crystal metallic 0.25 created broad chrome-white reflections.
Runtime now caps satin metallic at 0.06 and crystal metallic at 0.08 while keeping
dielectric coat, restrained sheen/transmission and bounded roughness. The GLB
export gate now rejects sheen-bearing satin above 0.061 and transmissive crystal
above 0.081, preventing this regression. The v20 reference fixture now separates
deep navy cloth `[0.008,0.032,0.09]` from emerald crystal instead of using two
similar teal materials.

The first satin-only trial still left chrome-like crystal panels and was visually
rejected; it is not in source or public artifacts. The accepted production run
was exported and reimported by Blender 4.3.0 before two actual Cycles renders.
Front and three-quarter views retain navy cloth and emerald panels at both angles.
They remain reflective couture surfaces, but silver is no longer the base colour.

New additive model, without overwriting stage1/hair-r1/eyes-r1:
`public/models/couture-fan-v20-color-r1.glb`, 12,991,544 bytes, SHA256
`1ec41880437639d1c9b4fde23d4107f422afe4edc751f5aeed8d977c9bc90d89`.
It has 176,904 vertices, 334,762 triangles, 80 objects and 5 packed images.
Reimport checks found one head, two eyes, two hands, ten nails and fourteen fan
rotors. Gown containment passed 11,774 samples, worst ratio 0.98224.

Twenty-four focused tests passed before the accepted render. Package was rebuilt,
then all 92 Python tests passed in 17.523 seconds. Frozen/current ZIP byte equality,
ZIP CRC and `git diff --check` passed. Frozen package:
`public/downloads/froge-v20-color-r1.zip`, 15,344,528 bytes, SHA256
`4f65761958e39efe7ef3a9571993da2ded0db34f1935c9f071226fa3c27d6f28`.
No frontend source changed, so no redundant frontend build was run.

Visual acceptance is limited to colour/material retention. It does NOT establish
reference likeness, commercial quality or print readiness. Site 38, GitHub draft
PR7 and Oracle remain unchanged; no publication, SSH, paid Astra call or install.
Photos/history/keys/pairing, cancellation, 600s AI, 900s Blender, JSON data-only
and limits remain unchanged. Next stage should improve face or garment detailing.

Durable canonical Site Git saves confirmed: source/tests/actual renders `96d408d`,
additive GLB `418b7f9`, frozen installer `3bc0f1f`. Push to `main` succeeded.

# Reduced soft-glam eye exposure r1 rendered and tested — 2026-09-10

Started from clean canonical Site Git `302ed92` with no conflicting Blender or
test process. This bounded stage only changes eyelid/orbit deformation for the
existing `soft_glam` portrait profile. Neutral portraits retain the established
20% symmetric aperture adjustment. Soft-glam now uses 36% closure plus an 8%
upper-lid bias, keeping the upper lid heavier without resizing or moving the eye
globes. A new unit test verifies the smaller aperture, upper/lower asymmetry and
that points outside the orbit remain unchanged.

The production runtime generated and exported a new additive model without
overwriting stage1 or hair-r1:
`public/models/couture-fan-v20-eyes-r1.glb`, 13,035,924 bytes, SHA256
`d271aeb4ae490d7f9810064b9f9d96743e11fe092094764815dddcc8033277a8`.
Blender 4.3.0 reimported that GLB before rendering. It contains 176,904 vertices,
334,762 triangles, 80 objects and 5 packed images; structural checks found one
head, two eyes, two hands, ten nails and fourteen rotors. Gown containment passed
11,774 samples with worst envelope ratio 0.98224.

Actual reimported Cycles renders inspected: face front and face three-quarter,
saved under `docs/reviews/v20/` with `eyes-r1` names. The upper lid covers more of
the iris, the lower opening is narrower, and neither reviewed view shows globe
penetration through the face. This is visual acceptance only for the requested
eye-exposure defect. The face remains visibly parametric and does NOT establish
reference likeness, commercial quality, print readiness or user approval.

`python3 scripts/package-blender.py` ran before the complete suite. Sixteen
focused tests passed, then all 92 Python tests passed in 16.885 seconds. ZIP CRC,
frozen/current byte equality and `git diff --check` passed. Frozen reviewed
package: `public/downloads/froge-v20-eyes-r1.zip`, 15,344,047 bytes, SHA256
`84a1fb3b632b4f96fedb73e22f134d83b2d1ef8987df65ad39e57b0be7ada4fe`.
No frontend source changed, so no redundant frontend build was run.

Site version 38, GitHub draft PR7 and Oracle remain unchanged. No SSH, paid Astra
request, publication or installation occurred. Photos/history/keys/pairing,
cancellation, 600s AI planning, 900s Blender execution, data-only JSON and limits
remain unchanged. Next bounded stage should address face proportions or couture
detail; always preserve these additive artifacts and inspect reimported renders.

Durable canonical Site Git saves confirmed: source, tests and actual render
evidence `f2d2526`; additive real GLB `d88f057`; frozen tested installer
`0325320`. The initial combined push returned an HTTP 500 after updating the
remote ref. A credentialed history refresh proved the remote already contained
all three commits; no force push or history rewrite was used.

# Hair silhouette r1 rendered and saved — 2026-09-10

Started from clean canonical Site Git89d90f5. Implemented one bounded hair stage:
asymmetric side-part hairline, broad low diagonal crown roll instead of a narrow
tower, and nine shallow surface ribs over the rear bun joined as one object.
The first attempted roll was too pointed and was rejected. A later fitted rim
made floating wires after head rotation; it was removed before the final build.
Neither rejected version is included in the final source or public model.

Final production runtime generated and exported a new additive model without
overwriting v20stage1:public/models/couture-fan-v20-hair-r1.glb. Actual GLB was
reimported before review:176904vertices,334762triangles,80objects,5packed images;
1head,2eyes,2hands,10nails,14fan rotors; containment11774samples,max0.98224,
pass. GLB SHA256 da15033e1a5850d1addbd18c5cc31aa56d8ce1d419202d5cae79bef28827d95b.

Inspected actual Cycles renders from the reimported output: front and3quarter
from the saved GLB generation, plus a profile from an independent identical-
source generation. PNGs are in docs/reviews/v20/ with hair-r1 names. The final
front/3quarter run took65.49s; the profile run32.84s. The broad roll is cleaner
than the rejected point and hairline is asymmetric; no floating wires remain.
The hair still reads too much like a smooth cap, bun folds are subtle, and this
does NOT establish reference likeness, commercial quality or print readiness.

Package rebuilt before the full suite.29focused tests and then all91Python tests
passed; full run16.884s. ZIP CRC and current staged-payload byte equality passed
through the installer test. Frozen reviewed package:
public/downloads/froge-v20-hair-r1.zip,15343838bytes,SHA256
efb439deeb364e2cedc13a5d10abe762b9fc35e11624b3060fa3eb47b9ffafbe.
Normal reproducible froge-v20.py/zip are now ignored; reviewed packages retain
explicit names. No frontend source changed, so no redundant frontend build.

Site38, GitHub draftPR7 and Oracle remain unchanged. No SSH or paid Astra call.
Limits, cancellation, photos/history/keys/pairing and data-only JSON unchanged.
Next bounded stage: improve couture facet/seam language or face proportions;
do not merely raise polygon limits. Always inspect actual reimport renders.

Durable Site Git saves confirmed: source+review cfbfaa3, additive real GLB
a156f8a, frozen installer beed73a. All three pushes to canonical main succeeded.

# Brow source recovered after workspace maintenance — 2026-09-10

Canonical checkout recovered from Site Git d8df36e after workspace maintenance
removed the prior checkout and Blender installation. Foreground handoff confirms
no foreground transfer remains. Fresh checkout stayed at d8df36e throughout this
bounded recovery/test stage; no conflicting edit was observed.

Reapplied the previous stage's uncommitted runtime/portrait.py change from the
recorded patch: refit brow fibres after sculpt, one tapered surface-fitted dark
underlay for soft_glam, remove undersampled vertex brow mask. This is recovery
of previously rendered work, NOT a new visual iteration or new likeness result.
Source SHA256:8a21a4de8818f1d4a8e07706f5519c1b8ff631ff55aff8cd272e947975ec62e9.

Rebuilt scripts/package-blender.py FIRST, then all91Python tests passed in16.917s;
git diff --check and v20ZIP CRC passed. Full installer test compared every staged
payload file against current source. Test Oracle messages use mocked transport;
no SSH/Oracle installation or paid Astra request took place.

Restored existing review archive without regenerating models:
libfile_13ff303155fc8191992663d56018967b, file_00000000f5cc82069aa9cc2c21ff3d87,
version0, froge-v20-brwi-review.zip, SHA256
3fa6795f3331a7ad3adb704c77b34da541ca28be576762a6379af6d4546ce864.
Current local copy:/workspace/scratch/95d608cd4d09/recovered/froge-v20-brwi-review.zip.
It contains the earlier actual GLB,2actual reimport renders and review report.
Earlier geometry:175925vertices,332840triangles,79objects; the brow is more
continuous but too graphic; natural hair and face likeness remain unfinished.

No new Blender generation/render occurred in this recovery stage. Blender is
not currently installed. Sites native get/credential and canonical Git work;
the local Sites skill/script package was removed by maintenance and its read
returns unavailable. Existing Site38 confirmed through native get_site.
Continue according to the previously read Sites lifecycle; restore its local
package before any preview/build/deployment flow that requires its scripts.

Frozen public/downloads/froge-v20-stage1.zip remains byte-identical, SHA256
a02a395bc98ec83f45a2c68be0b0a39778fd9b00bc7862383565ebee2085bbb3.
Normal generated froge-v20.py/zip contain the recovered brow source and are
local reproducible outputs, not the frozen stage1delivery. Rebuild via
scripts/package-blender.py after a fresh checkout before payload tests.
New local ZIP SHA256:98282a9692b4ef4abaee964aa9625bd06fd03b837b7708cdea370d7f8b6f695a.
This checkpoint saves source and generic updater fingerprint, not new binaries.

Next bounded stage: restore real Blender runtime, verify hair changes through
actual exported/reimported renders; keep source and archive checkpoints separate.
No publication, GitHub PR change, Oracle update, access change or budget change.

# Confirmed durable stage1 save — 2026-09-10T02:15:18+02:00

Site Git push f33df97 SUCCEEDED, including source342c06a, all3realGLBs (4d7daeb,
b716d8c), visual report/PNGs and frozen reviewed installer.
Frozen package:public/downloads/froge-v20-stage1.zip. SHA256 and36-file source
comparison:docs/reviews/v20/STAGE1_HANDOFF.md. Use this frozen package for stage1
review; normal froge-v20.py/zip were regenerated while the next brow stage was
editing portrait.py and are not the frozen artifact. Those newer changes remain
untouched; continue their own tests/checkpoint. No foreground transfer remains.
The hourly task is enabled, schedule02:00–09:00 Europe/Amsterdam; native lookup
reported a run at00:06:43UTC. Site38/GitHubPR7/Oracle deployment unchanged.

Final checks at01:55 Europe/Amsterdam:33targeted Python tests passed after the
last source edits; earlier full91passed. Frontend74passed across initial and
focused rerun; TypeScript/production build passed. Final36-file payload equality,
all relevantZIP CRC checks and actual revision2 installer export gate passed.
Mixed2person GLB with only1makeup head reimported:663632triangles,23564containment
samples,max ratio0.982227. No Blender/test processes intentionally left running.

# v20 foreground stage saved — 2026-09-10

Foreground work complete. Read docs/GENERATOR_V20.md for exact deliverables,
known visual shortcomings, working Blender path and priorities for scheduled
02:00–09:00 Europe/Amsterdam continuations. No duplicate foreground editing job.
Three real GLBs, actual before/after PNGs, embedded public/review-v20.html and full
v20installer are saved in this repository; manifest:docs/reviews/v20/manifest.json.
Site38 and GitHub draftPR7 remain unchanged. No Oracle install or paid Astra run.
Main geometry/export defects improved; photographic quality is NOT achieved.
Final test results and source commit are recorded in the concluding save note.

# v20 overnight work active — 2026-09-10 01:47 Europe/Amsterdam

Read docs/GENERATOR_V20.md first. User requests autonomous corrections until09:00;
hourly continuations02:00–09:00 created. Foreground work currently active; do not
overlap a second edit session. Site38 and GitHub draftPR7 remain unchanged.
Real Blender runtime now works; visual geometry/export fixes and bounded Astra
render-review/refinement implemented. 91Python tests passed before latest hair
iteration; final renders, packaging and frontend checks underway. No live paid
Astra, Oracle install, deployment, print or likeness claim. Prior notes below
are historical and their Blender-unavailable statements are superseded.

# v19 handoff saved — 2026-09-09

Final application/runtime source abb94c2 pushed successfully to Site Git.
Worker draft PR: https://github.com/teslaeco/Froge-MPC-2-test/pull/7
GitHub head:72f46895009020a63cfc0c67b8def0d5284d515a,
branch:codex/v19-couture-current-runtime. Includes PR6 budgets and full current
Oracle portrait/photo runtime, not the separately saved newer Site frontend.

Standalone froge-v19.zip saved successfully, version0:
libfile_44951d0ea99c8191a6f1a3601c996923; file_000000009c5881f482a3ad7ef0ccd8a8.
Local delivery:/workspace/scratch/95d608cd4d09/deliverables/froge-v19.zip.
15332079 bytes; SHA2569ee87bf071600b6fdf990ef57872e8250c3ac021b4eaf3e87140fe3b7423493d.
Identity metadata applied successfully. Do not regenerate to redeliver.

82 Python +74 frontend/API/photo tests passed. No Blender, Oracle install,
photo likeness or deployment pass. Site38 remains live. Actual full reference
model outcome is BLOCKED by missing execution access, not completed by tests.
Next:run the included installer on the existing Oracle host, inspect its retained
GLB/BLEND and execute six real review renders before accepting appearance.

# v19 source and installer prepared — visual/Oracle validation blocked

See docs/GENERATOR_V19.md for the concrete defect, implementation, installer and
remaining verification. Dedicated fitted couture replaces the v18 sweatshirt
construction, using the newer Site v16 portrait/hand/photo/group baseline.
82 Python tests and 74 targeted frontend/API/photo tests passed; TypeScript,
production build, ZIP CRC and all 33 payload file comparisons passed.
Legacy generic updater version detection was corrected to v19; its 3 tests passed.
Package: froge-v19.zip, 15332079 bytes, SHA256
9ee87bf071600b6fdf990ef57872e8250c3ac021b4eaf3e87140fe3b7423493d.

No actual new model GLB, Blender render, Oracle installation, paid AI generation,
face identity match, game rig or print validation was performed. Do not label
this requested visual outcome complete. Source checkpoint 475fdd6 was pushed to
Site Git after one expired credential and a transient HTTP500; native Site
still reports published version38. No publishing request/action was made here.
The old build samples remain in their existing saved versions; this fresh
checkout does not contain the ignored four fashion-v16 GLBs. Do not deploy it
until those existing assets are restored and the model is visually verified.

The final source and reviewable worker PR/persistent installer are being saved.
The worker installer runs the actual couture fixture without AI, checks reimport
and preserves its GLB/BLEND for review, with rollback on failure. Six-view review
script: oracle_connector/verify_couture_runtime.py. No SSH credential exists in
this session; the user must execute the concrete installer on Oracle before
live behaviour or image similarity can be assessed.

# v19 couture integration in progress — 2026-09-09

Canonical checkout: `/workspace/sites/froge-mpc-2-studio`, based on Site Git dd3e257.
Native Sites get_site confirms latest version 38, owner-private. GitHub PR #6
remains open at 032413a and contains time/prompt changes over a much older anatomy
baseline. Do not overwrite the Site v16 portrait, photo, replay, group or recovery
code with that branch. GitHub v18 couture explicitly calls person with sweatshirt;
this contradicts the supplied fitted crystalline gown.

Implemented so far: independent closed fitted-gown numerical mesh, real garment
thickness, conformal facets, pleated fan and solid linked rotors; dedicated Blender
adapter uses existing detailed portrait/hands rather than sweatshirt/trousers.
Integrated contract, satin/crystal materials, head/makeup controls and GLB reimport
gate. Preserved three-person support. Integrated 600s AI / 900s actual Blender
budgets including saved-scene replay, corrected elapsed progress clock and forced
cancellation cleanup; 5000 UTF-16-unit prompt limit follows the existing JS editor.

Checks: Python compilation passed; five numerical/contract tests passed (closed
seams, winding/volume, physical shell thickness, bounds and three-person budget).
No Blender runtime is installed. A network request to install bpy was cancelled
by the execution service; no install or real Blender render has succeeded.
No Oracle execution connector or SSH key is available. No paid AI call made.
Do not label geometry tests as a Blender pass, face likeness, or completed visual
quality. Source is in progress; package, remaining tests and final review pending.

## Group preview triangle budget fixed — 2026-09-09

User asked to change the one-million limit so the three figures fit. Clarified that
renaming triangles as polygons/polyhedra does not change rendering cost. Updated
src/studio/aiModel.ts to MAX_MODEL_TRIANGLES=2000000, covering Oracle v16's supported
three-person budget (3*640000). Oversized scenes still fail with the actual count
and limit; empty scenes have a separate clear error. No geometry was decimated.

Reproduced the old rejection using the REAL application loadModel, GLTFLoader and
Draco decoder on public/models/fashion-group-v16.glb. After the change the identical
file loads:1294664 triangles,3 anatomical heads,30 nails,199 Mesh objects,15
materials,5 decoded images. Default framing dimensions are finite:10 x7.84574
x4.48621 cm. This was a Node adapter for workers/image decoding, not a mocked
model loader and not a WebGL/browser rendering pass. Verification script:
/workspace/scratch/cfff2f2e6b11/verify-group-loader.mjs (temporary test harness).
Full production build and TypeScript passed. Source868131794689da730f851a8845ff951f2da8c92b
pushed; Site38 privately published successfully at2026-09-09T14:00:19.642029Z.
Saved version:appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_45a547ce22f481918379a7fb06774120.
Deployment:appgdep_6aa1665ed8d88191a166e87b255922e5; environment revision2 retained.
URL:https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Archive validation:63 files,213768689 expanded bytes; four fashion GLBs and full
v16 installer present. The native terminal success was verified directly. This
completion note is documentation only and requires no rebuild or redeployment.
Oracle v16 installation, visual quality improvements and the chat timer diagnosis
are separate and remain unresolved. Do not claim those were fixed by this change.

## AUDIT — publication is not task completion — 2026-09-09

Read docs/DIAGNOSTYKA_2026-09-09.md before resuming. Confirmed source defect:
fashion-group-v16.glb has1294664 triangles; src/studio/aiModel.ts rejects anything
above1000000. Single models pass; the group cannot pass the same loader. Prior
fashion-group deep-link test mocks that loader and the viewer. No application fix
or new deployment has been made in this diagnosis. Oracle still reports v15 in
native logs at2026-09-09T13:22:53.665Z. All27 application job records are terminal;
latest fails the person/portrait anatomy gate in40.013s, not an ongoing render.
The supplied shared chat visibly ends at code edits with2/3 plan items complete.
Cause of its continuing timer remains UNKNOWN: no execution telemetry for that
conversation is available. Do not repeat the unsupported frozen-UI explanation.
Preview browser access failed ERR_BLOCKED_BY_CLIENT; no visual browser pass claimed.
No Oracle SSH credential is available here. User authorization is not the blocker.
Model likeness/quality and Oracle installation remain incomplete.

## PUBLISHED — Site37 / Oracle package16 — 2026-09-08

Native private deployment SUCCEEDED at2026-09-08T22:00:00.893150+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Direct study: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=fashion-group
Application source:276edd08d3a9e050a1558032fc5ef4d0b9b18400.
Saved version:appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_b2a84747c88c819185487902adbe5c0b.
Deployment:appgdep_6aa085128f908191a7472edae1642114.
Archive:/workspace/scratch/8e338e0fb0bb/froge-site-v16-final.tar.gz,180369413 bytes; includes all four GLBs and both full installer files. Existing download aliases verified22 GET/HEAD requests and preserved through canonical byte-identical content. Owner-private audience preserved. No additional browser access is needed for publication handoff.

Delivered files already saved successfully: /workspace/scratch/8e338e0fb0bb/v16/froge-v16.zip (15319375 bytes), modelki-studia-v16.zip (124712811 bytes), modelki-studia-v16.png (1241030 bytes). Canonical file identities and hashes:docs/fashion-v16-deliverables.json. Do not duplicate or regenerate merely to re-deliver.

Oracle16 has NOT been installed by Codex. User uploads froge-v16.zip to Oracle Cloud Shell, extracts it with python3 -m zipfile, runs froge-v16/froge-v16.py, then checks the server after FROGE_V16_OK. No API key or connection reset. The full package fixes group budget admission and includes all anatomy/texture files. The tiny older v15 installer was a delta, not evidence of missing assets.

Three procedural wardrobe studies and a group are visible on the Site, but exact likeness, original bed composition, photorealistic store quality and rig/print readiness have NOT been achieved. This work changes the generator, reference handling and structural checks; it does not train AI weights. Keep these limits clear. Next quality work must be driven by review of the actual GLB, not claiming that counts of eyes/nails establish similarity or beauty.

This final checkpoint is documentation only after the published application commit; it needs no application rebuild or redeploy.

## v16 archive size recovery

Source e7baed7822b669f19868060b3d67389c1fe47e17 pushed successfully after separating generated output from source. Native save rejected the330188570-byte archive for exceeding256MiB; no successful new version/deployment yet. Found11 identical historical update ZIP aliases. They now resolve through one shared filename list in the Worker; build verifies byte equality before removing duplicate copies from dist. All22 GET/HEAD alias checks against the compiled Worker passed, including Range/query/status preservation. Production build passed. Repackage the same complete models/full installer with deduplicated aliases, then save/deploy exact new source. Standalone delivered artifacts unchanged.

## v16 publication recovery: generated output separated from source

The Git service returned502 on 68MB and29MB pushes; no remote changes were applied (main remainedbc07732). A buffered retry stalled and was interrupted, then remote was reconciled again. Unpublished render-release history is retained locally as v16-render-checkpoint. Current main applies the identical application/runtime/source fixture changes without committing newly generated v16 ZIP/Python/GLB outputs. These are build artifacts, not hand-authored meshes. Their generators and scene inputs are committed; exact model bytes, Blender sources and installer are saved under the deliverable identities below. Build/package includes the generated artifacts and keeps live URL/audience unchanged.

For a fresh checkout, first run Blender4.3.2 with scripts/render-fashion.py -- --output <temporary-folder>, then copy the four resulting model.glb files to public/models/fashion-{1,2,3,group}-v16.glb. npm build regenerates both full installer files. To recreate the standalone bundle use scripts/package-fashion.py. Do not deploy a fresh checkout without generated models; verify their SHA256 using the saved deliverable manifest/model bundle.

## v16 final build and deliverables verified — publish next

2026-09-08. Production build passed. Site sources include failed-POST acknowledgement recovery, submission race grace, classified errors, subject labels and optional letterbox crop. Prior API/UI/photo58 tests passed; final history/deep-link5 passed; connector16, scene contract14, quality7, installer3, updater7 and legacy repair3 passed. No claim that an upstream provider/network outage cannot recur.

Full v16 ZIP: 15319375 bytes; includes all anatomy and textures, no previous delta dependency. Standalone ZIP/model bundle/preview saved successfully; exact identities and SHA256 in docs/fashion-v16-deliverables.json. Previous v15 delta was intentionally small, reusing existing data. Oracle v16 NOT installed here. User must upload froge-v16.zip to Cloud Shell, extract it and run froge-v16.py, then check server; installation preserves connection/OpenAI key/jobs and tests the group before accepting, with rollback on failure.

Actual Blender4.3.2 exports and compressed group reimport verified3 heads,6 eyes,6 hands,30 nails. Final group655761 vertices/1294664 triangles/197 objects; three single GLBs plus group copied to public/models/fashion-*-v16.glb. Final visual check complete. Models are rough procedural wardrobe/pose studies; NOT exact likenesses, NOT photorealistic sale-quality characters, NOT model-weight training. Examples are labelled accordingly. Do not represent structural checks as beauty/likeness validation. The group is a comparative studio arrangement, not the original bed composition.

One curly clothed person reached247656 vertices; final human allowance320000 vertices/640000 triangles per head avoids failing broader variants. Planner estimates300000/600000 and80objects per person; max3people/256objects, nonhuman limits unchanged. Unsupported seated legacy outfits fail explicitly rather than silently rendering standing. Final model content unchanged by budget-only adjustment; actual exports already below even previous limits. Installer source rebuilt and exact-payload tests passed after adjustment.

Next: commit/push unchanged built source, package and privately deploy; record native success/URL. Live version36 remains until publish succeeds. Desired deep link: /?example=fashion-group. Preserve owner-private audience.

## v16 verified progress — publication pending

Source now includes same-ID recovery after failed POST acknowledgement, 90-second grace when a status check overtakes submission, storage-failure classification, per-photo subject labels and conservative letterbox preparation. API/UI/reference tests58 passed; Oracle connector16 and scene contract14 tests passed; portrait/installer9 and update7 passed before final export polish. Full self-contained v16 ZIP is ~15.3 MB, includes all anatomy/texture data; old v15 delta is frozen.

Three authored fashion references exist in oracle_connector/examples/fashion-*.scene.json. Real Blender export verified3 heads,6 eyes,6 hands,30 nails. Further preview corrections joined skin joints, aligned head/neck position, separated clothing from skin and corrected sRGB body color. Final render/Draco group reimport running; source-generated artifacts must be collected from /workspace/scratch/8e338e0fb0bb/fashion-v16 only when render job finishes. Need final preview check, copy GLBs to public/models, build/push/deploy and save standalone v16/model packages. Source is a procedural, approximate likeness study, NOT training of Astra weights and NOT approved for sale. Oracle16 NOT installed by Codex; user must run full installer.

## In progress — v16 diagnosis and recovery

Live Site36 remains unchanged. Production logs confirmed POST /api/blender/jobs 503 after 30.7s and connection 503. D1 history confirmed two later failures (20:42 and20:47 UTC) from a multi-person scene exceeding v15 single-person geometry limits; one intervening group job succeeded. No evidence of missing anatomy assets. User reports v15 installed; current Oracle needs later capability confirmation.

Working fixes: same-ID acknowledgement recovery; 90-second submission/status race grace; classified storage errors; letterbox preparation and per-photo subject labels; 3-character geometry budgets preserving each portrait/hand; new bob, curls, ponytail and fashion garment renderer. Not validated or deployed yet. Need real Blender group export and renders, lifecycle tests, full v16 installer/archive, source push and Site publication. Do not claim training weights or exact reference likeness.

## Published — Site version 36; Oracle installation still pending

The private Site deployment succeeded: `appgdep_6aa06de1f7788191bc41116edf07d6d5`, source `075c943dece2f139d165e0414ab55437fd90fdd9`, saved version `appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_68124f77ca8481918dd514584cf283a9`. Live direct model: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=seated-study . The corrected R8 girl is now a persistent Site asset and the direct link prevents old job history replacing it.

Generator v15 source, tested one-file installer and quality capability admission are deployed with the Site. Oracle itself has NOT been updated by this session: the owner must upload `froge-standard-postaci.py` to Cloud Shell, run `python3 "$HOME/froge-standard-postaci.py"`, then check the server in Froge. No need to import the girl's GLB. Preserve this distinction in follow-up replies; do not claim likeness or sale readiness.

## Ready for publication — 2026-09-08 portrait v15

Selected authored girl: `/workspace/tools/seated-girl-r8`, GLB SHA256 `3434af9d0e9043665a9e1a40e7ee97be5056655531c17cfbac80fad32df2428c`. Site asset `/models/seated-girl-studio-v2.glb`, direct view `/?example=seated-study`. Two anatomical hands, ten rose nails, baked makeup, lashes and connected wrist. Original body/clothes/boots retained. GLB and BLEND reopened, four renders checked. All deliverables saved with version guards; identities in `docs/seated-girl-deliverables.json`.

Oracle source v15 / renderer3 / portrait1: strict human plans, reusable portraits/posed hands, UV/eye/nail export gate, long wavy hair and dedicated iris texture. 37 Python tests and the UI/API checks passed. Real full figure reimport: 198343 vertices, 388759 triangles, 16696288 bytes, nine images; missing nail rejected. Current worker remains v14/r2, not remotely upgraded. One-file installer `/downloads/froge-standard-postaci.py`; Cloud Shell command `python3 "$HOME/froge-standard-postaci.py"`. It checks installed base hashes, preserves pairing/jobs, tests a real Blender export without AI and rolls back on failure.

Production build passed. Next: push exact source, package and privately deploy; record the returned deployment result. Do not claim Oracle v15 installed until live health confirms it. No photographic-likeness, print-ready or sale-ready claim. Previous deployment remains live until publishing succeeds.

# Seated portrait — selected actual model, delivery saved

2026-09-08. Selected authored correction is /workspace/tools/seated-girl-r4;
delivery copies /workspace/scratch/8e338e0fb0bb/dziewczyna-poprawiona.
Real GLB6732792 bytes,124320 mesh vertices,238956 triangles, two eye globes.
SHA2566bc36b0025280fd09072b5acea08ae0142ffba93df9b35190dd5a5ee4072d787.
ZIP18448691 bytes includes editable blend, GLB, front/three-quarter/full-body
renders, before-face render, Polish import instructions and verification JSON.
Archive CRC check passed. All delivered PNGs are Cycles renders of the exported
GLB after reimport, NOT the generated albedo reference. The latter remains an
intermediate source asset and was not passed off as a final 3D model.

Corrected the initial lip-texture offset; discarded the first angular strand
experiment. Final hair samples its own continuous surface with thinner strands.
Actual review confirms substantially better anatomy than the original blank
face and attached ellipsoids. Likeness remains approximate. Original hands,
garments and boot details remain coarse; do not call this ready for sale.
Verified20 retained body/pose-part bounds within1e-5, removed old facial inserts,
two eye globes, embedded GLB images, reopened blend with10 active packed images.
Blender lazily loads image pixels; has_data immediately on reopening is not a
valid corruption test. Pixel buffers were loaded and verified nonempty.
Three existing numerical portrait-deformation tests also passed.

The authenticated browser downloads DID both finish despite event-wait timeouts.
Do not claim the UI download button failed: two actual GLBs were verified.
Site35 and Oracle14/revision2 remain the installed versions. This authored
correction is imported with Wczytaj GLB lub scene JSON; it does not update the
general generator, publish a catalog product, or replace the user's job history.

Final modeling source4ef4aa8 is pushed to canonical main. All9 ordered Library
writes succeeded with local metadata applied. Exact identities are recorded in
docs/seated-girl-deliverables.json. ZIP library_file_id is
libfile_0ae9d12363bc8191b346c9acaa6b0f1e; GLB is
libfile_bfe8f86be71c81919241155c4e2f8903. Do not regenerate these files merely
because chat delivery was interrupted. No Site deployment was made.

---

# Seated portrait — source recovered and authored correction in progress

2026-09-08. The user's latest attachment provides a clear face reference:
upload/02-Screenshot_20260908-142407.png. Do not ask for this image again.
On the user's explicit browser request, the existing authenticated Site tab2
successfully reloaded Site35 and the actual seated job. Both the UI export and
the original model endpoint downloaded files despite the browser event waiter
timing out. Verified GLB headers and JSON: original file is1986592 bytes at
/workspace/scratch/froge-1348617b-a464-4272-b105-a9573f677bbe.glb.
The app's auth rules and audience were not changed and no identity was forged.

Original model has a2143-vertex blank face, separate729-vertex ellipsoid nose,
60-vertex lips, floating eye/iris parts and144-vertex main hair strips. An actual
Blender before-face render confirms the primitive-feature quality problem.
Blender4.3.2 now WORKS at /workspace/tools/froge-blender-4.3.2/blender. The earlier
extracted binary in synchronized scratch was truncated; extract outside scratch.
Runtime launch verified149268904-byte executable, bpy4.3.2, normal exit.

New scripts inspect_seated.py, seated_albedo.py and seated_girl.py replace the
old primitive head and hair while retaining the downloaded body/pose. A newly
generated neutral albedo based on THIS woman's reference is saved as
assets/seated-girl-albedo-r1.png. It is an intermediate texture, not 3D proof.
No Cardi identity texture or facial sculpt is copied. Reuses generic anatomy,
baking/hair methods and independent eye UVs. Initial bake completed; attribute
cleanup corrected to remove only its two own attributes. Export and render
review still pending. No corrected model delivered or Site update deployed yet.

---

# Portrait continuation — source assets required (superseded above)

2026-09-08. User rejects the new seated girl's facial quality and asks to use
techniques from earlier authored faces. Current Site35/Oraclev14 texture revision2
are confirmed healthy. This is a modeling-quality limitation, not another texture
installation failure. No new Site or Oracle update was deployed in this turn.

Added scripts/reference-portrait/portrait_shape.py: seven bounded independent nose,
mouth, lip, jaw, chin and cheek controls on the actual connected anatomical head,
with fixed orbital region. Three tests on the bundled4531-vertex head passed:
neutral identity; finite/bounded deformation; no triangle inversion under extremes;
orbital vertices unchanged; invalid input rejection. This is authored-model tooling,
NOT yet integrated into the Oracle photo generator and NOT a corrected likeness.

The exact current seated job is1348617b-a464-4272-b105-a9573f677bbe. Stored reference
is40145.png; original hash6b822e9e9c6c6875e2b4cf82ad97a4df0e87c5f580324b4069d255e8a2b2ac25.
Its screenshot has coarse facial primitives; generic person also lacks seated pose
and per-face controls. R9 prior study used separate authored sculpt/makeup/baked
texture/hair tools; do not copy Cardi identity or generated skin into this woman.

Read-only retrieval through the documented Sites OAI-Sites-Authorization bearer
failed with401 from the app: Zaloguj sie, aby korzystac ze swojego Blendera.
A freshly obtained platform token gave the same result. Do NOT forge user identity
headers, expose credentials, change auth rules, or create a public route for these
files. Original photo and GLB have NOT been downloaded. Ask the user to attach
40145.png plus the GLB from Pobierz GLB + tekstury; current attachments are only
screenshots, insufficient to inspect the actual facial geometry or fine likeness.
No new photo/model has been generated or claimed to be shop-ready.

Official Blender4.3.2 runtime downloaded successfully (368852356 bytes) and extracted
to /workspace/scratch/8e338e0fb0bb/blender-runtime/blender-4.3.2/.
The executable launch check FAILED with exit139 before producing output. This
is NOT a working local Blender runtime yet; do not claim rendering succeeded.
Resolve the runtime launch before any actual model/render verification.
Next: use the received GLB/photo, inspect named head/hair/body objects, apply the
portrait pipeline to the actual seated model, export/reimport GLB and visually
compare front/three-quarter/profile before delivering or updating the generator.

---

# Portrait quality investigation — latest photo model

2026-09-08. Site35 is deployed and native logs now confirm Oracle v14,
rendererRevision2 and sceneReplay=true: texture repair installed successfully.
Latest seated photo job1348617b-a464-4272-b105-a9573f677bbe succeeded; 174.9 s AI,
4.0 s Blender. Earlier photo job0f92ac48-a18c-496a-8a9d-7bcf4d7ef452 succeeded
with the generic person model (18.0 s Blender). Both preserve reference40145.png.

User explicitly says the face is poor and compares it to the better authored
Cardi B face. Confirmed root limitation: Oracle scene_contract has no portrait
shape controls, person only supports standing/performing poses, and the authored
R9 sculpt/makeup/hair pipeline was never included in the generic worker. The new
seated model appears to use primitive body/head construction; exact saved scene
is not available through the current worker API. Do not describe it as a likeness.

R9 uses authored geometry, neutral generated albedo, separate eyes, baked makeup,
long-strand hair and actual GLB reimport/render verification. Its likeness still
was approximate. Reuse its techniques, not the Cardi face or texture for another
woman. Added bounded generic lower-face controls in portrait_shape.py; integration
and visual checks remain pending. No generator update or new Site published yet.

A Blender4.3.2 runtime download from official download.blender.org is in progress
(the HEAD request succeeded). No installed local Blender has been found otherwise.
Requested the user's actual saved photo/GLB read-only using the Sites tool-provided
OAI-Sites-Authorization bearer credential, without spoofing identity or changing
access. No private live Site browser navigation. Download results pending.

Next: inspect downloaded reference/model, restore an actual local Blender renderer,
then build and visually compare an authored face improvement before any delivery.

---

# Site35 published — texture export fix and saved-plan replay

Native private publication succeeded at 2026-09-08T18:19:12.196549+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Source: 886dec8f0feb38cf5525b70d47631396b0659f04
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_a589d899b120819198f15a9ddd6c0d0b
Deployment: appgdep_6aa051424d7c8191844febfcbc403237
Environment revision2; existing owner-only audience preserved.

64 Python tests +53 UI/API tests passed; TypeScript and production build passed.
Archive61 files /256105572 expanded bytes, every entry matched the build, required
D1 migrations present, no public Python bytecode. The first archive check prepended
dist twice; corrected the check and validated the unchanged archive successfully.

Deliver public/downloads/froge-napraw-tekstury.py (36763 bytes), SHA256:
83662d94b59fefec7db2b314139957b778bfc16c13b9dc7d8b6c6cfe06ec0a9d
User uploads this ONE file to Oracle Cloud Shell and runs:
python3 "$HOME/froge-napraw-tekstury.py"
No new ZIP or photo upload required. The script installs rendererRevision2 while
preserving connectorVersion14, pairing, AI configuration, photos and job history.
It requires a REAL isolated Blender GLB export with eight fabrics and both albedo
and normal maps; a failed check rolls code back. SSH and real Blender are not
available here, so this Oracle installation/export check has NOT run in this turn.
Do not claim the user's model has already been regenerated.

After FROGE_TEXTURE_OK: refresh the existing Site, check connection, then choose
Wykonaj zapisany plan bez AI on failed job2ac35f11-9632-4a09-8dda-79963c037703.
Site exposes that button only with live sceneReplay=true and rendererRevision>=2.
Replay creates a new isolated job from the saved JSON, preserves private photo
history, bypasses AI entirely, and does not repeat an AI call on renderer failure.
Native FROGE_ORACLE_HEALTH logs now include the bounded renderer revision and replay
capability, so the next turn can verify installation instead of guessing from a ZIP.
The deployed Site and repair file are saved in canonical Git; no duplicate storage.
No paid AI generation, provider switch or direct live Sites URL browsing occurred.
This completion checkpoint is documentation only; deployed source is the SHA above.

---

# Texture export repair — implementation checkpoint

2026-09-08. Latest screenshots and native logs CONFIRM installed Oracle v14,
OpenAI ready, photoInput true. This supersedes the prior v2 diagnosis below.
Private Site34 remains deployed. Latest failed job 2ac35f11-9632-4a09-8dda-79963c037703
contains the girl photo reference and fails in /runner/run.py with
Use at most 8 materials and 8 images. The saved JSON plan is on Oracle.

Implemented separate 8-material / 16-image export budgets with unused datablock
cleanup, shared textile normal maps retained, and a saved-scene replay path that
bypasses every AI call. Source photos and the old failed job remain preserved.
Site offers the replay only after live sceneReplay + rendererRevision 2 capability.
Until then it offers the self-contained froge-napraw-tekstury.py repair.
The helper uses the existing Cloud Shell SSH key and VM; no new ZIP required.
It validates known installed v14 file hashes, uses the checked updater and backups,
and requires a real isolated Blender export of 8 fabrics with packed albedo/normal
maps BEFORE restarting the worker. Failed export invokes code rollback.

Checks complete: 64 Python tests and 53 UI/API tests passed. Dedicated tests cover
saved-scene replay without AI/provider settings, preserved private photos, duplicate
submission protection, capability gating, rejected unknown installed code and updater
rollback when the export check fails. TypeScript and production build passed. No local Blender
runtime is available; a package lookup could not install one. The helper performs
the real exporter regression on Oracle when the user runs it. It has NOT run here;
no claim the user's model or remote worker is repaired yet. No paid AI request.

Canonical v14 ZIP and installer fingerprint refreshed. Source checkpoint 5fd59f3
is pushed; the final build/source commit and private publication follow. The only
remaining installation is the user running the one-file helper in Cloud Shell.

---

# Site34 published — live paired Oracle confirms v2

Native private deployment succeeded at2026-09-08T17:40:49.253234+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Source: 2da7d29ed3162f19015a248cc0559eb4f7d3cc99
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_8f100c20103c819182aff9a60aaedf9b
Deployment: appgdep_6aa04881d8e881918c9187865fb53b9b
Environment revision2; existing owner-only audience preserved.

Native operational logs at2026-09-08T17:41:06.923Z now explicitly report:
FROGE_ORACLE_HEALTH {"connectorVersion":2,"provider":"ollama","ready":true,"photoInput":false}
This is the freshly read paired worker capability, not an HTTP200 assumption or
the version of a downloadable ZIP. The current blocker is confirmed legacy v2.
No new job, paid generation, provider switch or Oracle installation performed here.

public/downloads/froge-napraw-oracle.py is saved in canonical Git and included in the
published Site. Deliver it as a download; user uploads it beside their existing v14
ZIP in Oracle Cloud Shell, then runs: python3 "$HOME/froge-napraw-oracle.py"
It prints four stages and FROGE_DIAG with actual localhost version/provider/photo
readiness. Three focused helper tests (SSH mocked) and58 UI/API tests passed; full
production build and TypeScript passed. Archive60 files /256059385 expanded bytes,
all matched build, v14 fingerprint verified, no bytecode in public downloads.

Next: read native FROGE_ORACLE_HEALTH logs after the user runs the helper. If localhost
reports v14 but the paired endpoint still reports v2, investigate service/tunnel
mismatch instead of inventing another geometry update. If provider is still ollama,
photo generation requires the user's explicit OpenAI selection in Studio.
This completion checkpoint is documentation only; deployed source is the SHA above.

---

# Oracle update recovery launcher — source checkpoint

2026-09-08. User asks again whether the update was installed and authorizes a
replacement if needed. Native get_site confirms active Site33 and its existing URL.
Native logs through17:25:45Z show only connection/history/model GETs, no new job
POST. Paired endpoint was last saved on2026-09-06; no connection change observed.
Personal Context found no v14 installation success/error output, only older update
screenshots including a missing-file failure. Runtime secret values are redacted;
do not try to retrieve keys through alternate routes or print secrets.

Added public/downloads/froge-napraw-oracle.py for running inside Oracle Cloud Shell.
It locates the user's already-uploaded v14 ZIP independent of filename suffixes,
verifies all22 files against the known v14 payload fingerprint (timestamps ignored),
uses the existing SSH key and existing141.148.242.30 VM, runs the existing checked
updater with backup/rollback, then reads authenticated localhost health without
printing keys. FROGE_REPAIR_OK confirms only installed v14; FROGE_DIAG separately
states provider/readiness/photo capability. It never submits a model or switches
the user's AI provider. Missing keys, bad ZIPs and SSH/update errors stop clearly.
This helper is a script update, not a new generator protocol; Oracle remains v14.

GeometryUpdate now offers the helper and one copyable Python command. Added strictly
bounded FROGE_ORACLE_HEALTH server logs (version/provider/ready/photoInput only) to
enable future native operational diagnosis without exporting runtime credentials.
Three helper tests pass with subprocesses mocked; no actual SSH/update ran here.
Production build/publication pending; last deployed version is Site33 below.

---

# Site33 — Generate status and recovery published

Native private deployment succeeded at 2026-09-08T17:18:08.489519+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Source: ddfbe07e9807faeac9ff0037519a9a601d395b3f
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_20ff3710432c8191a0388f95359b8fa7
Deployment: appgdep_6aa0432e49348191b9b8b5c790aa0a49
Environment revision2; owner-only audience preserved.

Production build and TypeScript passed;57 focused tests passed. Archive59 files,
256052562 expanded bytes, all entries matched build output. Source pushed before
save. UI changes below are published; no paid generation or Oracle update ran.

The end-to-end generator issue remains blocked by the legacy paired Oracle worker.
Ask for the actual final output from the operator's v14 update command. Do not
conflate a ZIP upload or this Site deployment with a successful Oracle installation.
No extra live URL fetch/browser verification was performed after publication.
This completion checkpoint is documentation only; deployed source is the SHA above.

---

# Generate blockage — verified source, publication pending

2026-09-08. User says Generate/chat still appears stuck after uploading v14.
Read-only native logs show no new POST /api/blender/jobs; all19 D1 jobs remain
terminal, latest65216976-125d-4141-b4ad-dd9fa4f50db6 succeeded, all reference_photos
empty. HTTP200 connection reads do NOT establish readiness/capability.

Authenticated Studio UI showed "Generator wymaga aktualizacji", contradictory
"AI i Blender sa gotowe.", model qwen2.5-coder:7b, disabled Generate even with a
typed description, and OpenAI settings' pre-v4 update branch. Thus the paired
endpoint still reports a legacy worker, not the v14 photo service. Exact worker
version was not exposed by the old UI. No real generation or Oracle installation
performed. Do not tell the user this UI repair installed v14 or repaired ChatGPT.
Browser direct API navigation was ERR_BLOCKED_BY_CLIENT; do not retry or bypass.
Follow Sites environment: use native logs/database for live diagnostics, and only
the supervised internal preview for any subsequent explicitly requested browser QA.

Fix: explicit connected-worker version and photo capability, last successful check
time, refresh progress and stale-check protection, a precise legacy-worker reason
beside Generate, canonical v14 update guidance. Removed the contradictory ready
message for incompatible workers. Submission prep now stays inside try/finally,
with an immediate duplicate-click lock, and "Wysyłam zlecenie" is distinct from
accepted-job generation. Existing data/models and Oracle ZIP unchanged.

57 focused UI/API tests passed, including legacy-worker recovery and preparation
failure releasing Generate. Production build/deployment pending. Last deployed
version remains Site32 below until a subsequent completion checkpoint.
Remaining blocker: Oracle operator needs to provide the actual update result
(FROGE_UPDATE_OK or FROGE_UPDATE_ERROR) or server diagnostic output; uploaded ZIP
is not proof of an installed/restarted worker. Original girl photo still missing.

---

# Site32 — new photo drafts separated from old prompts

Native deployment succeeded at 2026-09-08T16:32:37.121079+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Source: d1f41a3669759fd77fd7bab755ef2df8bb254f89
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_5d62b443e9b88191be0055eb1dd37e36
Deployment: appgdep_6aa0389191648191baa0a4454d06eb38
Environment revision2; owner-only access unchanged.

Completed draft-reset UI fix described below is published. Build and TypeScript
passed; 29 focused UI tests passed. Archive59 files /256051652 expanded payload
bytes, below256 MiB; all entries matched the build. Saved Cardi R9 asset unchanged.
No browser QA, paid generation, live job mutation or Oracle installation performed.

The girl model is NOT generated: the attachment is a screenshot with a tiny thumbnail.
Exact title search for40145.png found no matching file; unrelated fuzzy candidates
were not used. Ask the user to attach the original photo. Oraclev14 installation
remains necessary to run photo jobs; the existing ZIP, copyable update command and
connection refresh are available next to Generate. New-model reset preserves saved
history and photos selected after the reset; refreshing the entire page clears draft
photos. The published source is the SHA above; this checkpoint is documentation only.

---

# New-photo draft reset — verified fix before publication

2026-09-08. User reported the old Cardi B prompt appearing stuck while selecting
40145.png to create a different girl. Their attachment is Screenshot_20260908-181806.png,
showing a small thumbnail, not the original photo. Do not claim to have reconstructed
the new subject from a full reference image or generated her model in this session.

Read-only native D1 inspection confirmed all19 stored jobs are terminal. Latest job
65216976-125d-4141-b4ad-dd9fa4f50db6 succeeded (72.8s); reference_photos is empty for
every job. The screenshot explicitly shows the Oracle v14 prerequisite. No live
job was cancelled, no DB data was changed and no worker upgrade was installed.

Implemented: completed-job prompts no longer auto-fill new descriptions; a New model
button clears the draft and preview while keeping history. Selecting the first photo
starts a separate draft, preserves manually entered instructions and invalidates old
model loads. Completed prompts are collapsed and saved previews labelled accordingly.
Photo-related Oracle update instructions now sit by Generate, with Copy command and
Refresh connection buttons; status refresh preserves selected photos.

29 focused UI/regression tests passed, including actual ModelStudio draft lifecycle,
late history and late GLB responses. WebGL/image decoding are stubbed, not a visual
quality check. TypeScript passed. Next: build, package, push and publish existing
owner-private Site. Source baseline85c1193; live version31 remains unchanged so far.
Final handoff must explain Oracle v14 is still needed and ask for original40145.png.

---

# Site31 — photo-guided model creation published

Native deployment succeeded at 2026-09-08T16:13:56.575443+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Source: dd9d24c88e915f67ca3f9b337dfa2e88bd85c90d
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_405642eb8efc819192e4654e5ada71e3
Deployment: appgdep_6aa033eeda7481919fde57b5226778e1
Environment revision2; existing owner-only private audience retained.

Published: 1–4 photo inputs with previews, view labels, optional text instructions,
explicit generation, private saved references and retry from history. The download
froge-oracle-update.zip now contains worker14 and photo_input.py. The installer and
updater ZIPs passed CRC and every entry matches its source. The Site client/Worker
production build passed. R9 example GLB checksum is unchanged.

Archive: 59 files, 256050099 expanded payload bytes, below 256 MiB. All archive files
matched the build; D1 migration0002 is included. The first archive-check command used
an incorrect local root (the helper packages a dist/ prefix); correcting that check
verified the unchanged archive successfully. No packaging defect was found.
52 focused Vitest + 43 Python tests passed; TypeScript passed. No browser QA requested,
no paid API generation, and no new model's appearance/facial fidelity was verified.

Remaining user action: install the provided v14 package on the existing Oracle VM
using the Studio instructions, and use the configured OpenAI provider. This session
has no Oracle SSH key and did not install the worker. The Site refuses photo jobs
until that worker explicitly reports version14+ and OpenAI photoInput capability.
Do not report a locally tested photo transport as a completed Oracle generation or
photogrammetric reconstruction. The GitHub mirror was not synchronized; Site Git is
the canonical source. This final checkpoint is documentation after the published SHA.

---

# Photo-guided 3D generation — verified source, before build/publication

2026-09-08. Completed the v14 photo protocol, compatible installer/updater, UI,
owner-scoped R2 image persistence, D1 metadata migration and reference-based retry.
Actual image bytes are sent as Responses input_image blocks; local Qwen is blocked
for photo jobs. The public job JSON never contains base64 image data. History images
remain authenticated and available independently of the current Oracle connection.

Validation: 52 focused Vitest tests and 43 Python tests passed, plus TypeScript and
git diff whitespace checks. Tests cover private storage and owner isolation, limits,
old-worker/provider gates, job idempotency/replay, failed storage, real local worker
HTTP/SQLite and Responses image transport through a local SSE fixture. UI tests use
a normalization stub because jsdom has no browser canvas decoder; no browser QA or
paid visual generation was performed. These tests do not establish portrait fidelity.

This source follows durable checkpoint 56abcc1. Next: rebuild the downloadable v14
ZIPs and Site, check archive size/migrations/source correspondence, save and publish
the exact source to the existing owner-private Site. The live Site is still version30.
No Oracle installation was performed; the user must install the offered v14 update
on their existing VM before photo generation is available there. Pairing, API keys,
saved models and R9 example assets are preserved.

---

# Photo-guided 3D generation — implementation checkpoint

User requested adding model creation from photos to the existing Studio.
Recovered canonical source e52fa41 into /workspace/sites/froge-mpc-2-studio
because the older scratch checkout no longer exists. Site identity and private
access preserved. Dependencies installed using the Sites helper.

Authored selection of 1–4 JPG/PNG/WebP images with thumbnails, view labels,
removal and bounded JPEG normalization. The job API validates actual JPEG
headers/dimensions/size, stores image bytes in owner-scoped R2 paths, and keeps
metadata with the D1 job. Added a constant-default reference_photos column in
new migration 0002; existing migrations remain untouched. History/retry keeps
references. Photo requests require a version14 worker that explicitly advertises
OpenAI photo input; old text-only workers cannot silently ignore attachments.
TypeScript check passed. This code has NOT been deployed or fully validated.

Next: complete the Oracle vision-input protocol and compatible updater, verify
cross-owner isolation, malformed inputs, retries and end-to-end image forwarding
using local fixtures, then build/save/deploy the existing Site. No paid API call
or Oracle installation has been performed. The live Site remains version30.
Photo-guided scene construction is an approximation, not photogrammetry or a
verified facial reconstruction. OpenAI image input schema checked against:
https://developers.openai.com/api/docs/guides/images-vision

---

# Site30 — R9 model and three prompt guides published

Native deployment succeeded at 2026-09-08T15:06:56.474272+00:00.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Direct model route: /?example=cardi-study
Source: 0b7696990077b85d61bb5e7eb20425c55b54a165
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_74fa415f89dc81918b79dc0ca2588f02
Deployment: appgdep_6aa0246025a48191b4f6ec973f5db349
Environment revision2; existing private audience retained.

The live Studio now serves the verified R9 GLB, actual fullbody/face renders and
three copyable prompt guides. Only the new-generation prompt fills the generator;
existing-model and photo-reference work is directed to Codex/Blender. Generator
behavior and exact-likeness limitations are unchanged. No new model generation,
paid service, Oracle installation, shop launch or artist contact occurred.

Final archive: 57 files, 256,002,331 expanded payload bytes, below the 256 MiB
limit. Every archived file matched the local build; GLB checksum unchanged from
the verified R9 standalone. Client/Worker build and TypeScript check passed.
The legacy installer URL is preserved by a verified GET/HEAD rewrite to the
canonical byte-identical ZIP, avoiding a duplicate 14,957,337-byte payload.
Publication was confirmed by the native terminal success response. No browser
QA was requested or performed. This documentation checkpoint follows deployment;
the exact published source is the full SHA recorded above.

---

# R9 website update and prompt guides — prepared for publication

2026-09-08. User explicitly requested updating the existing website and prompts
for the same or a better 3D model. The selected existing Site remains owner-only
private. New publication is authorized; no audience change or Oracle installation.

Replaced public/models/cardi-reference-study.glb with verified R9, byte-identical
to the saved standalone file. SHA256:
cec15f0c6c229b53e07c0070e6b5a6fb231a72784a4e48159b8615f622933407
The example now requests revision9 with no-store and labels the R9 appearance.
Added actual fullbody and three-quarter renders in a collapsible guide. Three
copyable Polish prompts cover new stylized generation (1225 characters), editing
the current model with Codex/Blender (1104), and detailed modeling from reference
photos (1372). Only the first prompt can fill the 2000-character generator field;
reference-based and imported-model edits are clearly directed to Codex/Blender.
Filling or copying text never starts generation. No exact likeness guarantee.

Production client/Worker build and TypeScript check passed. Built GLB and two
renders match their source bytes; hosting identity retained. The existing Oracle
update ZIP passes CRC and each entry matches the current runtime source; v13 alias
is identical. No new tests for this reversible asset/copy UI change. Browser QA
was not requested, so no preview or live-site browser session was started.

The first native save rejected the 270,959,445-byte expanded archive because it
exceeded the 256 MiB limit; no new version was returned. Deduplicating the legacy
texture-fix ZIP in the built output saves 14,957,337 bytes. The Worker preserves
that GET/HEAD download URL by serving the byte-identical canonical update ZIP;
the build refuses deduplication if the two files differ. The R9 model and images
retain their original quality. Source 557bf95 was pushed before the rejected save.

Rebuild passed. A smoke check of the actual built Worker confirmed legacy GET
and HEAD responses preserve the canonical ZIP bytes, content type, request
method, query string and headers. Unknown ZIP paths still return 404.
Next: push/package this exact revision, save one Site version, deploy privately
and wait for completion. Prior live Site29 retained until success. Saved
standalone artifact IDs are unchanged.

---

# R9 requested appearance correction — verified and saved

2026-09-08. Sebastian requested softer lips, a smaller nose, a slim silhouette,
darker warm skin, better hair, and violet stilettos matching the dress. Selected
output: /workspace/scratch/8e338e0fb0bb/cardi-r9-verified. Delivery copies:
/workspace/scratch/8e338e0fb0bb/cardi-r9-deliverables. Do not deliver the rejected
cardi-r9-review or cardi-r9-final candidates. Earlier saved versions are retained.
Finalized source and verification are in the same Git commit as this checkpoint;
the previous recovery commit 21a5054 was pushed to canonical Site Git.

Changes: smaller nasal landmarks/projection with local alar surface relaxation;
softer, narrower lips with satin rose-brown pigment; slimmer bust, waist, hips,
seat and calves; a shared warmer darker skin multiplier; sleeker black hair with
finer normal relief, 300 tapered strand paths and restrained specular response;
violet satin stilettos. Shoe scalar colors are converted from sRGB to linear to
match the dress image palette. A radial dress-clearance pass resolves visible
thigh penetration after slimming while preserving the intentional cutout.

Actual exported GLB reimported and front/three-quarter/profile/fullbody renders
visually reviewed. GLB: 10,806,008 bytes; 196,261 vertices; 384,202 triangles;
10 meshes/materials; 6 embedded images. Header, internal resources, finite
geometry and textured-mesh UVs checked. Bounds: 0.722995 x 0.455524 x 1.800684 m.
Blend reopened; all six active material images packed. SHA256:
cec15f0c6c229b53e07c0070e6b5a6fb231a72784a4e48159b8615f622933407
See docs/cardi-r9-verification.json. Four review renders: 720x840, 24 Cycles
samples with denoising. No web build or app tests were needed for this asset pass.

All six replacements succeeded with local identity metadata applied:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version8
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version8
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version8
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version5
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version8
- cardi-studium-profil.png: libfile_87a2bbee07fc819180c07725b349088c version1

The face/hair remain stylized; faithful portrait likeness is not established.
The existing generated neutral albedo plus baked cosmetics remains active; the
rejected photo-derived diffuse experiment is not used. No scan, artist approval
or print readiness claim. No paid service, artist contact, shop launch or Oracle
installation. Live private Site29 still serves R7; import the saved R9 GLB into
Studio to use it there. No Site deployment was inferred from this model request.

---

# R8 corrected body/face study — files saved; likeness still approximate

2026-09-08. Selected output /workspace/scratch/8e338e0fb0bb/cardi-r8-final;
deliveries /workspace/scratch/8e338e0fb0bb/cardi-result. Do not deliver the rejected
cardi-r8-review, review2 or selected folders. Last verified modeling source before
this final documentation commit: 2af8dfa, pushed to canonical Site Git.

Actual GLB reimport and front/three-quarter/profile/fullbody renders inspected.
GLB 10,135,844 bytes; 176,033 vertices; 345,104 triangles; 10 meshes/materials;
6 embedded images. Binary header/internal resources/finite geometry/textured UVs
checked. World bounds 0.724243 x 0.464748 x 1.800694 m. Blend reopened and active
material images are packed. SHA256:
4f90b3a41f6bfd3227cf3c61cb17dd32c04fceed9e0e6c00bee66ee7f23a74e3
Full verification: docs/cardi-r8-verification.json. Review renders 720x840,
24 Cycles samples with denoising. No application tests/build/deployment performed
because this was the standalone model correction, not a website update.

Changes: stronger waist/hip/bust silhouette, higher hands and natural elbows,
localized dress cutout, lower-face spacing and restrained native lip-contact
compression, 8% eyelid-aperture compression with darker irises/larger pupils,
and post-subdivision hair clearance eliminating the visible cheek penetrations.
Active facial material remains the previous generated neutral albedo plus glam
cosmetics, baked at 2048px. The photo-projection experiment was rejected for
patchy pigment and an unnatural lip surface; its photo is NOT in this deliverable.

All six writes succeeded, local identity metadata applied; earlier versions retained:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version7
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version7
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version7
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version4
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version7
- cardi-studium-profil.png: libfile_87a2bbee07fc819180c07725b349088c version0

IMPORTANT: the user's full faithful portrait goal is still not met. Face/hair
remain stylized and the reference fingernails/tattoos/expression are incomplete.
Do not call it artist-approved, commercially printable or a faithful scan.
No Oracle installation, artist message, paid service, store launch or audience
change. Live private Site29 still serves its R7 example; the new saved GLB can
be imported into Studio. No website-publication request inferred from model edits.

---

# R8 reference projection rejected — final anatomy/material review running

Three photo-projection candidates in cardi-r8-review, review2 and selected were
rejected for pale/patchy pigment, an unnatural lip surface and remaining cheek
penetration. Do not deliver them. Their source experiment is retained for audit.
The accepted R7 neutral generated texture is being reused with corrected face
spacing, a continuous lip-contact compression, refined eyelid aperture/dark
pupils and post-subdivision hair clearance. Preserve revised body, natural elbow
pose and localized cutout. New output: /workspace/scratch/8e338e0fb0bb/cardi-r8-final.
This output must still pass actual GLB visual review. No new delivery or publication.

---

# R8 body and reference-surface work — in progress

2026-09-08. Resumed from saved R7 blend/GLB (Library version6) and source d515625.
Current task: improve actual Cardi B body and facial appearance. Original neutral
F9 photo is used for a new landmark-guided diffuse bake excluding eye pixels;
this replaces the generic generated face texture. A residual mesh sculpt corrects
lip depth/cheeks/nasal base. Body waist/hip/bust, hands-on-waist pose and cutout
placement are being revised. Candidate has NOT passed render/export review.
Do not deliver until checked. Saved R7 files and live private Site29 retained.
No Oracle install, artist contact or store launch. No exact likeness claim.

---

# Prompt handoff and conversation Markdown — complete

User narrowed task to website update and prompts, then requested a full Markdown
handoff for a new chat. No new model sculpt or Oracle installation performed.
Added referenceCharacterPrompt.ts and collapsible studio prompt section; explicit
button fills textarea without starting generation. Combined description1233chars,
below2000limit. Copy accurately describes R7, with exclusions and a1:1 limitation.

Site29 published at2026-09-08T13:07:39.892608+00:00, environment revision2, private.
Source: fe3bc19fe6c1e515097a4971dbe839889b6a7b97
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_8d5cb1cff6e08191b4ed9d1ae194e790
Deployment: appgdep_6aa008803484819192c246db41e06e5b
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Build/typecheck passed. Archive56files,268,206,150expanded payloadbytes.
Caught a truncated unversioned worker ZIP before publication; restored from the
versioned v13 alias only after checking every entry against current source.
Final archived ZIP CRC passed. Root cause of truncation unconfirmed; not an Oracle
runtime fix. R7 GLB checksum unchanged. No new tests for reversible prompt UI.

Saved standalone Markdown:
FROGE-instrukcje-do-nowego-czatu.md
Library: libfile_13687a627cac81919d407c0a4a595a9a version0
File: file_000000009e9c8210a7b33e4fa0e87eae
Local: ../handoff/FROGE-instrukcje-do-nowego-czatu.md
2028words,15914UTF-8bytes; placeholders removed, code fences balanced.
Includes project origin/evolution, actual completed work vs limitations, original
characters and artist approval/B2B plans,3prompts, recovery/source instructions.
Current model remains R7 with approximate likeness. No artist contact/store launch.

---

# Revision 7 — saved and privately published

Site28 succeeded at2026-09-08T12:51:52.594765+00:00.
Source: d17f556a29f09cfb266df8ac4d20ee8f7b4e1b3e
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_9fabb992fc948191b9d3ad88bea4bfcb
Deployment: appgdep_6aa004d377e08191830e30e9d4e609dd
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Private audience retained; environment revision2. Build/typecheck passed.
Archive56files,268,204,200expanded payloadbytes; native tar268,257,280bytes.
Asset checksum verified: b1c291d902b904953123e4d3559015ecd3e7a5ab7607b98e9bccf19989a6e6db

Selected model ../cardi-r7-final, delivered in ../cardi-r7-deliverables.
GLB9,474,256bytes;166,989vertices;327,016triangles;10meshes;6embeddedimages.
Actual GLB reimport front/three-quarter/fullbody reviewed. No external buffers.
Changed nasal base width, lip width/height, chin target; fuller tapered brows,
rose/plum shadow and lipstick coverage. Eye positions, R6 hair and outfit retained.
Rejected ../cardi-r7-contact because groove deformation caused lumpy highlights.
Do not deliver that rejected output. Selected source restores original lip depth.

All five files saved, identity metadata confirmed:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version6
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version6
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version6
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version6
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version3

The user's faithful portrait requirement is still not met. Do not call this
photoreal, artist-approved or commercially printable. Mouth still slightly open;
face and hair remain stylized. No general Oracle-generator update or installation,
artist contact or shop launch. No fresh JavaScript tests for this asset-only pass.
Canonical Site Git pushed; no GitHub mirror claim. No subagents used this turn.
Further work must address the underlying likeness limitation, not merely keep
renaming cosmetic revisions or announce completion without visual evidence.

---

# Revision 7 selected model saved — publication pending

Accepted ../cardi-r7-final; do not use rejected ../cardi-r7-contact. All five
standalone replacements in ../cardi-r7-deliverables succeeded with local metadata.
Existing GLB/blend/front/fullbody IDs now version6; three-quarter ID version3.
Source matches selected output after reverting the rejected mouth-depth edit.
GLB9,474,256bytes;166,989vertices;327,016triangles;10meshes;6embeddedimages.
All buffers/images internal; actual GLB reimport and3views inspected.
SHA256:b1c291d902b904953123e4d3559015ecd3e7a5ab7607b98e9bccf19989a6e6db
Production build/typecheck passed. Web example revision7 staged. No new JS tests.
Next: push/package/private Site28 update and terminal confirmation. Site27 live.
Faithful likeness remains unfinished; no artist or print-readiness claim.

---

# Revision 7 review complete — rejected contact deformation

Root rejected ../cardi-r7-contact: the groove correction produced a lumpy upper
lip and unnatural highlights. Restored face.py/build.py to2496f25. Accepted
candidate is ../cardi-r7-final, whose front/three-quarter/fullbody actual GLB
renders were reviewed. Keep wider alar targets, slightly narrower lips/restored
chin spacing, fuller brows and rose/plum pigments. Mouth remains slightly open;
do not claim it was closed or faithfully reconstructed. Face still stylized.
Next: save accepted five files, update example revision7, build/private publish.

---

# Revision 7 mouth contact correction — final review running

First R7 front review confirmed improved brow body and rose/plum makeup, but
mouth contact still appeared excessively open. Actual midline BVH sampling found
z1.617 surface y-0.15697 versus upper lip y-0.16667: a deep groove/overhang.
Added topology-preserving localized refinement after face fit to shallow this
contact, relax upper lip projection and lift lower lip by at most0.8mm.
Selected final candidate now renders into ../cardi-r7-contact; do not deliver
../cardi-r7-final as the final accepted result. Wait for and review real GLB
reimport renders. Current live Site27 and saved R6 files remain unchanged.

---

# Revision 7 reference face pass — in progress

User again asks to finish likeness. Compared R6 front to the saved Road to F9
Bustle neutral and Allure frontal photos. Identified overly narrow nasal base,
wide/open lip treatment, thin eyebrows and overly brown rather than rose/plum
cosmetics. Current candidate broadens alar targets, narrows mouth corners,
reduces lip vertical exaggeration and slightly restores chin length. Eye globe
centres and existing eyelid geometry are preserved. Fuller tapered brows and
rose/plum pigment, generic broad mouth seam covered with a narrow contact line.
Source at scripts/reference-portrait; integrated real GLB/reimport rendering
runs in ../cardi-r7-final, log ../cardi-r7-final.log. Not visually accepted yet.
Live Site27 and all R6 deliverables remain unchanged until review passes.
Do not claim faithful likeness or that the generator was updated. No artist
contact, shop launch, or Oracle installation. No new external 3D service found.

---

# Revision 6 — saved and privately published

Site27 succeeded at2026-09-08T12:29:47.900675+00:00.
Source: f1afa086b44d0bec9ad1056a142d777a6eecc7b5
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_1dcbe048e1008191acdce5fed058b05a
Deployment: appgdep_6a9fffa46da881918bab9a4a3f7d06a8
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Existing private audience and environment revision2 retained. Production build
and typecheck passed. Archive56files,268,204,432expanded payloadbytes;
native stored tar268,257,280bytes, under256MiB. Model checksum matched archive.

Final selected build: ../cardi-r6-final. Root reviewed front, three-quarter and
fullbody renders from reimported GLB. 9,474,528bytes;166,989vertices;327,016triangles;
10meshes/materials;6embeddedimages. GLB2 with all buffers/images internal.
SHA256:312b83e3874eb7e357c65f9e948aa5b49ab6c15c5a8ae73d4d6972853a6e1864
Integrated refinements: nasal/lip/chin spacing, cheek shape; fine hair normals and
filaments, hairline/ear clearance; bent arms toward hips, original fingers;
asymmetric hem with a localized crescent and gathered flounce. Makeup and silver
strappy heels retained. Earlier wide-gap integrated fullbody was rejected.

All five deliverables saved successfully, local metadata confirmed:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version5
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version5
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version5
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version5
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version2
Local deliverables: ../cardi-r6-deliverables. Source in scripts/reference-portrait.
Three agents assisted: face_r5, reference_hair_outfit and outfit_r5.

IMPORTANT: faithful photoreal Cardi B likeness is still not achieved. Face and
hair mass remain stylized; individual micro-anatomy/expression are not reconstructed.
No artist approval, commercial print-readiness or general Oracle-generator update.
No shop launch or messages sent to artist. No JavaScript tests rerun for this asset
revision. Current source is saved in canonical Site Git, not a GitHub mirror update.
Any next likeness work must start from these saved files and compare reference
structure, not rerun earlier rejected models or call the portrait complete.

---

# Revision 6 final model saved — private publication pending

2026-09-08. Final selected build: ../cardi-r6-final. Root reviewed actual GLB
reimport renders from front, three-quarter and fullbody. Localized one-thigh
crescent opening replaces the rejected broad gap. Fine hair detail, ear clearance,
refined facial spacing, bent arms and completed dress flounce are integrated.
GLB: 9,474,528 bytes, 166,989 vertices, 327,016 triangles, 10 meshes/materials,
6 embedded images. Valid GLB2, no external buffers/images. SHA256:
312b83e3874eb7e357c65f9e948aa5b49ab6c15c5a8ae73d4d6972853a6e1864

All five standalone replacements succeeded with local metadata in
../cardi-r6-deliverables: cardi-studium.glb, cardi-studium.blend,
cardi-studium-twarz.png, cardi-studium-sylwetka.png are now Library version5;
cardi-studium-twarz-3-4.png is version2. Existing Library IDs retained.
Production build and typecheck passed; web example now revision6.
Next: package validation, source push, native save/private deploy, terminal check.
Live Site26 remains until that succeeds. No Oracle/general generator update.
Likeness still approximate/stylized; no scan, artist approval or print readiness.
No store launch or artist contact. No new JavaScript test run for asset revision.

---

# Revision 6 final review checkpoint

Integrated ../cardi-r6-integrated GLB/front/three-quarter were reviewed. Face spacing,
fine hair normals and ear clearance are improved; coherent eyes retained. Fullbody
revealed a crescent opening too broad across both legs, making a dark floating-band
appearance. Root localized it over one thigh and welded the remaining front edge.
Selected final build is running into ../cardi-r6-final (log ../cardi-r6-final.log).
Do not publish the earlier integrated fullbody. Current combined model before this
small hem correction was9,495,140bytes; package is only~210KB below archive limit.
Source is saved; live Site26 and saved R5 artifacts unchanged pending finalreview.

---

# Revision 6 final-detail work — source checkpoint

User accepted R5 improvement and asked to finish. Three agents assisted the new
bounded pass: face_r5 audited actual facial geometry, reference_hair_outfit authored
portable strand detail/ear clearance, outfit_r5 completed posed arms and dress hem.
Integrated source scripts/reference-portrait has finer hair normals and tapered
filaments, hands at hips with original finger topology, angled hem/crescent opening
and gathered flounce. Agents reviewed actual exports. Root reduced hair normal
strength from0.72 to0.36 to avoid a coarse ribbed surface.
Face changes use actual geometry sampling: nasal base down4mm, tip down3mm with
slight depth retraction, mouth assembly down6mm with added vertical lip body,
chin down only2.5mm; cheek fullness redistributed upward. Shared skin mapping
retained. Final combined portrait has not yet passed root visual review.
Output ../cardi-r6-integrated; no new publication or artifact replacement yet.
Live Site26 and saved R5 deliverables remain valid. Next: actual combined GLB
reimport/front/three-quarter/fullbody review, save, build and private update.
Do not claim a scan, exact likeness, artist approval or universal generator fix.

---

# Revision 5 makeup and reference outfit — privately published

Site26 succeeded at2026-09-08T12:03:04.220026+00:00.
Source: d09d2bc1800eec3ddc48cd725e39d178bd4d8897
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_581fa360a71c819182160994a2cdaeb4
Deployment: appgdep_6a9ff9516a488191808dfabb5866c212
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Owner-private audience and environment revision2 retained. Production build passed.
Archive56files,267,172,796expanded payloadbytes; model checksum verified.
Actual reimported GLB8,442,932bytes,154,084vertices,302,098triangles,9meshes,
9materials,5embeddedimages. Front, three-quarter and fullbody reviewed at48 samples.

All five standalone replacements succeeded with local identity metadata:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version4
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version4
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version4
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version4
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version1
Local copies: ../cardi-r5-deliverables; generation: ../cardi-r5-integrated.

Completed: shortened/broadened lowerface, refined almond eyelid aperture, coherent
single irises; visible tessellated eyeliner and112 swept lashes,440 brow hairs
with feathered pigment, rose/mauve shadow, lip contour/satin roughness, warm skin;
welded dress waist, continuous anatomical feet and silver strappy heels.
Reference look verified from several Road to F9 event photos (see REFERENCE_LOOK.md).
Four agents assisted: reference_r5, face_r5, makeup_r5, outfit_r5. Root rejected
initial occluded/pale liner and solid graphic brow ribbons, then integrated/reviewed.

User's faithful Cardi B portrait goal remains UNFINISHED. Current face still has
generic/stylized traits. Hair remains a grouped shell, reference expression and
hands-on-hips pose absent; asymmetric dress hem not reproduced. Do not claim artist
approval readiness or commercial print readiness. No artist messages or store launch.
This is an authored example update, not an installed Oracle/general-generator fix.
No new JavaScript tests were added or run for this asset-only revision.

---

# Revision 5 visually checked — saving and publishing next

Final selected source is scripts/reference-portrait, output ../cardi-r5-integrated.
Root inspected actual GLB reimport front, three-quarter and fullbody at48 samples.
New makeup is visible; solid graphic brow strip replaced with feathered pigment
and hairs. Single eye irises retained. Warmer skin, satin lips, welded dress waist,
continuous feet and silver strappy heels. File8,442,932bytes,154,084vertices,
302,098triangles,9meshes,9materials,5embeddedimages; validGLB2 with internal buffers.
Staged deliverables ../cardi-r5-deliverables. Web example revision5 staged.
Likeness remains approximate/generic rather than verified portrait quality;
stylized hair, neutral expression and incomplete reference hem/pose remain.
Do not claim artist-approval readiness or a universal generator improvement.
Next: Library ordered replacements, production build, source push, archive/private
Site publication and terminal deployment verification. No Oracle deployment.

---

# Revision 5 integrated model rendering

Combined source includes the accepted face, makeup and outfit modules.
Root removed the solid graphic brow ribbon in favor of dark feathered baked
pigment with individual hairs. Final integrated output is ../cardi-r5-integrated,
log ../cardi-r5-integrated.log. Build uses 48 samples for clearer fine cosmetics.
Front, three-quarter and fullbody are rendered only after actual GLB reimport.
Wait for successful completion and inspect all three before publishing. Likeness
remains approximate; reference expression and asymmetric dress hem not recreated.
Live Site 25 / saved R4 artifacts still unchanged. No Oracle or shop launch.

---

# Revision 5 combined source checkpoint — not yet published

Actual face structure and reference footwear changes integrated and reviewed.
Cosmetics source now integrated for review: shaped brows, anatomical eyeliner and
lashes, rose/mauve eye pigment, lined lips, warm skin correction and exported lip
roughness. Final combined GLB has not yet passed visual review. Prior makeup
candidates were rejected because lashes appeared pale and brows too uniform.
Next: review final2 cosmetic candidate, complete one integrated render with the
new footwear, then save deliverables/build/publish if visually improved.
Live Site 25 and saved R4 deliverables remain unchanged at this checkpoint.

---

# Reference likeness and makeup — revision 5 in progress

2026-09-08. User rejected R4 likeness and absent makeup. Exact supplied look is
Road to F9, Miami, 31 January 2020, verified using event photographs. Reference
pages and visual acceptance notes saved in scripts/reference-portrait/REFERENCE_LOOK.md.
Independent asset agents are preparing compatible face structure, cosmetics and
outfit changes outside the Site. Face targets now authored independently of the
generic generated albedo; cosmetics must follow actual eyelids and shared targets.
Face geometry candidate reviewed as an improvement and integrated; eye globes remain
aligned. Cosmetics first candidate rejected for occluded lashes and weak brows;
corrected candidate still under review. Outfit candidate reviewed and integrated:
continuous feet, silver strappy heels and welded/smoothed dress waist. Front and
footwear actual GLB reimport renders checked. Live Site 25 and saved R4 files unchanged.
Do not claim realistic likeness or commercial readiness. No artist contact.
Current candidate directories: ../cardi-r5-face-src, ../cardi-r5-makeup-src,
../cardi-r5-outfit-src; exact-event reference photos in ../cardi-r5-reference.
Next: visually review integrated GLB reimport, save accepted source and artifacts,
then update the existing private example only after genuine visible improvement.

---

# Eye repair and reference outfit — privately published

Site 25 succeeded at 2026-09-08T11:32:30.306718+00:00.
Source: f062be189b0287e7462ea21cd2330e9f9a2fd536
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_905a89b25e388191bca77db637ad530d
Deployment: appgdep_6a9ff2239968819186f38d8e34835def
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Owner-private audience and environment revision 2 retained. Production build
passed; archive 56 files, 266,623,436 expanded bytes; asset checksum verified.

All saved deliverables: ../cardi-r4-deliverables.
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b version 3
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73 version 3
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75 version 3
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f version 3
- cardi-studium-twarz-3-4.png: libfile_0402052f088881919f7373971cdee507 version 0
Library confirmed all five writes and local identity metadata.
Final actual GLB: 7,893,624 bytes, 129,619 vertices, 257,521 triangles, 8 meshes,
6 embedded images. Reimported and rendered from front, 38 degrees and full body.
Root rejected intermediate hair shading and skirt penetrations and fixed both.
Eye duplication/alignment defect repaired. Exact likeness NOT achieved: the face
remains generic, neutral expression, stylized hair and visible waist seam. Do not
claim the user's realistic Cardi B portrait goal complete. No Oracle deployment.
No additional JavaScript tests this asset-only turn; prior tests not rerun.

---

# Eye repair and reference outfit — visually checked, saving

Final selected output: ../cardi-r4-final, staged standalone ../cardi-r4-deliverables.
Actual GLB reimport rendered front, 38-degree portrait and full body, checked by
root. Duplicate eyes and floating lashes removed; aligned gaze, original globe
roundness, local iris atlas. Detached lash corner tips trimmed. Superellipse
skirt envelope covers knee protrusions, smooth complete hem; one hair material
removes patchwork reflections. Previous intermediate knee/hair defects rejected.
GLB 7,893,624 bytes, 8 meshes, 6 embedded images, all buffers internal, valid v2.
Source mirrors selected model; example revision=4. Production build, private
publication and ordered Library replacements are next. Facial identity remains
weak/generic, hair stylized and waist seam pronounced: unfinished portrait.
Do not claim realistic likeness, artist approval or installed generator changes.

---

# Eye repair and new reference outfit — combined candidate rendering

2026-09-08. User correctly rejected Site 24 eye projection. Do not reuse its
full-face eye material. Isolated first repair confirms one iris per globe and
natural socket occlusion; detached source eyelashes were excluded, then a
thin anatomical lash rim added. Dedicated 512px procedural eye texture uses
globe-local UVs, both globe scales restored to original anatomy. Final skin
repair samples a continuous adjacent skin UV instead of clamping to one row.

Three agents: eyes_repair, reference_hair_outfit, likeness_check. Current combined
source integrated in scripts/reference-portrait. New face_fit.py shortens midface
through the same landmark targets used for geometry and texture; no eye-centre
movement. New long centre-part hair and ruched violet dress from latest reference.
Final combined GLB/front/3-4/fullbody generation is running in ../cardi-r4-integrated-output.
Still awaiting combined visual acceptance, archive/build, deliverable replacement
and private Site publication. Existing live Site and saved models remain unchanged.

Do not call this exact likeness. Source generated albedo is still an approximate
neutral portrait; photographs were not reconstructed. No print-ready claim.

---

# Textured portrait revision — privately published

Site 24 published successfully at 2026-09-08T11:01:13.841409+00:00.
Source: 62f1610de73a0e618ad00cf3cc2368d24ce17ec4
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_dde47c0fe5188191997d453e031e1876
Deployment: appgdep_6a9feae1fa6c8191ad626ff028c874db
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Owner-private audience and environment revision 2 retained. Production build and
archive validation passed; deployed GLB checksum matches selected source asset.
All four standalone deliverables below successfully replaced at Library version 2.
No additional JavaScript test run this asset/documentation turn.

2026-09-08: Four Codex agents assisted (audit, original photo, mesh/hair work,
generated albedo). Prompt: docs/CODEX-CARDI-LIKENESS.md. No Copilot invocation.
Selected FINAL assets: ../cardi-textured-eyes/; complete source integrated from
../cardi-textured-eyes-src/. Reject all cardi-expression candidates and the earlier
cardi-textured-output render with exposed eye white. Final image reviewed by root.
True anatomical mesh retained; lower face fitted in X/Z via 32 landmarks, orbital
geometry preserved, 1536px baked PBR skin, projected generated iris/sclera and revised
bob. Generated texture provenance in scripts/reference-portrait/assets/GENERATION.md.
Final GLB 8,795,624 bytes; 119,893 vertices; 238,780 triangles; reimported and rendered.
No original reference photo pixels are directly packed; generated albedo is packed.
Likeness remains approximate/unverified; stylized hair, neutral expression and eye
contours remain limitations. No claim of print readiness or artist approval.
Deliverables saved in ../cardi-textured-deliverables and Library version 2.
Web example revision=3 integrated and privately published.
Installed Oracle generator and original-character/permission workflow unchanged.

---

# Likeness task — visual rejection and texture route checkpoint

2026-09-08: User rejected Site23 face as unlike reference. Concrete Codex task
saved to docs/CODEX-CARDI-LIKENESS.md and pushed (5015e89). Independent agents:
likeness_audit, portrait_revision, reference_photo, face_texture.
Audit found unchanged upper face because old sculpt stopped at z1.674; helmet
hair, inflated lips and mismatched expression also visible.
Expression candidates in ../cardi-expression-* FAILED visual review: skin spikes
through mouth. DO NOT publish or integrate that face or its GLB. Site23 unchanged.
Hair-only improvement ../cardi-hair-src/bob.py may be reused independently.
A generated neutral front face texture is now available for real mesh projection:
../generated_images/exec-ae2c6f9d-775d-42b9-9048-e71260242f74.png (1254x1254).
It is generated artwork, not an original artist photograph or a finished 3D model.
Agent portrait_revision is testing UV alignment/baking on prior neutral topology
in ../cardi-textured-src, with standalone outputs. Await render review before
integration. No claim that generated texture alone solves 3D likeness.
Verified actual reference: Commons File:Cardi_B_at_2026_Essence_Festival_of_Culture,_cropped.jpg
Photographer Runawaymo, CC BY-SA4.0. Viewed locally at ../cardi-reference/cardi-essence.jpg.
No original photograph is included in the deployed model; retain provenance if
subsequent work incorporates it. No artist contact, approval or rights claim.

---

# Generator recovery and reference revision — published

Site23 privately published successfully 2026-09-08T10:32:11.806833+00:00.
Source: 2f30a65e16c66d07d610a6ac88144ab9d793e71b
Version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_065d325092e88191b83b6c813470110f
Deployment: appgdep_6a9fe4171a4881918b5996b6462a0348
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site/?example=cardi-study
Environment revision2 and owner-private access retained. 47 focused tests and full
production build passed. Archive validated; revised model checksum matches source.
All four standalone deliverables successfully replaced at Library version1:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f
Local deliverables: /workspace/scratch/116f83481a3c/cardi-revision-deliverables/
Fixed frontend auto-history race and blank-prompt recovery. No pending live jobs
found in the inspected history. Exact cause of any separate transient freeze remains
unconfirmed. No live Oracle worker update, exact likeness or print readiness claimed.

---

# Generator recovery and reference revision — ready to publish

2026-09-08: Inspected owner-scoped live job history: all 18 rows terminal; latest
Nova job ad5be1dc-9016-4e80-adf8-be0b95d0d959 succeeded in 29.4 s with an artifact.
No pending job was found. Empty prompt on reload explained the disabled button.
Fixed initial history restoration racing with explicit example/model selection.
Completed-job prompt restores only while untouched; added reuse/edit actions and
an explicit reason for disabled generation. No automatic paid generation is started.
47 focused UI/API/Studio tests passed. Full production build/publication pending.
Revised real Blender reference asset: smooth clipped tank neckline/armholes and
sewn edge, fuller clothed proportions, revised lips, cheeks and side-part bob.
GLB 7,276,460 bytes; 114,287 vertices; 226,972 triangles; successfully reimported.
Portrait/fullbody visually reviewed. Likeness remains stylized, not an exact Cardi B
portrait; reference smile is not reproduced. Commercial print topology unverified.
Web replaces existing cardi-reference-study.glb and uses revision=2/no-store.
Standalone outputs staged in ../cardi-revision-deliverables for durable replacement.
This updates the authored example and website UI, not the installed Oracle worker.
Preserve owner-private audience, existing logos and original-character workflows.

---

# Original collection and request workflow — published

Site22 privately published successfully 2026-09-08T10:11:51.940091+00:00.
Source: 62f1b3f3c9ce371fe2ec768c61819770f6721a02
Saved version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_f2ad1932e2208191a9dc02737eb630b0
Deployment: appgdep_6a9fdf52cd48819198b4e1129c0b3cff
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Environment revision2 and owner-private audience preserved. No Oracle update needed.
Studio original character briefs: /?character=nova, /?character=atlas, /?character=lumen.
Shop /shop has collection starters, rights fields, exact model+request ZIP and mailto.
All monetary additions are entered manually; no artist fee or platform rate invented.
21 focused tests and production build passed. ZIP independently decoded/CRC checked.
Remaining: verified external artist reply portal, signed license handling, customer
checkout and B2B fulfillment/payment connectors. Current tool prepares an email draft
for the user to send and records a received quote; it does not authenticate permission.
No new example renders or universal likeness generator were created in this turn.
Original characters are prompt briefs, not new finished figures. Source saved to SiteGit.

---

# Original characters and artist requests — implementation checkpoint

2026-09-08: User chose original fictional characters as first collection, and a later
customer -> artist permission/fee -> B2B manufacture + platform commission workflow.
Implemented Nova/Atlas/Lumen original prompt starters in Studio and Shop. They are
briefs to generate, not newly rendered models or purchasable finished products.
Existing examples and marketplace logos retained.
Commerce product JSON now optionally stores rights/contact/scope, received response,
artist per-unit fee and separate platform commission. Legacy products remain readable.
Requests export the exact owner-scoped model plus text in ZIP; mailto opens an unsent
email draft and requires attaching ZIP. No email is sent by platform, no artist portal,
no payment, accepted legal permission or B2B order is fabricated.
Model/currency mismatch excludes stale artist cost; commission currency is separate.
Records persist using existing D1 product payload/R2 model storage; no schema change.
Source typecheck passed; 21 focused tests passed including legacy data, model/currency
invalidation, private API boundaries and ZIP decoded by Python with CRC verification.
One pre-existing UI test expected removed old connection labels; updated assertions
to the existing four planned marketplace integrations. Production build passed. Private publication pending.
Do not claim external artist/customer access: Site remains owner-private.
Next: finish focused checks, build/save source, publish within existing private scope.

---

# Cardi B study — published and saved

Site21 privately published successfully2026-09-08T09:46:06.255599+00:00.
Application source: 00090885409a46c571b66259232a36b3aa3770a8
Saved version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_b12950d3a0b08191ba3db9c6e6a0088b
Deployment: appgdep_6a9fd93bfed88191af959cc4c46abb2b
Environment2 and owner-private access retained.
URL: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
Direct authored example: /?example=cardi-study; button Cardi B · studium.
Web GLB7,250,180bytes,111406vertices,221496triangles,7meshes/materials; original
deliverable9,978,280bytes retains2048px eye atlas. Both exported and reimported,
portrait/fullbody reviewed. No Oracle update necessary to open this example.
No change to live generator's ability to reconstruct identity: likeness is approximate,
not a faithful Cardi B portrait or photoreal result. No paid3D service was enabled.
All four original files durably saved with IDs recorded below. Source canonicalGit
saved; no GitHub mirror update claimed. Studio logos and earlier models retained.
Remaining quality limits: simplified facial likeness/hair, neckline edge waviness,
no print topology certification. Future media additions need download alias dedup
rather than repeated archive-limit failures; existing aliases all consume~14MiB each.

---

# Publication recovery: archive size

First reference study save rejected because expanded dist268,689,693bytes exceeded
256MiB. No new version or deployment created by that rejected call.
Reduced new figure's eye-only atlas from2048 to1024; full original GLB and Blender
file already durably saved, unchanged. Existing model/download URLs retained.
Web optimized output: /workspace/scratch/116f83481a3c/cardi-reference-web.
Saved original deliverables, all version0, metadata confirmed:
- cardi-studium.glb: libfile_d70f7254d7208191b18a81e27e94198b
- cardi-studium.blend: libfile_fd5ba7ad8d248191ae09352a42c37f73
- cardi-studium-twarz.png: libfile_69875a96959c8191aa22b68b743ccb75
- cardi-studium-sylwetka.png: libfile_d42ee034dac08191be9104620d5e0c5f

---

# Cardi B reference study — visual review and publication

User rejected generic v13 and does not want another Oracle package to view it.
Authored a dedicated reference study: continuous full-body female anatomy, lower-face
sculpt, almond eyelids, projected brows/lashes, pigmented lips, continuous black bob,
scoop-neck sleeveless mint top, fitted jeans and detailed shoes. Similarity is still
approximate; this is NOT a photo reconstruction or a universal celebrity generator.
New example button "Cardi B · studium" and ?example=cardi-study direct link.
No substitution for the user's prompt: example loading is explicit. Existing Oracle
runtime, logos, former examples and access remain preserved.
Source portable under scripts/reference-portrait, including CC0 data/provenance.
Full output at /workspace/scratch/116f83481a3c/cardi-reference-final.
Real GLB export/reimport followed by portrait/fullbody renders; source geometry seams
at neck removed by using one anatomical skin; covered torso retained under garments.
Final material batching reduces192 meshes to7 for mobile. No paid service activated.
Five existing focused UI/export tests passed. Production build passed.
Final GLB: 9,978,280 bytes,111,406vertices,221,496triangles,7materials/meshes,5packedimages.
Final reimported GLB portrait/fullbody visually reviewed. Similarity remains approximate.
Deliverables staged at /workspace/scratch/116f83481a3c/cardi-deliverables.
Private publication and durable deliverable saves pending.
Source checkpoint73bc5ee saved before visual iteration. Final source saving now.

---

# Cardi B reference sculpt — in progress, not published

User rejected the generic v13 and does not want to install it. Do not call the
current generic female a Cardi B likeness. Existing live Site20 preserved.
New authored real Blender prototype under scripts/reference-portrait; face morph,
continuous bob, anatomical sleeveless clothed body. Portrait visual review pending.
Source has scratch absolute paths to be made portable before final delivery.
No Oracle install, no paid reconstruction service, no claim of photorealism.
Current working Blender: /workspace/scratch/116f83481a3c/blender-shapes-verify/bin/python.

---

# v13 silhouette correction — published; portrait reconstruction still unfinished

Latest screenshot has no upgrade banner: do not keep claiming v12 was uninstalled.
Actual source issue: head/forearms are anatomical bases, but clothing torso is a
front/back symmetric loft. Female preset forced slim; no bust or seat geometry.
Implemented bounded continuous clothed silhouette morph, natural/curvy shape and
fitted/regular/oversized fit, after garment union, before folds and projected details.
Shared hips/seat applied to both garments; full-body size and material budgets unchanged.
Single-subject prompt correction prevents a known adult female Cardi B request from
selecting a masculine presentation. This does NOT recreate Cardi B's face.
Generic base heads cannot preserve named identity; reference reconstruction remains
unimplemented and cannot be claimed solved. Supplied photos were inspected as references,
but are not passed to the live generator. No paid service was activated.
50 Python tests and 40 focused API/UI tests passed. Production build/typecheck passed.
Real Blender 4.3.0 export/reimport and front/back review passed after reducing excessive
hem inflation in the first draft. Final: 12,343,836 bytes, 141,948 vertices, 280,609
triangles, 8 objects, 5 packed images. Blender-only stage 6.97s, not live Oracle latency.
All 21 update entries equal source and ZIP CRC passes. Minimum compatible worker remains7.
Canonical model and reviews: /workspace/scratch/116f83481a3c/woman-v13-final/
Deliverables: /workspace/scratch/116f83481a3c/woman-v13-deliverables/
Initial source checkpoint 909bfa8 pushed before runtime verification. Final source,
durable deliverables and private publication being saved now. No Oracle install performed.
Final application source pushed: 6ee36eb58511ce8b37d0cbf9bb39058bd96b919d
Site version 20 saved:
appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_62706183f9b88191b4f3adf387b8323c
Deployment succeeded: appgdep_6a9fd23d1e5881919a0c103a78dbbe0f
Published at 2026-09-08T09:17:00.430619+00:00, environment revision2 retained.
Owner-private: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
All four deliverables durably saved, version0, metadata applied:
- kobieta-sylwetka-v13.glb: libfile_cd202dd5fc688191b6055d607348dc3b
- kobieta-sylwetka-v13.png: libfile_86cb979a5ca08191ae8cf1d870c3b213
- kobieta-sylwetka-v13-tyl.png: libfile_2c574915aa008191b39df2fd23e064ce
- froge-oracle-figures-v13.zip: libfile_c8cf8538cbb88191b548744e71b24ddf
Existing rendering examples and logos preserved; Site Git canonical, GitHub not updated.
The blender43-verify venv's bpy import crashed (SIGBUS); same-version working
blender-shapes-verify venv used successfully. No user VM problem inferred from this.

---

# Figure quality v12 — release checkpoint

User's screenshot confirms generation works again (27.2s), but the Oracle upgrade
banner proves the VM still runs a version older than11. This session cannot SSH
to that VM. Publishing a Site or adding an example does not update its worker.

Changes: feminine hair defaults/prompt; explicit no unsolicited headwear/necklace;
streetwear no longer creates a hood; narrower shoulder frame also moves sleeves
and hands; reduced oversized shirt folds; swept fine locks and upright microphone
with finger-specific curl. New authored singer fixture exercises actual Blender.

Final GLB exported and reimported in Blender 4.3.0, then visually reviewed.
Grip points upward; strands cover the front scalp. Still stylized, not photorealistic.
12363660 bytes, 143340 vertices, 283400 triangles, 8 objects and 5 packed images.
48 Python tests and 62 focused API/UI/auth/commerce tests pass.
Canonical outputs: /workspace/scratch/116f83481a3c/singer-v12-final/
Deliverables saved: /workspace/scratch/116f83481a3c/singer-v12-deliverables/
Four durable saves confirmed, all version 0:
- wokalistka-v12.glb: libfile_25803045e1588191bdc34dbdf9d88026
- wokalistka-v12.png: libfile_c413974cc0e481918ba6fcc087a12807
- wokalistka-v12-twarz.png: libfile_d1bab25eeea0819188266777477b6562
- froge-oracle-figures-v12.zip: libfile_59ece15a38b8819198baf982f3c8bce8

Production build/typecheck passed. Update ZIP passes CRC and all 21 packaged
files match source byte for byte. Compatible minimum worker remains v7;
v12 is recommended, without blocking generation on supported older workers.
Final application source pushed: a4248c5429dba58110d3c12a020f8f784bf5a284
Site version 19 saved:
appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_03061d9b45688191b32c9bfe196ada22
Deployment: appgdep_6a9fc617b88081919104c69cf6a324e4
Published successfully at 2026-09-08T08:25:08.271387+00:00, environment revision 2.
Owner-private access, existing credentials, models and commerce logos preserved.
Live: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
No Oracle installation or live AI-to-Oracle v12 generation was performed.
New singer example uses an authored scene executed in real Blender. Local
Blender stage took 6.67s; this is not a live service latency measurement.
Site Git is canonical; the GitHub mirror was not synchronized this session.

---

# Generation recovery published — 2026-09-08

- Production logs confirm HTTP 401 for Blender connection/jobs before any Oracle call.
  Dispatcher forwards authenticated email/full name but stable user ID is absent.
- Native read-only D1 inspection confirms one existing connection, 14 saved jobs,
  and no new jobs after 2026-09-07. Existing credentials/models were not deleted.
- Recovery adds a server-only, explicit verified-email → existing owner alias when
  stable ID is absent. Real stable ID takes precedence; unmapped sessions deny.
  Mapping values are runtime secrets; no emails/owner identifiers are stored here.
- Shared compatibility now accepts validated-scene workers v7–v11. v11 remains
  recommended for new figure appearance. Legacy v5/v6 remain blocked.
- Unknown/unreachable health is not presented as an outdated worker.
- Audit: 21 packaged files byte-identical to source; 47 Python tests pass.
- 52 focused API/UI/identity tests pass, including all v7–v11 lifecycles, exact
  prompt submission, GLB retrieval, email-only session and cross-owner rejection.
- Production build and 10 additional commerce tests pass (62 focused tests total).
- Source pushed: 3dcc14f19df47ce9f8659cf36055aefa550ff7fa
- Published version 18 succeeded at 2026-09-08T08:01:43.711426+00:00.
- Saved version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_3882e4739b248191a05fb3c8a19d1b76
- Deployment: appgdep_6a9fc0b9b5c08191a9b8f84b18bb0d62
- Runtime environment revision 2 contains the verified owner alias as a secret;
  existing encryption key and owner-only access were preserved.
- No database writes or credential migrations were performed during recovery.
- Oracle installed version/live end-to-end generation not yet verified.

---

# Active v11 handoff — 2026-09-08

## Current result
- New male LA and adult female LA examples built in real Blender, exported and reimported.
- Individual tapered eyebrow hairs and male buzz stubble; female crown-fitted long locks.
- Untucked shirt, draped folds and custom slanted LA lettering follow garment geometry.
- A radial clearance pass prevents trousers breaking through the shirt hem.
- Both examples are stylized; the female hair still needs finer detail for realism.
- No claim of commercial print readiness or exact celebrity likeness.
- Packaged Oracle worker is version 11; installation is needed for the new figure features.
  Compatible older workers can generate with their own existing geometry.
- Studio source now includes male and female example buttons and gates incompatible workers.
- Published version 17 succeeded on 2026-09-08 at 07:00:47 UTC.
- Application source: 9021a55c2acc42789027dd1250412f12c17429da
- Saved version: appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_ac4ec07b746c8191b8c0f47846bf561f
- Deployment: appgdep_6a9fb25b93b88191a77ec041cf61c0a6
- Live: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
- Owner-private audience and environment revision 1 preserved.

## Checks
47 Python tests and 32 targeted Blender API/UI tests passed; typecheck and production build passed.
Both GLBs pass real Blender export/reimport, finite geometry, height and packed-image checks.
Male: 10959516 bytes, 136208 vertices, 253886 triangles; female: 12266552 bytes,
140187 vertices, 277251 triangles. Both contain 8 objects and 5 packed images.
Full unrelated test suite exposed an existing stale commerce-ui.test.tsx assertion:
expects two “Niepołączony” labels and a server panel; current CommerceHub has one label
and a link to Studio. This was not changed or claimed passing.

## Final files
Canonical renders and Blender sources: /workspace/scratch/116f83481a3c/characters-v11-release/
Deliverables: /workspace/scratch/116f83481a3c/characters-v11-deliverables/
Superseded review/final folders have known defects; do not deliver those.
Seven new files have confirmed durable saves, version 0, with local metadata:
- raper-la-v11.glb: libfile_d5b869a698008191a3d445ee80160981
- raper-la-v11.png: libfile_090f9efea8f08191a7b5396a2231c9e4
- raper-la-v11-twarz.png: libfile_44350bca27ac8191b959c238b8972cdc
- kobieta-la-v11.glb: libfile_f9d0523f5cf88191aae4410e4138e8c8
- kobieta-la-v11.png: libfile_fccd043a88508191a0c595af6c1f0728
- kobieta-la-v11-twarz.png: libfile_7fdc022a8fd0819195060942bcfa8157
- froge-oracle-style-v11.zip: libfile_5800d53428208191a19b99cb90d22022

## Recovery
Source checkpoint already pushed to Site Git before renders; final source is being saved
with this handoff. Deployment success is confirmed above.
GitHub mirror remains at f99fd84ef49c34632135d64bbae66a26e1eec53b until separately synchronized;
do not claim GitHub is current. Site Git is the canonical saved v11 source.
Next user handoff: link the two full-body previews, two GLBs, update ZIP and confirmed Site.
Existing v10 baseline/recovery references follow for history.

---

# Work checkpoint — 2026-09-08

## User request and recovery state
Sebastian reported another ChatGPT network error and requested earlier saves.
The screenshot shows the ChatGPT conversation reporting a network error after
22 min 27 s. It does not establish a Froge application failure, a root cause,
or a fixed 12.5/125-minute timeout.

The v10 implementation and deliverables already exist. Do not restart this work.
The project instructions now request checkpoints after about 5 minutes and
reviewable handoffs within 8–10 minutes. This is a work cadence, not a background
autosave guarantee.

## Verified application baseline
- Site: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
- Site ID: `appgprj_6a9c7f472a208191aaae6df3fe3423bf`
- Latest published version: **16**, deployment status **succeeded**, verified on 2026-09-08.
- Saved version: `appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_22ab0727fb088191a0aee23df5e3f5d5`
- Deployment: `appgdep_6a9f332cb8848191ae136744d2a3d3ee`
- Application source commit in Site Git: `01b36705f9c904f183037045be10cb2083f655e5`
- Equivalent application commit in `teslaeco/Froge-MPC-2-test`: `248eb4d42aacf5654dd4506c7a0bd4dc4d83f439`
- Application tree: `3b22066b3102ecd1b671e2b2819b96c58ed33ce2`
- Access remains private to the owner. Do not widen it.

This checkpoint and AGENTS.md are documentation additions after that application
baseline. They do not require a new application build or deployment. Use Git
history to identify the latest documentation revision; the published version
above refers to the application baseline.

## Completed v10 changes
- Enlarged official Shopify logo; Amazon, eBay and AliExpress remain labelled as planned integrations.
- Improved neck, shoulder silhouette, collar and sleeve transitions, wrists and hands.
- Short/buzz/bald hair options; buzz hair is in the scalp atlas rather than a helmet shell.
- T-shirt, sweatshirt and hoodie options; the supplied example has no chain and no hood.
- Packed cotton/denim materials and normal maps.
- The Studio example button “Przykład · raper” loads `/models/rapper-v10.glb`.
- The example is a stylized rapper inspired by early-2000s Eminem clothing, with a generic face.
- Neither exact likeness nor commercial print readiness has been established.

## Validation already completed
- 47 Python tests and 32 Vitest tests passed (79 total).
- Actual Blender 4.3.0 generation, GLB export/reimport, texture and budget checks completed.
- Final GLB: 10,343,368 bytes; 119,032 vertices; 236,936 triangles; 7 objects; 5 images.
- Local Blender stage: 7.42 seconds, excluding AI, network and Oracle time.
- Final visual review confirmed prior sleeve/skin, collar/neck and wrist defects were corrected.
- On recovery, local output files were verified present and the ZIP passed ZipFile.testzip().
- The package contains CONNECTOR_VERSION = 10.
- No application test rerun is needed for the documentation-only recovery update.

## Final deliverables and durable recovery references
Local deliverable directory:
`/workspace/scratch/116f83481a3c/characters-v10-deliverables/`

All six files were saved and updated to Library version 1 after final correction.
Do not replace them with earlier review/release/approved variants.

| Filename | Bytes | Saved Library file ID |
| --- | ---: | --- |
| raper-v10.glb | 10343368 | libfile_d0056cb0c680819192ff7c1895671c67 |
| raper-v10-sylwetka.png | 952577 | libfile_7235417ff754819190799fa99d744665 |
| raper-v10-twarz.png | 1006736 | libfile_444fc2cd2a388191a6c88c97afaa6a0c |
| raper-v10-ubranie.png | 1064946 | libfile_3678d242a9f88191bd9d55af3a8b8419 |
| raper-v10-buty.png | 1097540 | libfile_09f329bb98588191aa73255625e6af30 |
| froge-oracle-portrait-v10.zip | 14952793 | libfile_1752a36e557081919e5182adc8dda5e7 |

Canonical Blender working output:
`/workspace/scratch/116f83481a3c/characters-v10-verified/rapper-eminem-style/`
Files include model.glb, model.blend, review.png, face-review.png,
clothes-review.png, shoes-review.png, back-review.png and verification.json.

## Remaining user action and next handoff
- The website update is published and the saved example can be loaded immediately.
- **New Oracle generations still require installation of the v10 ZIP.**
- The user's SSH key is in their Oracle Cloud Shell; no Oracle installation was performed here.
- Upload the v10 package through Oracle Menu → Upload, then use the existing
  “Jak zainstalować aktualizację?” instructions in the Studio.
- Preserve the existing connection and OpenAI key.
- Re-deliver the Site, model, preview and update ZIP links now. No new generation is pending.
- Later quality work should start with the user's feedback on this verified v10 output.
