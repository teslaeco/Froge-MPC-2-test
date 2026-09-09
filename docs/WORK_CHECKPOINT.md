# Work checkpoint — 2026-09-09

## Verified application baseline
- Site: https://froge-mpc-2-studio.terraformingplanet.chatgpt.site
- Site ID: `appgprj_6a9c7f472a208191aaae6df3fe3423bf`
- Latest published site version remains **16**, deployment status **succeeded**, verified on 2026-09-08.
- Saved version: `appgprj_6a9c7f472a208191aaae6df3fe3423bf~appgver_22ab0727fb088191a0aee23df5e3f5d5`
- Deployment: `appgdep_6a9f332cb8848191ae136744d2a3d3ee`
- Application source commit in Site Git: `01b36705f9c904f183037045be10cb2083f655e5`
- Equivalent application commit in `teslaeco/Froge-MPC-2-test`: `248eb4d42aacf5654dd4506c7a0bd4dc4d83f439`
- Access remains private to the owner. Do not widen it.

## Previously verified v10 baseline
- Improved neck, shoulders, collar/sleeve transitions, wrists and hands.
- Short/buzz/bald hair options, T-shirt/sweatshirt/hoodie and packed cotton/denim materials.
- Studio example `rapper-v10.glb` remains the previously verified saved example.
- Previous verification: 47 Python + 32 Vitest tests passed; Blender 4.3.0 generation and GLB reimport were completed for that v10 deliverable.
- v10 model: 10,343,368 bytes; 119,032 vertices; 236,936 triangles; 7 objects; 5 images.
- Previous local package `froge-oracle-portrait-v10.zip` passed `ZipFile.testzip()`.

## v17 task — 2026-09-09
Sebastian supplied a failed reference-driven generation. The UI reported:
`Skrypt AI został ucięty. Użyj krótszych funkcji i pętli; zwróć kompletny model.`
Source inspection traced that exact message to OpenAI Responses event `response.incomplete`
in `oracle_connector/ai_stream.py`. The OpenAI request in `openai_provider.py` had
`max_output_tokens = 4500` while the trusted scene contract allows plans up to 60 KB.

The same reference exposed a second quality requirement: preserve a fitted original dress
instead of replacing it with thick generic armor. Repeated fan mechanisms should be compact
reusable geometry instead of huge repeated mesh lists.

### v17 source changes prepared
Branch: `codex/v17-fitted-couture`
PR: `#1 Oracle v17: prevent truncated Astra plans and preserve fitted reference outfits`

Changes:
- `openai_provider.py`: `MAX_OUTPUT_TOKENS = 9000`; Responses API still uses strict schema,
  fixed official origin, low reasoning, no prompt/key leakage and the existing 60 KB parser cap.
- `runtime/scene_contract.py`: reference-quality planning rules now preserve visible outfit
  identity, keep fitted dress geometry close to the anatomical silhouette, reconstruct cropped
  lower gowns coherently, keep crystalline decorations thin, and prefer compact procedural
  geometry / `copies` for repeated fan turbines.
- `server.py`: source package reports `CONNECTOR_VERSION = 17`.
- `apply_update.py`: full-package updater expects and verifies connector version 17.
- `test_openai.py`: expected Astra budget updated to 9000 and health test checks version 17.
- `apply_v17_hotfix.py`: rollback-safe small updater for an already installed worker v10-v16;
  it patches only server/provider/planner guidance, keeps state/key/pairing/models, refuses to
  run during an active job, compiles patched Python, creates backups, restarts the service and
  rolls back unless local `/v1/health` confirms version 17.

### Validation actually completed for v17
- GitHub PR diff inspected: 6 source/test/update files plus this checkpoint.
- PR mergeability confirmed `true` after GitHub recalculation.
- No GitHub Actions workflow runs exist for the branch, so the repository test suite has **not**
  been executed in this session. Do not claim Python/Vitest/Blender generation passed for v17.
- A standalone `froge-oracle-v17-hotfix.zip` was created in the active runtime; its updater
  source compiled successfully before packaging and `ZipFile.testzip()` returned no error.
- No paid OpenAI generation was run for this checkpoint.

### Deployment / Oracle status
- Source preparation is not Oracle installation.
- **Oracle v17 is not yet verified as installed in this session.** There is no Oracle SSH/Cloud
  Shell execution connector available here and the endpoint/token are intentionally not stored
  in the repository.
- Installation is complete only after the updater prints `FROGE_V17_OK` and local health returns
  `connectorVersion: 17`.
- Published Site version remains 16; this v17 work is currently Oracle-worker/source work, not a
  new Sites deployment.

## Next handoff
1. Install `froge-oracle-v17-hotfix.zip` on the Oracle VM as `opc` when no generation is active.
2. Verify `FROGE_V17_OK` / `/v1/health` version 17.
3. Generate a fresh model from the emerald-dress/fan reference and inspect full body, fitted dress,
   fan thickness, repeated devices, hands/fingers, eyes, materials and GLB output.
4. Only after that visual/model QA call v17 generation verified.

## v18 reference reconstruction implementation — 2026-09-09
Branch: `codex/v18-astra-reference-quality`.

Implemented production source (not a marker-only change):
- The validated data-only scene schema now requires `characterStandard: 18` and provides a bounded `reference_character` operation with observed/reconstructed provenance, fitted-garment offset/thickness limits, a floor gown and updo controls.
- Trusted Blender runtime code creates the complete existing anatomical person underneath body-following couture, a floor-length continuation, attached thin panels, collar/belt, multi-part updo and ornament. Existing five-finger anatomy, eyes, feet and skin atlas path remain the base.
- Compact `rotor` and linked `radial_copies` operations provide reusable fan machinery without large generated vertex arrays.
- A deterministic emerald couture/fan fixture and GLB re-import/geometry QA checks were added; its review path renders front, three-quarter, side and back from the re-imported GLB.
- Oracle health and web connection metadata now expose connector version 18 and character standard 18 together. The rollback-safe full updater includes the couture runtime.

Checks actually run in this environment:
- `python3 -m py_compile oracle_connector/*.py oracle_connector/runtime/*.py` passed.
- `(cd oracle_connector && python3 -m unittest discover)` passed: 49 tests.
- `npm run typecheck` passed.
- `git diff --check` passed.
- `npm test -- --run` could not execute under the installed Node runtime: `node:sqlite` is unavailable and jsdom/undici workers fail on missing `webidl.util.markAsUncloneable`. This is an environment/runtime incompatibility, not a recorded passing test.

Still unverified and deliberately not claimed:
- Neither `blender` nor `podman` is installed in this environment. The couture fixture was therefore not generated here; GLB bytes, actual vertices/triangles/objects, Blender runtime, export/re-import result and four review renders remain for an Oracle/Blender 4.3 run using `verify_scene_runtime.py --scene couture-fan-v18.scene.json --output <directory>`.
- No image-comparison metric and no visual identity/similarity percentage was run. Unseen back, legs, feet and floor hem are explicitly reconstruction in fixture metadata.
- Source preparation is not Oracle installation or a Sites deployment. Published Site version remains 16 until separately deployed, and Oracle v18 is confirmed only after its local health endpoint returns both `connectorVersion: 18` and `characterStandard: 18`.
