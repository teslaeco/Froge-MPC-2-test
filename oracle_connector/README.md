# Froge Oracle connector

This is the text → selected AI → Blender → GLB worker for the private Froge test studio.
It is separate from the desktop Blender add-on and the example dragon.

## Saved-script recovery (version 5)

AI sometimes redefined `make_material`, replacing the supplied renderer helper with an
invalid implementation such as `image.generated_type = 'RGBA'`. The worker now validates
the entire original source, removes plain top-level definitions of the reserved helpers,
and validates the prepared source again before execution. Calls and geometry remain in
the script; the provided, tested helpers supply materials and meshes. Other rebinding or
nested replacement of helper names is rejected. Forbidden operations are still rejected,
even if they occur inside a helper definition that would otherwise be removed.

For a failed job with a saved `generate.py`, the studio offers **Wykonaj zapisany skrypt**.
It creates a separate job from that script and its original description. It checks owner,
endpoint, source-job state and source size, retains the original failure and source, and
runs the same policy and container checks. This path makes no AI request and never falls
back to AI automatically. Other errors in the saved code can still cause failure.
The real Blender smoke test reproduces the enum error and verifies its correction plus
two embedded PNG textures; it does not run the user's complete Oracle script.

Install `froge-oracle-rebuild.zip` using the normal updater, refresh the studio and use
the saved-script button. The OpenAI settings remain available for new descriptions.

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

OpenAI uses low reasoning effort, compact helper-based code, streamed responses, and a
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

With local Qwen, a model run may take several minutes on 2 CPU cores. Code generation attempts share
a 30-minute deadline and each response is capped at 5000 output tokens; Blender gets 10 minutes
per attempt. The local request uses curl (installed by `install.sh`), with a total deadline,
live wait/progress messages and cancellation even before the first HTTP headers arrive.
There is no 180-second inactivity cutoff during model loading or prompt evaluation.
Incomplete streams are rejected, even if they contain syntactically valid partial code.
Forbidden attribute operations such as `.load` are detected on complete code lines during
streaming, with strings/comments ignored. The full AST policy still runs before every
execution and the container boundary is unchanged. Materials use `make_material` and its
packed procedural textures; no input image files are assumed to exist. Policy failures get
an English repair instruction with valid helper examples and the original user request,
without repeating rejected file-loading code. Drafts and rejection details are retained
privately under the job directory for diagnosis, and rejected drafts are never executed.
The renderer preserves unchanged packed texture bytes instead of packing them twice:
repacking a generated image without an external filepath can discard its PNG in Blender 4.3.
One active job is allowed.
Quality and exact adherence depend on the selected model. This is procedural AI modeling,
not a pretrained image-to-3D or photogrammetry service. Textures are procedural packed UV images.

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

The generator returns Python which is syntax/policy checked and run in a separate rootless
Podman container. The container has no network, a read-only root filesystem, dropped capabilities,
no new privileges, a 4 GB RAM limit, 2 CPUs, and a 256-process limit. Only its own job directory
and the read-only renderer are mounted; SSH keys, API tokens and the worker database are excluded.
The Python filter is defense in depth, not a general-purpose Python security sandbox.

Completed `.blend`, `.glb`, generated source and logs remain under `state/jobs/<id>/` on the VM.
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
updates `server.py`, `ai_stream.py`, `openai_provider.py`, `runtime_check.py`, `code_policy.py` and `runtime/run.py`, restarts only `froge-worker.service`, and verifies
its authenticated health response. It preserves pairing, the tunnel, downloaded AI weights
and all jobs. Failed startup restores the old code. `froge-oracle-rebuild.zip` is the explicitly
named version-5 download. After `FROGE_UPDATE_OK`, refresh the Site, connect OpenAI in
**Ustawienia serwera**, then use **Ponów ten opis** on a failed or cancelled job. The legacy
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
