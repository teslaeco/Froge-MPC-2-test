# Direct model repair — 2026-09-12

User requested real model previews in chat and explicitly stopped generator/Oracle updates. This checkpoint changes only review scripts and documentation.

Source: job 5280cdee-32da-48ce-8b67-2afd34236ce5, original SHA256 b369e18e017412ef87dedd9c82ebdbf1ed10374447988eecb1f8fd46fc31d54d. Original 77-object .blend recovered from the studio download.

Blender 4.3.0 CPU was run locally with auto-execution disabled. Revision r3 repairs shared head/neck proportions and neck alignment, rebuilds scalp and hair, reduces/insets teeth and smooths selected bones. Original packed skin UV/image retained. The script starts from the original .blend, not an already repaired revision. Adapt OUT/original constants to the local file locations before replaying.

The exported r3 GLB was reimported into Blender and rendered at 640x800, 64 samples, front/left/back. These are actual geometry renders. Three-view sheet and editable .blend/.glb were prepared for user review. No paid model calls, no generator update, no deployment.

NOT APPROVED: face/smile resemblance remains insufficient, hair is still too sheet-like with an uneven hairline, skull teeth/central seam and garment folds/sleeves need further work. Unseen back is an interpretation. No print-readiness claim. User is to assess the three views before the next visual iteration.
