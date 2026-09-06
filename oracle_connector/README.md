# Froge Oracle connector

This is the actual text → local AI → Blender → GLB worker for the private Froge test studio.
It is separate from the desktop Blender add-on and the example dragon.

Requirements: the existing Oracle Linux 9 ARM instance, user `opc`, the already-tested
`localhost/froge-blender:local` Podman image, and about 10 GB additional free disk space.
The installer uses official ARM64 Ollama and Cloudflare downloads. The selected local
Qwen2.5-Coder 7B model is about 4.7 GB; inference runs on CPU. No paid AI API is used.

1. Download `froge-oracle-connector.zip` from the authenticated Froge studio.
2. Upload the ZIP to Oracle Cloud Shell (Menu → Upload).
3. Copy the ZIP to the existing VM, extract to `/home/opc/froge-connector`, and execute `install.sh`.
4. Paste the HTTPS address and pairing code printed by the installer into the Froge connection form.
5. Wait for local AI to finish downloading; the connection status shows actual download progress.
6. Enter any model description and click **Generuj model 3D**. The request creates a new job;
   there is no keyword-to-example fallback. The model appears only after valid GLB export.

The first model run may take several minutes on 2 CPU cores. Code generation attempts share
a 30-minute deadline and each response is capped at 5000 output tokens; Blender gets 10 minutes
per attempt. The local request uses curl (installed by `install.sh`), with a total deadline,
live wait/progress messages and cancellation even before the first HTTP headers arrive.
There is no 180-second inactivity cutoff during model loading or prompt evaluation.
Incomplete streams are rejected, even if they contain syntactically valid partial code.
One active job is allowed.
Quality and exact adherence depend on the local model. This is procedural AI modeling,
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
artifact transfer and explicit failures. They do not validate actual Ollama output quality or
execute Blender; verify the first real generated asset after installing on Oracle.

Status and logs:

```bash
systemctl --user status froge-worker froge-ollama froge-tunnel
sudo journalctl _SYSTEMD_USER_UNIT=froge-worker.service _SYSTEMD_USER_UNIT=froge-ollama.service -n 60 --no-pager
```

For an existing installation, download `froge-oracle-update.zip` from the Site, upload it to
Cloud Shell, copy it to the VM and extract it into a separate directory. Run its
`apply_update.py` as `opc`. It checks that no job is active, backs up the replaced code,
updates only `server.py` and `ai_stream.py`, restarts only `froge-worker.service`, and verifies
its authenticated health response. It preserves pairing, the tunnel, downloaded AI weights
and all jobs. Failed startup restores the old code. After `FROGE_UPDATE_OK`, refresh the Site
and use **Ponów ten opis** on the failed job to submit the same prompt as a new job.

To stop the services:

```bash
systemctl --user stop froge-worker froge-ollama froge-tunnel froge-model-pull
```

Sources: [Ollama Linux](https://docs.ollama.com/linux),
[Qwen2.5-Coder 7B](https://ollama.com/library/qwen2.5-coder:7b),
[Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).
