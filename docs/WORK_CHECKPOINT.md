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

