# ChessArena → FORGE E17: source evidence and transfer decisions

Reviewed on 2026-09-12. This dossier records retrieved source and measured implementation evidence; it does not claim a new neural training run.

## What was actually recovered

The private repository is **teslaeco/Chess-Arena-512-AI**, distinct from the public Cube Chess foundation. Main was inspected at `f512f85b01504fca3b3d77efe0cb73a8e7c40a98`. A newer, unmerged training branch exists: `sprint/full-product-training-v12-2026-08-27`, pinned commit `e8240922a43d852c878a5e8613b5750713de17d8`, [draft PR #115](https://github.com/teslaeco/Chess-Arena-512-AI/pull/115).

| Evidence | Verified contents | What it does not establish |
| --- | --- | --- |
| [ACTIVE_DATASET.json](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Dataset/ACTIVE_DATASET.json) | Full training state is `blocked_pending_real_unreal_v5_pilot_evidence`; 90-minute core plus 30-minute story allocation; exact canonical geometry. | The written 120 minutes are not completed GPU minutes. |
| [Visual trainer](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Tools/VisualTraining/train_visual_qa.py) | ResNet18 without pretrained weights; multi-label defect head plus quality regression; AdamW, mixed precision, validation F1/MAE; writes `last.pt`, `best.pt`, summary when executed. | It is a quality-assurance image classifier, not an image-to-3D generator and not Astra weights. |
| [Sprint trainer](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Tools/VisualTraining/train_visual_qa_sprint_v10.py) and [V11 configuration](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Tools/VisualTraining/visual_training_v11.json) | ResNet50, 448-pixel input, no downloaded pretrained weights, bounded GPU memory/batches, resume compatible owner-local checkpoint. | A resume path is not proof a checkpoint exists or improved held-out accuracy. |
| [V11 scorer](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Tools/VisualTraining/score_visual_qa_v11.py) | Loads checkpoint, scores val/test samples, exports predicted defects and rights-approved asset rankings. | `status: PASS` means scorer execution completed; it does not certify generalization, image likeness or production approval. |
| [PR115 proof](https://github.com/teslaeco/Chess-Arena-512-AI/pull/115) | Records CPU smoke of 300 curriculum games and 3 legal rollouts, CI and private dataset upload verification. | Not a full L4 visual training result. Full 100k curriculum/3k rollout targets must not be counted as completed by this smoke. |
| Recursive tree at the pinned V12 commit | Trainers, configs, schemas, plans and data-validation code are present. No .pt/.onnx files or actual TRAINING_SUMMARY.json were found in that tree. | Owner-local Saved/SourceAssets files may exist on the earlier VM; they were not available for inspection here. Do not claim they never existed. |

The main branch lacks the visual trainer path, while the newer V12 branch contains it. This branch distinction matters; a default-branch-only search would miss useful implementation.

## The reusable lesson from incorrect chessboards

The useful transfer is **explicit constraints plus inspected before/after evidence**, not inheriting chess-specific neural labels as anatomy knowledge.

The [actual visualizer](https://github.com/teslaeco/Chess-Arena-512-AI/blob/f512f85b01504fca3b3d77efe0cb73a8e7c40a98/Source/ChessArena512AI/Private/Presentation/ChessBoardVisualizer512.cpp) assigns cell material class using `((X + Y + Z) & 1) == 0`. The [layout contract](https://github.com/teslaeco/Chess-Arena-512-AI/blob/f512f85b01504fca3b3d77efe0cb73a8e7c40a98/Docs/BOARD_VISUALIZER_512_CONTRACT.md) binds indices to `X + 8 * (Y + 8 * Z)`, 64 cells per level, 512 total, unique centers and a common XY footprint. This existing color convention alternates between levels as well as within them; do not silently replace it with an XY-only convention.

The [seed correction example](https://github.com/teslaeco/Chess-Arena-512-AI/blob/f512f85b01504fca3b3d77efe0cb73a8e7c40a98/Dataset/06_PREMIUM_FULL_GAME_V3/training_examples.jsonl) explicitly rejects a generated 9×8 playable surface and rebuilds the exact 8×8 surface deterministically while retaining suitable decorative style. These are authored seed examples, not captured training pairs.

| Chess failure and check | Appropriate character counterpart |
| --- | --- |
| Wrong cell count / duplicate coordinates | Explicit inventory of reference-visible anatomical parts, side labels, required eyes and tooth groups; deliberate skeletal stylization remains declared. |
| Grid on decorative frame | Garment follows body; jewelry, fan, hair and clothing cannot replace the anatomical core or disguise missing surfaces. |
| Missing material / opaque fallback | Verify connected image nodes and exported UV set, material assignment, actual texture dimensions and portable import. |
| Piece floating / wrong scale | Measure contact/clearance at neck-head, eyelids-eye, tooth-gum, hair-scalp, cloth-body and hand-prop interfaces. |
| Incorrect square colors | Evaluate semantic material masks in albedo/diffuse views under controlled color management; compare side-specific palettes separately from lighting. |
| Camera hides defect | Require matched front, side, back and detail renders; neutral clay plus textured views. |
| One visual fix breaks another part | Local bounded edit, preserve baseline, render and KEEP/REVERT with change-specific evidence. |
| Same scene frames in train and validation | Split by underlying asset/identity/reference family; all camera views of an asset remain in one split. |

[Chess defect taxonomy](https://github.com/teslaeco/Chess-Arena-512-AI/blob/f512f85b01504fca3b3d77efe0cb73a8e7c40a98/Dataset/06_PREMIUM_FULL_GAME_V3/defect_taxonomy.json) makes zero structural P0 errors a prerequisite for aesthetic acceptance. [Pilot targets](https://github.com/teslaeco/Chess-Arena-512-AI/blob/f512f85b01504fca3b3d77efe0cb73a8e7c40a98/Dataset/07_REAL_UNREAL_DATA_V5/pilot_targets.json) demand actual captured examples and keep/revert outcomes, explicitly rejecting high GPU utilization or written target counts as evidence of useful training.

### Improvements needed before transplanting the old trainer

- Old training augmentation includes horizontal flip. For the living-left/skeletal-right brief this changes meaning unless side labels and landmarks are transformed. Disable it for this task.
- Old color jitter is inappropriate when judging exact color compliance. Separate geometry/lighting invariance training from calibrated albedo-color evaluation.
- Old rights configuration allows `QUARANTINE` in training. Do not inherit that blindly; uncertain rights must not become approved production training.
- Old classes are board/camera/environment defects. Train a separate labeled anatomy evaluator only with actual reviewed samples and a held-out identity split; do not relabel a board model as human-anatomy understanding.
- A finite mesh, complete UV map or successful reimport does not establish likeness. Keep structural and visual acceptance independent.
- Synthetic pores/gray hairs can improve appearance but are generated detail. They cannot be claimed as measured skin pores or actual aging evidence from a low-resolution reference.
- More triangles should implement visible silhouette, curved tooth crowns, eyelid rims, hair fibers and cloth structure; global subdivision alone does not improve correspondence.

## Durable record to reuse

[V12 asset/reference/texture schema](https://github.com/teslaeco/Chess-Arena-512-AI/blob/e8240922a43d852c878a5e8613b5750713de17d8/Dataset/16_FULL_PRODUCT_TRAINING_V12/asset_reference_texture.schema.json) already links model SHA → reference image SHA/purpose → UV/material slots → maps → runtime performance → human review. Reuse this idea in FORGE with character-specific metrics and explicit `observed`/`inferred` regions. Each pair should store source/candidate hashes, exact edit parameters, render camera and lighting, region label, measured checks and user verdict. Saving this corpus and retrieving it in future prompts is project memory; it is not fine-tuning Astra.

## Focused external resources

Only sources with direct relevance were checked; no broad global dataset scrape was started.

| Source | Decision | Reason and boundary |
| --- | --- | --- |
| [MakeHuman core assets](https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html) | Suitable base mesh/targets/skin source already used by FORGE. | Publisher explicitly licenses core meshes, targets and skins CC0 and permits reuse in another character generator. Community add-on packs can have different licenses. Base age/shape morphs are generative priors, not an anatomy accuracy guarantee. |
| [MakeHuman asset packs](https://static.makehumancommunity.org/assets/assetpacks.html) | Narrow candidate selection: CC0 skins, eyebrows/eyelashes, dress01; inspect before adding. | Hair01 is described as mostly low-poly/stylized, so it is not evidence of photoreal strand hair. Other hair/dress packs may be CC-BY. |
| [Poly Haven asset license](https://polyhaven.com/license) | Suitable individual PBR texture/HDRI candidates when needed. | The assets are CC0; website text/render examples and API access have separate terms. No wholesale site scraping or copying showcase images into training. |
| [OpenStax skull page](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull) | Excluded from the commercial generative training corpus. | Current page states NC-SA licensing and requires permission for LLM/generative-AI training. It was consulted to check suitability, not copied into a dataset. |

No new external training data or checkpoint has been silently installed. The most valuable immediately available examples are the user's actual exported models and their known failure/correction pairs.

## Queen Neptune / fan asset recovery

The current FORGE branch contains full builders and measured reference signatures, but no ready-made couture GLB in its tree:

- `oracle_connector/examples/couture-fan-v20.scene.json`
- `oracle_connector/verify_couture_runtime.py`
- `oracle_connector/runtime/couture.py`, `couture_geometry.py`, `portrait.py`, `portrait_hair*.py`
- `oracle_connector/runtime/assets/emerald-reference-landmarks.json` and `emerald-reference-signature.json`.

The 4K reproduction README requires original private `reference-0.jpg` plus matching `reference-photos.json` in the output folder. Without that reference, the fixture remains a generic study. Do not apply the old 478 landmarks to the new Julia poster; its composition is different.

Historical checkpoint records `FORGE-modelka-4K.glb`, 39,711,312 bytes, SHA256 `63d9924795454898e60f52fe8bce87c5906e60016f06211c19b0f2f88078b99b`, and an earlier `public/models/couture-v20-dopracowana.glb`. These are recovery clues, not proof those binaries are currently local.

## Honest Meshy comparison

The [earlier actual FBX/GLB audit](https://github.com/teslaeco/Froge-MPC-2-test/blob/codex/v27-mcp-startup-audit/docs/reviews/meshy-reference/README.md) contains reusable real front/three-quarter/back clay renders and detailed source hashes. Meshy bust: 3,079,530 triangles; FORGE full figure: 592,396 triangles. Their coverage differs, so counts do not rank likeness.

That audit judged Meshy stronger in cheek/lip shape, ear hair, collar, grip and diagonal folds. The user's observation that some FORGE fan mechanisms were reconstructed better can be reported as a specific user observation, not as a measured general victory. For the split woman, available Meshy screenshots use different cameras/lighting and do not support fair numerical topology, speed or likeness metrics.

Meshy offers strong reconstruction in these supplied examples. Astra/Codex with Blender offers explicit editable geometry, correction code, repeatable validation and export control. Their combination is a useful engineering direction; current evidence does not establish a universal winner or production-ready anatomical reconstruction.

