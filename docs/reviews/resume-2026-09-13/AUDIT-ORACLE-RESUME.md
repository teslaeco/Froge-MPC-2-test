# Oracle resume audit — 2026-09-13

Read-only audit for parent integration. No Oracle, Studio, secret, job, branch or deployment mutations performed.

## Verified source and CI
- Base branch `codex/v27-mcp-startup-audit` currently points to `5c02f9ff1243b88876fef2631346c480a70cfffa`. Confirmed by Git ref API.
- [Draft PR11](https://github.com/teslaeco/Froge-MPC-2-test/pull/11) is open, mergeable and unmerged; head `01bf1d05ed72eb4e9da48d513d5b34a1a71e34f2`, 77 files, 2 commits.
- Base checkpoint is E16. PR checkpoint is E18 and explicitly says no Oracle installation.
- [CI run 34721452691](https://github.com/teslaeco/Froge-MPC-2-test/actions/runs/34721452691) failed for Python3.9 and3.12. Python3.12: 115 tests, 13 errors, all updater fixture FileNotFoundError for `incoming/runtime/reference_reconstruction.py`. New updater allow-list contains the module but test_update.py fixture does not create it.
- Codex install, MCP smoke and real Blender steps were skipped after that failing gate. The earlier 16 targeted passing tests are not evidence that required CI passed.
- `.github/workflows/oracle-control-plane.yml` is a test workflow only, not a deploy mechanism. No deployment action is present.

## Recovered exact limits: code outranks stale README
| Setting | Source value |
|---|---|
| Connector version and updater expectation | 33 |
| OpenAI model | gpt-6-astra; reasoning high |
| Agent | 32 requests; 96,000 output/reasoning tokens; 5 builds; 1,800 seconds |
| Non-agent initial AI / Blender | 600 / 900 seconds |
| Worker input | Prompt5,000 UTF-16 units; agent instructions12,000 |
| Worker GLB and Studio import | 48MiB |
| Interchange export aggregate | 512MiB |
| Container | 2 CPUs, 4GiB default; 8GiB only requested8K profile with >=10GiB available |
| Photos | <=4; max reference edge8192; texture sizes2048/4096/8192 |
| Retention | One active job; max300 retained jobs; requires2GiB free before accepting new work |

No evidence of GPU usage in this worker path; it launches rootless Podman CPU Blender. Do not describe a quota increase as a quality fix.

## Integration gaps
1. PR11 adds runtime report and updater dependency, but `server.py` and `quality_report.py` are unchanged from v33. `quality_report.model_status` still trusts `completed_outcome.accepted` alone; reconstruction/board evidence is not part of host promotion.
2. Health remains connectorVersion33 with no new revision distinguishing PR11. A returned33 cannot establish installation of the new code. Add an explicit capability/revision or verified source hash in the parent patch.
3. An updater must preserve active-job double checks, code/tool rollback, pairing, keys, models and tunnel. Do not alter those to force installation.
4. Installer rejects busy jobs. A reinstall is not needed to read a prior job. Paid trial is opt-in and must not be used merely to diagnose.

## Latest screenshot evidence (not fetched Oracle logs)
Julia job: `076cb6e8-c3de-4a59-a7b9-c0dfeb2d0e0d`, verified in025146.
Atlas job: `b653826a-1b24-44f5-a881-c0e0c2492a18`, verified in021422.
Julia025123 reports SyntaxError line30, ANATOMY_VALIDATION skin_atlas missing >=2048 (expected/actual head/eye/hand/nail counts match); five-build budget exhausted; 27 API requests and20,663 output/reasoning tokens; final246,828 triangles186objects11images. It explicitly lists hair roots/gaps/thick bands, oversizedcircularorbit, separate nasalholes, poor smile, longneck, blockygarments. Thus no evidence here of OpenAI quota exhaustion or insufficienttrianglebudget as primary cause.

## Access and read paths
Documented Oracle host: `opc@141.148.242.30`; installed path `~/froge-connector`; Cloud Shell private key file `~/ssh-key-2026-09-06.key`. The key must remain in the user's Cloud Shell, not in chat.
Local read-only presence check: ssh exists; documentedkey absent; localOracleinstall absent. No Oracle/SSH connector tool exposed. No remote SSH or credential attempt made.
Worker loopback listens at `http://127.0.0.1:8765`, bearer from local `state/config.json`; do not print/copy its value.
Existing private Studio stores that credential encrypted under its existing settings secret; preserve it. Use authorized owner HTTP session instead of exposing the bearer.

| Resource | Private Studio owner route | Worker route |
|---|---|---|
| Health | GET /api/blender/connection | GET /v1/health |
| Job | GET /api/blender/jobs/{id} | GET /v1/jobs/{id} |
| Quality | Verify current deployed router; base source lacks Studio quality route | GET /v1/jobs/{id}/quality |
| GLB | GET /api/blender/jobs/{id}/model | GET /v1/jobs/{id}/model |
| Export list | GET /api/blender/jobs/{id}/exports | GET /v1/jobs/{id}/exports |
| File | GET /api/blender/jobs/{id}/exports/fbx (or blend,scene-json,obj,stl,master,pbr) | GET /v1/jobs/{id}/exports/{format} |

GET export paths do not invoke AI. Only succeededworkerjobs may download exports throughthatAPI. Failedjobfolders canstillcontainpreservedmodelsforread-onlySSHrecovery. Full job folders are `~/froge-connector/state/jobs/{id}/`. ParentmayuseexistingauthorizedSitesDB/logstools; this agent did not accessSiteslifecycle.

## Exact documented v33 update command, not a new release
After uploading the actuallybuilt/verified v33 ZIP into the existing Oracle Cloud Shell:
```bash
python3 -m zipfile -e "$HOME/froge-v33.zip" "$HOME/froge-v33"
python3 "$HOME/froge-v33/froge-v33.py"
```
This installerSSH-streamsscript toOracle; validatesbaseassetSHA before stoppingworker; stages tools; tests actual Codex/MCP/Blender; rolls back on failure. It does NOT deployStudio.
This command refers to existingv33. Do not present it as applyingPR11/newfix unless package was rebuilt from that exact testedsource and released withidentifyingversion.

## Parent release procedure
1. Fix failing updaterfixture and run workflow's full unittests, plus new regression suite. RecordtestedSHA.
2. Integrate review into host quality/promotion path and exposeunambiguousnewrevision. Preserve draftmodel availability.
3. Buildrelease fromthatSHA with completeallow-list and correctbaseassetmanifest. Prefernewnamedrelease overambiguousv33overwrite.
4. Package/probecompile+ZIP integrity locally; run no-paid-API Codex/MCP/Blender checks.
5. Recoverjobartifacts/reportsbeforestartingnewjobs. Keeporiginals and hash models/reference.
6. DeployonlythroughavailableauthorizedCloudShell/SSH session; absentaccess, handoff exactverifiedZIP+command, neverclaiminstalled.
7. Afterinstall readhealth+newrevision andhash; exercise newinputjob withuser'srequestedgeneration and inspectactualrenders. Sourcecommit≠workerinstallation.
8. UpdateprivateStudio separatelyonlyifhostUI/APIchangesneeddeployment, preservingowner-onlyaudienceandsecret.

