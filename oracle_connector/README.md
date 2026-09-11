# Froge Oracle connector

This is the text/photos → selected AI → Blender worker for the Froge test studio.
Each completed scene keeps the editable BLEND master and exports GLB, FBX,
OBJ+MTL, STL (unitless format with numeric coordinates written in millimetres)
and the validated Froge scene JSON when the job originated from that schema.
FBX requests embedded textures and preserves an existing armature; it never invents a rig.
OBJ/MTL cannot preserve every PBR shader, and STL has neither textures nor an
automatic print-readiness guarantee.
Interchange export revision 2 materializes packed/generated PNG and JPEG images
under unique content-addressed names in `textures/`, then temporarily binds ordinary
file images for the native exporters. Original image nodes and master geometry are
restored. Deliver OBJ together with its MTL and the entire `textures/` directory.
A failed optional exporter is reported as `status: partial`; the completed GLB/BLEND
remain available. `formats` includes only nonempty files produced successfully.
An export report does not claim that a native reimport was performed for every job.

Run `python -m unittest test_scene_exports` for failure handling, and
`blender --background --python verify_scene_exports.py` for real FBX/OBJ/STL imports.
The native fixture checks two distinct packed images with empty paths, preserved
image bytes/material assignments, geometry, UVs, STL units and a relocated OBJ.
Complex shader graphs, vertex-color-driven skin and advanced PBR require inspection
in the target application; shipping their source images is not a shader bake.

It is separate from the desktop Blender add-on and the example dragon.

## Photo-guided generation (version 14)

Install the current `froge-oracle-update.zip` using the update instructions in Studio,
then select the already-configured OpenAI provider. Publishing the Site does not
install the worker on Oracle. The updater preserves pairing, the API key and history.
Text-only Qwen and workers older than v14 are explicitly blocked for photo jobs.

The browser accepts 1–4 JPG/PNG/WebP files, each up to 12 MiB, with view labels.
It normalizes them to JPEG, at most 1600 pixels on the long side and 768 KiB each,
stripping source metadata through canvas encoding. Selecting files alone does not
upload them or start an API request. After Generate, the authenticated Site saves
the normalized bytes in owner-scoped R2 objects and metadata/hashes in D1. Private
history thumbnails and retries remain available with the job, including after
disconnecting the worker. Migration 0002 adds a default-empty metadata column.

The worker validates and privately stores those same bytes, then sends them as
Responses `input_image` data URLs alongside the prompt and view labels. It never
fetches caller-supplied image URLs or silently routes photos to the local text model.
AI produces the existing bounded scene JSON; Blender builds its actual geometry.
This is approximate photo-guided construction, not photogrammetry, a textured scan
or verified facial likeness. Hidden surfaces are inferred and the supported scene
operations limit detail. Each generation uses the owner's selected OpenAI API account.

