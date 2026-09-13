# R12 measured audit and partial geometry correction

Status: partial and not accepted. No Oracle or site deployment.

Reproduction in the same workspace from saved R11 assets and runtime helpers:
1. audit.py compares sampled R11 head points against saved original 1M surface.
2. rebuild.py creates local changes and first rejected nose/neck attempt.
3. Open its R12 blend and run correct.py: restores neck, tries rejected separate nasal patch.
4. Open the resulting R12 blend and run stitch.py: rejected angular boundary stitching experiment.
5. Open the resulting R12 blend and run finalize.py: restores original head and nasal cavity, preserves coherent front UV mapping and other local changes.
6. render.py reimports FBX and renders front, left, back, face and clay face using frozen R11 framing.
7. compose.py produces comparison sheets and upload manifest.

Do not run intermediate scripts and call their output final. Finalize restores the failed nasal experiment. The angular sort in stitch.py did not establish a valid single edge loop and caused visible folds. Future reconstruction must trace connected boundary loops and verify topology before interpolation.

Final local changes retained: asymmetric scalp plus 52 root meshes replacing old panel and 76 transverse rails; removal of floating jaw/orbital overlays; differentiated crowns/recessed lower teeth; small corset curvature adjustment. Nose and neck reconstruction failed and were reverted. The new scalp still looks panel-like, hair still coarse, teeth regular, garment simplified and likeness insufficient. No new global flat subdivision was used.

Detailed measured audit and visual limitations are in FORGE-analiza-r12.md. Counts are technical validation, not evidence of likeness. Rendered previews are actual reimported FBX, not generated illustrations.
