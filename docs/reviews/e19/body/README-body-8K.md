# E19 — torso geometry and authored 8K skin textures

This correction operates on the recovered E18R adult character in the split ivory/black dress. It does not turn the model into the separate Julia character in a hoodie.

## Geometry

`apply_body.py` exposes `apply(with_textures=True)`. It edits only the continuous shoulders/neck, upper arms, gown and attached neckline/seam meshes. A shared continuous deformation preserves their relative placement:

- restrained paired bust/corset contours and a recessed centre front, with about 5 mm added local projection rather than exaggerated spheres;
- subtle curved clavicles and a suprasternal notch;
- blended neck muscle contours and a 28 mm upper-rim extension into the existing jaw volume, to hide the old open collar gap;
- the face, skull, dental objects, eyes and hair are left to the corresponding correction modules.

This is a surface-shape refinement, not a medically validated skeletal reconstruction. Shared deformation does not weld previously separate parts or certify manifoldness or material thickness.

## 8K maps

`bake_body.py` opens E18R, applies the same geometry correction and bakes Blender Cycles procedural material evaluation through the actual torso `UVMap`, at 8192 × 8192 pixels. The original cylindrical seam had 124 triangles incorrectly spanning most of the U interval. Per-loop wrapping is repaired to U=1 before baking; the identical UV correction is applied when assigning the maps. Only the torso/neck object is selected. No lights, AO or shadows are baked into colour. The map contains padding and unused UV space; resolution is the whole atlas, not 8K per individual body region.

- `E19_body_BaseColor_8K.png`: new procedural colour variation on living skin; retains the existing lower-resolution weathered-bone source colour on the skeletal half. This is not a recovered 8K reference photograph.
- `E19_body_ORM_8K.png`: red = 1 (no AO bake), green = newly authored roughness, blue = 0 (nonmetal).
- `E19_body_Normal_8K.png`: tangent-space normal bake from physically scaled procedural pore/bone bump detail. Existing bone normal relief is included. This changes lighting response; it does not add printable pore geometry.

The existing facial likeness image remains unchanged and lower resolution. The body atlas must not be described as a new high-resolution face scan or proof of likeness. Side/back reconstruction remains artistic interpretation because the reference is a front image.

The script assigns these three maps to new torso material copies and preserves the original source file. The master/export must retain 8192 dimensions to be labelled 8K; reduced web previews should be labelled separately.

`8k-bake-report.json` records exact dimensions, semantics and SHA-256 values. `body-apply-report.json` records geometry displacement bounds from the applied scene. A before/after render under identical cameras and lights is required to judge the changes.