Focused tests cover authenticated image storage/replay, limits, capability gates,
UI selection and explicit submission, a real local HTTP/SQLite worker, and image
content through the real Responses transport to a local SSE fixture. They make no
paid API calls and do not establish the quality of a newly generated photo model.
Image-input format: [official OpenAI guide](https://developers.openai.com/api/docs/guides/images-vision).

## Checked scene plans (version 8)

New generation produces a compact JSON scene, not executable model-written Python.
`runtime/scene_contract.py` is the single schema shared by OpenAI Structured Outputs,
Ollama's structured output request, host validation, and Blender validation. The host
checks names, material references, finite bounds, face indices, degenerate faces, copy
references and aggregate geometry budgets. Blender executes only the fixed operations
in `runtime/build_scene.py`; it never evaluates expressions from the plan.

The operations cover custom meshes, curved tapered tubes, lathes, smooth lofts,
noncircular stepped extrusions, detailed generic adult figures, boxes, ellipsoids,
translated copies, a parameterized branching oak with lobed leaves, and a garland with
an exact bulb count. This is a procedural asset vocabulary, not unrestricted Blender
scripting. Other shapes can be composed from the general operations. Geometry quality
and whether those parts match a new prompt still depend on the selected AI model.
The prepared oak fixture is authored and tested; it is never substituted for a user's
AI job or reported as a successful OpenAI generation.

Version 5 incorrectly removed generated geometry helper definitions while retaining
callers that could expect `(vertices, faces)` instead of a Blender Object. Version 6
rejects that legacy mismatch before execution. It never silently replaces a geometry
function. Limited replay of a compatible material-only script remains available, but
an incompatible stored geometry script requires a fresh scene plan. Original job files
and failures are retained.

Install `froge-oracle-update.zip` for the latest worker and figure appearance. Existing
OpenAI credentials are preserved. Validated-scene workers v7–v13 can still generate text jobs
using their own bundled schema and geometry. The update is recommended, not a
protocol requirement; v5/v6 remain blocked because of their known script/profile failures.


Version 7 accepts valid closed, descending and stepped lathe cross-sections. Radius
zero closes an axis cap; negative radii, crossings and zero-area sections are rejected.
Points are never sorted or silently substituted. `extrusion` supports noncircular
ordered XY outlines and stepped levels with separate facade and terrace materials.
The `windows` pattern is a packed facade image. This fixes a class of profiles rejected
by the v6 monotonic-height check, not every possible invalid AI plan.

Version 8 replaces the formula-based face and fingers with a MakeHuman CC0 adult
anatomy base, preserved UV topology and 2048px skin atlas. Nose, lips, lids and ears
belong to the head surface; hands retain individual fingers and nail geometry.
Headwear follows the actual cranium. Skin/cloth avoid metallic shading, clothing
texture contrast is reduced, and shoe soles meet their uppers. The two adult morphs
and their blend support the existing presentation setting. Height is normalized to
the completed figure, including headwear. `runtime/assets/SOURCES.md` documents data
provenance and the bundled CC0 license; no MakeHuman executable code is shipped.

The wardrobe remains procedural. These are generic textured figurines, not
photorealistic scans, AAA game characters or identity-accurate reconstructions.
Visual review, manufacturing checks and a test print remain necessary before selling
a physical figure. Exported GLB preserves geometry, materials and embedded textures;
STL cannot retain texture detail. Existing saved models are not altered: generate
again to use the new anatomy. AI never receives file paths or executable data.

The updater checks the bundled asset hashes before stopping the worker, backs up
code and data together and restores both if startup fails. Pairing, stored OpenAI
credentials, job history, tunnel and downloaded models remain untouched.

Requirements: the existing Oracle Linux 9 ARM instance, user `opc`, the already-tested
`localhost/froge-blender:local` Podman image, and about 10 GB additional free disk space.
The installer uses official ARM64 Ollama and Cloudflare downloads. The selected local
Qwen2.5-Coder 7B model is about 4.7 GB; inference runs on CPU. It remains the default until
the owner explicitly connects OpenAI in the private studio settings.

## OpenAI Astra

Version 4 adds OpenAI Responses API (`gpt-6-astra`) for instruction generation. Blender
still runs on the existing Oracle VM. In **Ustawienia serwera → OpenAI · Astra**, enter
an OpenAI API key and click **Podłącz OpenAI**. The model access check makes a read-only
request; generation is billed to the owner's OpenAI API account. No credentials are
bundled, and a ChatGPT subscription does not configure an API key for this worker.

The key is sent through the existing authenticated, owner-scoped connection and stored
in `state/ai-provider.json` with mode 0600 inside the private state directory. It is not
returned to the browser, persisted in browser storage/D1, included in model input, passed
in process arguments, logged, or mounted in the Blender container. Requests use the fixed
official HTTPS API origin and never follow redirects. Switching AI requires no active job.

OpenAI uses low reasoning effort, a compact schema-constrained scene plan, streamed responses, and a
4500 output-token cap. At most two attempts share a 3-minute instruction deadline;
Blender is limited to 3 minutes per attempt. These are failure limits, not speed promises.
Provider errors are explicit and never silently fall back to local Qwen. Successful jobs
report measured worker time for AI and Blender; private job files retain timing and token
usage. These measurements exclude browser polling and the final transfer to the Site.
Real OpenAI latency and model quality must be measured with an authorized key after setup.

Before requesting any AI generation, the worker starts a no-op container with the same
CPU, memory, process and isolation limits. A failed container check stops the job before
an API request. The installer/updater also runs this check. If it detects missing CPU
controller delegation, it adds `Delegate=cpu memory pids` in a Froge-specific drop-in for
the current `user@UID.service` only, reloads systemd, and enables CPU accounting for that
unit to apply resource configuration. It checks the container again and stops installation
if it still fails. It never removes limits or restarts the user manager/tunnel. This setup
uses `sudo -n`; unit tests simulate systemd calls, so real delegation is verified on Oracle
by the installer's container check, not by the local tests.

## Initial installation

1. Download `froge-oracle-connector.zip` from the authenticated Froge studio.
2. Upload the ZIP to Oracle Cloud Shell (Menu → Upload).
3. Copy the ZIP to the existing VM, extract to `/home/opc/froge-connector`, and execute `install.sh`.
4. Paste the HTTPS address and pairing code printed by the installer into the Froge connection form.
5. Wait for local AI to finish downloading; the connection status shows actual download progress.
6. Enter any model description and click **Generuj model 3D**. The request creates a new job;
   there is no keyword-to-example fallback. The model appears only after valid GLB export.

Local Qwen uses the same JSON contract, a 3000 output-token cap and a shared 3-minute
AI deadline. It keeps the loaded model for five minutes to avoid loading weights for
every follow-up. A timeout ends the job without another AI attempt. Failed validation
can trigger one repair within the original deadline. Blender is capped at 3 minutes
per execution. These are failure limits, not guaranteed completion times. The streaming
transport supports progress and cancellation even before the first HTTP response headers.
Incomplete responses are rejected. No provider is silently substituted.

One active job is allowed. Textures are procedural packed 512px UV images. Emission is
exported as a PBR material; bloom and illumination of neighboring objects depend on the
viewer's rendering features. This is not a pretrained image-to-3D service.

The worker listens on loopback only. Cloudflare Quick Tunnel exposes its authenticated API over
HTTPS without adding inbound ports to the VM. Quick Tunnels are for testing, have no uptime SLA,
and their address can change after restart. A stable production service needs a managed tunnel.

The API requires a random bearer credential. A 128-bit pairing code expires after one hour;
first use binds it to the current Site user and shortens the remaining time to ten minutes
so that a lost pairing response can be retried. The Site stores the bearer credential encrypted
with AES-GCM under its production secret and does not return it to the browser.
Generate a fresh pairing code and read the current tunnel URL with:

```bash
python3 ~/froge-connector/server.py --pair-info
```

The validated JSON scene is built in a separate rootless Podman container. The container has no network, a read-only root filesystem, dropped capabilities,
no new privileges, a 4 GB RAM limit, 2 CPUs, and a 256-process limit. Only its own job directory
and the read-only renderer are mounted; SSH keys, API tokens and the worker database are excluded.
The Python filter remains defense in depth for legacy saved-script replay only.

Completed `.blend`, `.glb`, scene plans, legacy source and logs remain under `state/jobs/<id>/` on the VM.
The Site imports GLB into private R2 storage after successful generation and keeps owner-scoped
job metadata in D1. Restarted in-progress jobs report failure rather than silently duplicating work.
Limits are 12 MB per GLB and 300 retained jobs; archiving old VM jobs is a separate explicit action.

The Site requires a server-only `BLENDER_SETTINGS_KEY` runtime secret (32 random bytes as
64 lowercase hex characters). Preserve it across deployments. It is never included in this ZIP.
The local HTTP/SQLite, API and UI tests cover authorization, pairing, job identity, cancellation,
artifact transfer and explicit failures. OpenAI tests use a local SSE fixture to verify streaming,
credential handling, cancellation, incomplete responses, quota failures and provider routing.
These tests make no live OpenAI calls and do not validate AI output quality or execute Blender.
The separate `verify_blender_runtime.py` smoke test runs the actual renderer
with `bpy` 4.3 and a controlled two-mesh fixture, checks geometry and verifies two embedded
PNG textures in the GLB. The test environment uses `bpy==4.3.0` and `numpy==1.26.4`.
This checks the renderer, not AI quality or the ARM64 deployment; verify the first real
generated asset after installing on Oracle.

Status and logs:

```bash
systemctl --user status froge-worker froge-ollama froge-tunnel
sudo journalctl _SYSTEMD_USER_UNIT=froge-worker.service _SYSTEMD_USER_UNIT=froge-ollama.service -n 60 --no-pager
```

For an existing installation, download `froge-oracle-update.zip` from the Site, upload it to
Cloud Shell, copy it to the VM and extract it into a separate directory. Run its
`apply_update.py` as `opc`. It checks that no job is active, backs up the replaced code,
updates `server.py`, `ai_stream.py`, `openai_provider.py`, `runtime_check.py`, `code_policy.py` and the trusted runtime modules, restarts only `froge-worker.service`, and verifies
its authenticated health response. It preserves pairing, the tunnel, downloaded AI weights
and all jobs. Failed startup restores the old code. `froge-oracle-wardrobe-v9.zip` is the current named update; older download names are
retained as aliases. After `FROGE_UPDATE_OK`, refresh the Site and use **Ponów ten opis**
on a failed or cancelled job. OpenAI settings remain unchanged. The legacy
`froge-oracle-texture-fix.zip` download is retained as an alias of the current update.

To stop the services:

```bash
systemctl --user stop froge-worker froge-ollama froge-tunnel froge-model-pull
```

Sources: [Ollama Linux](https://docs.ollama.com/linux),
[Qwen2.5-Coder 7B](https://ollama.com/library/qwen2.5-coder:7b),
[OpenAI Astra](https://developers.openai.com/api/docs/models/gpt-6-astra),
[OpenAI streaming](https://developers.openai.com/api/docs/guides/streaming-responses),
[systemd delegation](https://systemd.io/CGROUP_DELEGATION/),
[Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).

## Reproducible verification

Run `python3 -m unittest discover -s oracle_connector -p 'test_*.py' -v` for data-contract,
transport, authentication, cancellation and updater checks. With a Python environment
containing bpy 4.3, run `python verify_scene_runtime.py` to build complete oak, rocket, rapper and tower
fixtures, validate their GLB payloads, verify two embedded oak PNG textures and 20 distinct
bulb meshes, then reimport the GLBs in Blender. `--output /absolute/directory` also saves
each model and review renders; `--scene rapper.scene.json` selects one fixture. This does not call OpenAI or measure Oracle ARM performance.
See `docs/ASTRA-3D-NOTES.md` in the project for the documentation review and measured results.

Version 9 adds separate top/trouser unions, post-union localized folds, sewn pocket panels, cuffs and a folded hood. Sneakers use flat rubber soles, layered uppers, quarter panels, crossed laces and heel tabs. The wardrobe remains a generic procedural design, not an automatic guarantee of retail or print quality. `wardrobe.py` is trusted bundled runtime code and is included in updater rollback.

