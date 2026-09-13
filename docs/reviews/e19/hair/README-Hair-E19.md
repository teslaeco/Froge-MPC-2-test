# E19 hair refinement

Use `apply_hair.py:apply()` on an already-open original E18R scene. It fails safely if the expected 312 UV-ring hair cores and E17 fine fibre mesh are missing, or if applied twice. Do not use the rejected alternative curtain scripts.

The accepted E18R long fine-fibre groom remains. The 312 supporting hair tubes are reduced around their verified longitudinal UV-ring centres, retaining stronger attachment near roots and tapering tips. Measured mean core radius falls from 1.516 mm to 0.898 mm. No triangles were added. Both the 3,967,360-triangle fine fibre mesh and the supporting cores share a restrained fit adjustment: up to 3.5% narrower lower silhouette and 9 mm less rear stand-off. Roots and the upper head silhouette stay in place.

Materials preserve brown living-side and aged grey skeletal-side hair, with darker roots and less polished reflection. The original 960 E18R root fibres remain. No anatomical or clothing meshes are edited.

Validation: successful Blender 4.3 execution; real Cycles front/left/back renders at 480×640, 20 samples with denoising. This is a modest correction, not a claim of complete photo likeness. The hair still has artificial long-lock grouping and some gaps. The fine fibres are part of a visual asset, and need a separate manufacturing copy with verified joining and feature sizes.

Two broad replacement groom experiments were rejected after actual renders because they introduced a smooth, repetitive curtain look. Their scripts are experiments, not the delivered patch.
