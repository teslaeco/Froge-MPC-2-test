# Reference fidelity verification — 2026-09-10

Blender 4.3.0 produced and reopened native test textures at 4096×512 and
8192×1024. Synthetic UV patterns test real encoding and dimensions; they do
not represent reconstructed photographic detail. The texture stage preserved
mesh coordinates, topology, transforms, UVs and material assignment.

The current couture fixture was built with the retained measured reference,
textureMaxSize=4096, exported and reimported. Four CPU renders (front face,
profile, full three-quarter, hand detail; 12 samples) were inspected. The
model is still visually different from the original; see model-verification.json.
Reference imagery remains 1229×1536; skin atlas 2048×2048. Nothing was upscaled.
The user's current attachment is 1122×1402 and also is not native 4K or 8K.

Reproduction with Blender installed:

    blender -b --python-exit-code 1 --python scripts/verify-reference-quality.py -- /tmp/froge-quality
    python scripts/package-blender.py
    python -m unittest discover -s oracle_connector
    npm run build

For the measured couture reproduction, copy the original private
reference-0.jpg and its matching reference-photos.json to an output directory,
retain the original hashes/landmarks, set textureMaxSize=4096 on that metadata,
and run oracle_connector/verify_couture_runtime.py with
--scene oracle_connector/examples/couture-fan-v20.scene.json, --output,
--render --views face-front face-profile full-three-quarter hand-detail.
Without measured photos the deterministic fixture is a generic study.

No Oracle installation, paid model request, weights training or Site publication
was performed. Standalone r8 edits are not silently called generator features.
