# Generator v19 — fitted reference couture

Status: implemented source and full installer; **not installed on Oracle and not
visually verified in Blender**. This is not a photorealism or identity milestone.

## Why this change exists

The v18 GitHub `reference_character` renderer calls `person` with `outfit:
sweatshirt`, then adds a skirt and four planar decorations. It cannot preserve
the reference's close-fitting dress. The GitHub baseline also predates the
Site's v16 portrait/hands, photo handling and three-person fixes. This change
keeps that newer generator baseline and replaces the sweatshirt construction.

## Actual implementation

- Dedicated body-following gown, stitched inner and outer surfaces, 1–6 mm
  material thickness and bounded clearance; no sweatshirt/trousers template.
- Thin conformal facets, raised open-front collar, belt, attached shoulder
  drape, full hidden legs and shoes. Unseen areas remain labelled reconstruction.
- Pleated hand-held fan with solid five-blade rotors, shared rotor mesh data,
  real fan ribs, detailed anatomical holding hand and manicure.
- Existing parametric CC0 portrait, separate textured eyes, lashes and makeup,
  swept updo, head rotation with attached jewellery. Face likeness remains
  approximate; seven proportions do not constitute photo-to-face reconstruction.
- Satin/crystal materials use exportable Principled inputs. Couture GLBs are
  reopened by the worker and checked for retained anatomy, part roles, UVs,
  embedded images and finite coordinates before success.
- 600-second AI deadline, 900-second Blender deadline on fresh and saved plans,
  measured stage progress and forced process cleanup after cancellation.
- 5000 UTF-16 units consistently with the existing browser textarea; a new
  capability check blocks longer prompts/unsupported couture on old workers
  before an AI job is submitted. Previous photo history/replay/group code stays.

## Verification completed in this session

- 82 Python tests passed, including numerical production geometry, prompt
  boundaries, cancellation, private photo transport and rollback behaviour.
- 74 frontend/API/photo tests passed using Node with real SQLite.
- TypeScript and production client/worker builds passed.
- Full ZIP CRC check passed; every one of 33 payload files matches source bytes.
- ZIP `froge-v19.zip`: 15,332,079 bytes, SHA256
  `9ee87bf071600b6fdf990ef57872e8250c3ac021b4eaf3e87140fe3b7423493d`.

No Blender/podman executable was available in this environment. A request to
install bpy was cancelled by the execution service. No Blender render, live
Oracle generation, paid AI request, identity comparison, rig test or print test
was completed. Mocked updater test output is not evidence of an Oracle install.

## Installation and required next verification

Upload `froge-v19.zip` to the existing Oracle Cloud Shell and run:

```bash
python3 -m zipfile -e "$HOME/froge-v19.zip" "$HOME/froge-v19"
python3 "$HOME/froge-v19/froge-v19.py"
```

This uses the existing SSH key and VM, preserves pairing/API key/jobs, checks
that no job is running, makes a backup and rolls back if its production Blender
fixture fails. It makes no paid AI call. The test GLB/BLEND remain in a printed
`state/couture-review-v19-*` directory for inspection. `FROGE_V19_OK` requires
connector 19, renderer 3, portrait 1, character standard 19, couture revision 1
and the GLB reimport check. A full installer is not evidence it has been run.

For an explicit six-view review on a host with Blender, run:

```bash
blender -b --python oracle_connector/verify_couture_runtime.py -- --output /absolute/review-v19 --render
```

It builds the production fixture and renders the reimported GLB (front, back,
three-quarter and three face angles). Compare the real GLB with the reference:
face/eyes first, then fingers, fit, clipping, hair, fan and material response.
Only then decide what needs correction. Do not call the stage complete because
the source compiles or the runtime reports success.

## Repository boundaries

Canonical Site source is based on `dd3e257` (Site 38). The GitHub worker PR is
based on PR #6 commit `032413a` and imports the newer Oracle runtime, its tests
and packaging only. It does not replace the GitHub application's older frontend
or copy 78 MB of historical sample assets. The v19 frontend changes are saved in
Site Git. No Site publication or Oracle installation was performed in this turn.
