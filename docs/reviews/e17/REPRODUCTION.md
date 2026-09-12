# Reproducing the authored review assets

The correction scripts preserve the executed worker paths as source evidence. They are not a general photo-to-3D training implementation. To rerun them elsewhere, provide the referenced input BLEND/FBX files and adjust the workspace path constants or use an equivalent mounted workspace. Do not run with automatic execution of embedded Blender scripts; the validation commands use `--disable-autoexec`.

The chain is E15 user-provided source → E16 baseline → E17 hair/material edits → E18 local anatomy/hairline repair. E17/E18 scripts and reports accompany this PR. Large source model files are delivered separately and are not embedded as ordinary Git blobs. The current web GLB is published with a SHA-pinned manifest in `public-studio/`.

The Queen fixture reuses the existing `oracle_connector/runtime` modules. Its executed build script expects that runtime copied beside the script as `runtime/`; `scene.json` belongs beside it. This preserves the exact import arrangement used for the reported Blender validation. No recovered facial landmarks from another image were silently treated as this poster's measurements.

The trailer scripts expect the user-provided source clip basenames in `upload/`, plus the Queen render; their hashes and durations are in the trailer verification report. Source media are not copied into the repository. The published MP4 is a derivative montage authorized by the user.

Generator checks can run directly in this repository:

```sh
python oracle_connector/test_reference_reconstruction.py
blender --background --threads 2 --disable-autoexec --python-exit-code 1 --python oracle_connector/verify_board_review_blender.py
```

The board verification script reads the actual Blender geometry and material assignments of known positive and negative fixtures. It is independent of the published character render. Running it does not train weights or deploy the Oracle worker.
