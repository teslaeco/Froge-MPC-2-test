# Reconstruction, evidence and production workflow

This is an engineering specification. A stage is complete only when its stated output exists and is linked to the artifact manifest. Proposed checks below are not reported as executed tests.

## 1. Case ingestion and registration

Store the authorized reference, immutable source model, requested changes and visibility mask. Record image-left/image-right separately from anatomical left/right. Keep creative deviations, such as grey hair on one side, in a separate field. Registration uses landmarks visible in both image and model; no numeric accuracy score is emitted for unavailable views or uncertain landmarks.

Case memory contains technical decisions and feedback relevant to generating the asset. It does not copy unrelated personal conversation into a public repository. The known preference history is explicit: R15 was rejected, R14 facial proportions were preferred, E15 restored that basis, and E16 only repaired part of the geometry/materials.

## 2. Anatomical structure before surface appearance

Review connected support structures: cranium, orbital rim, zygomatic region, maxilla, mandible, dental arch and neck support. Adult skull anatomy provides a structural reference for the facial skeleton, tooth sockets and the relationship between orbit and cheek. It does not supply the identity of the reference face. [OpenStax: The Skull](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull)

For this fantasy split character, retain the chosen visual motif. Age is an explicit character parameter or a supported reference observation; grey hair alone must not automatically rescale the skull or substitute an elderly face. For future age-dependent assets, use a separately reviewed age-aware dataset, documented sample distribution and held-out evaluation. Do not claim a universal anatomical age model from this single adult example.

Neutral-material review is a required checkpoint before pore detail or high-resolution colour. Compare silhouette and key surface boundaries from the source camera and both profiles. A texture-painted eyelid, jaw edge or nostril fails this checkpoint if the required structure is absent in the mesh.

## 3. Hair and microstructure

Hair development has three levels: overall hairstyle silhouette, supporting clumps/roots, and fine strands. Attach guide roots to a named scalp surface and maintain root density where the camera sees the hairline. Use consistent strand direction and taper, then controlled local variation. The living/grey split is evaluated as two material regions with coherent shared hairstyle.

Blender's Principled Hair shader exposes colour/roughness variation and hair-specific scattering. Those facilities help develop a native render material; final delivery still requires checking how the intended FBX/GLB consumer represents the hair. [Blender: Principled Hair BSDF](https://docs.blender.org/manual/id/5.2/render/shader_nodes/shader/hair_principled.html)

Pores and weave belong to a measured surface scale. Native displacement changes the surface, while normal/bump detail changes its shaded appearance; use the representation that matches the shot and delivery constraints. High-resolution surface detail can be baked to an export-oriented asset and checked against the source. [Blender: Displacement](https://docs.blender.org/manual/en/latest/render/materials/components/displacement.html), [Blender: Render Baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)

## 4. Agent responsibilities and evidence

| Role | Input | Required output | Failure blocks |
|---|---|---|---|
| Reference analyst | User reference, requested deviations, prior accepted revision | Landmarks, visibility masks, feature priorities | Invented hidden detail presented as observed |
| Geometry worker | Registered reference, baseline geometry | Local edit script and candidate mesh | Broken silhouette, open unintended seams, eye/teeth displacement |
| Material worker | Accepted geometry, source colour | Named maps and material assignments | Lighting painted into colour, unresolved seams, missing export maps |
| Independent reviewer | Re-imported candidate, baseline, reference | Labelled front/side/back and detail evidence | Empty render, wrong artifact, critical visible regression |
| Release worker | Reviewed artifacts and reports | Manifest, PR and public comparison | Unsupported benchmark, unverified completion claim |

Agent agreement alone is not the acceptance criterion. The artifact, visible evidence and explicit user acceptance remain decisive. Record which worker produced a change and which reviewer inspected it; do not let an author silently mark its own unrendered work as visually accepted.

## 5. From examples to actual learning

OpenAI's published optimization guidance separates evaluations, contextual instructions and fine-tuning. We apply the evaluation/context stages here: curate cases, retrieve relevant failure records, execute a bounded correction and compare against a preserved baseline. This does not alter Astra's pretrained weights. [OpenAI: Model optimization](https://developers.openai.com/api/docs/guides/model-optimization)

Inspection of the private chess-board work recovered exact layout/colour contracts, authored correction examples and a newer visual-QA training implementation. The newer branch contains ResNet-based defect classification and quality regression code. Its recorded CPU smoke exercises curriculum games/rollouts; the reviewed tree did not contain a trained weight file or a completed L4 visual-training summary. Owner-local VM artifacts may still exist, so this finding is not proof that no training ever occurred. The QA classifier is not an image-to-3D model and is not Astra's weights. Detailed private source links belong in the internal evidence dossier, not in a public customer page.

Transfer the verified method: explicit cell counts, parity-based colour assignments, coordinate invariants, texture-region checks and repeatable visual tests, then measure it on character assets separately. The existing board convention alternates colour with `((X + Y + Z) & 1) == 0`; do not silently change it to XY-only parity. For this asymmetric character, disable unlabelled horizontal-flip augmentation. Avoid colour jitter when judging exact colour compliance. A board result is not evidence that a face model learned a skeleton.

Before any new dataset is used, require provenance, compatible permission for the intended operation, useful labels, and a specific defect it can address. Deduplicate by object/person/source grouping before dividing development and held-out cases; adjacent renders of one object must not leak across the split. Keep difficult failures instead of publishing only successful outputs. No claim of global dataset training is made without a real dataset manifest, run logs, weight/checkpoint identifiers and held-out improvement.

An anatomical publication consulted for structural understanding is not automatically licensed training data. The OpenStax page above is a cited reading reference only; no text or diagram from it is admitted into the commercial generative training corpus. Review the current permission terms of any proposed data source for the particular use before ingestion.

Run ablations that answer a concrete question: baseline; reference/landmark instruction; anatomy constraints; material constraints; combined pipeline. Report each error category separately. Do not use one aggregate score to hide wrong field colours or a broken eye. Budget each experiment; stop collecting unrelated data when no named failure is being addressed.

## 6. Two delivery paths

For games, create an editable high-detail source plus a separately tested runtime asset: suitable topology and LODs, material maps, rig/skin tests where animation is promised, and scene-specific performance measurements. A static FBX import is not an animation test.

For fabrication, derive a manufacturing asset after dimensions and process are chosen. Require a process-specific wall/clearance review, units, connected volumes and support assessment. Quoted mass is based on the chosen manufacturing plan, not just the closed mesh's solid volume. Food-contact tableware also needs suitable material/process validation before it is sold for that use; a decorative concept is not automatically suitable for serving food.

## 7. Quote and store contract

The public page presents a preview, prompt/reference input and product categories. The user chooses an approved candidate before a quote. Quote records include dimensions, material, colours, manufacturing process, finish, quantity and delivery destination. Supplier rates remain unset until provided; do not invent a live price list.

Illustrative quote structure: material usage × supplier material rate + process time/setup + colour changes + finishing + packaging/shipping + applicable tax. Every term records its source and currency. This is a proposed pricing model, not a price quotation. Supplier acceptance, payment and production each have distinct states; the UI must not display an order as accepted because a prompt was saved.

## 8. Release evidence

Every published candidate includes source/output hashes; generator/Blender version; actual triangle count; render settings; real export verification; visual review status; reference/deviation notes; known limitations; and comparison source labels. Public comparisons describe this test case. Claims of a faster, cheaper, more accurate or scientifically validated system require a separately designed, reproducible experiment.
