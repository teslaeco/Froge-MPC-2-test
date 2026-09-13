# Public FORGE Studio showcase

The public UI offers real model previews, a local project-brief download and a local B2B quote specification. It does not call paid generation, submit an order or take payment. Supplier rates are provided explicitly by the user. Material/colour/process choices remain part of the brief.

The full deployed source and local Three.js/Draco dependencies are tracked in the canonical Sites source repository. This folder mirrors the editable HTML/CSS/JavaScript and includes a hash-pinned asset manifest and a downloader for the published binary assets and vendored dependencies. No credential is needed to download the public assets. The existing private operator Studio is unchanged.

To reconstruct this mirror after publication:

```sh
python download-assets.py
python -m http.server 8000
```

Open the local HTTP URL. Use HTTP rather than file URLs for ES modules. `assets/model.glb` is the separately compressed web copy; the original Blender/FBX source remains the authoring master. Web GLB textures are reduced to a documented browser budget. The 3D view loads only after a click; the default preview uses real rendered images.

Third-party notices are included in the downloaded `vendor/three/LICENSE` and Draco license. The asset manifest pins every file by SHA-256. No API tokens, operator tooling or private training dossier are included in the public bundle.

Validation: HTML asset/ID references, JavaScript parse checks and real Blender reimport of the GLB. No browser rendering, mobile frame-rate or checkout integration test has been claimed.
