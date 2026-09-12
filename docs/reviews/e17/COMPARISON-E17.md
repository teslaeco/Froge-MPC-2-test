# Meshy and FORGE / Astra + Blender — evidence and comparison

## What is being compared

This is a character reconstruction case study, not a leaderboard. The reference is an adult woman with a living left half and a skeletal right half **as viewed in the image**, long wavy hair and a split ivory/black dress. The user's later request adds grey hair to the skeletal side. Left/right image coordinates are recorded explicitly to prevent mirrored edits.

Evidence inspected for this report:

- The user's `POROWNANIE-E15-Meshy.md` and the comparison visible in `Screenshot_20260912-205829.png`.
- Actual E15/E16 renders, including E16 front, oblique and neutral-material views, and the E16 export report.
- E17 evidence is to be linked after the actual final export is inspected. The baseline findings below are not an assertion that E17 fixed each issue.

The available Meshy evidence consists of screenshots. We do not have its underlying mesh, UVs or texture files. The screenshot panel is a crop of the user's composite with its original comparison labels preserved. It has undergone screenshot scaling. Meshy and FORGE were not rendered with a common camera, lighting setup or exposure. Therefore comparisons of fine pore resolution, material reflectance, mesh cleanliness, runtime, cost or absolute reconstruction error would be unsupported.

## Visible details

| Detail | Meshy in the supplied screenshots | E15/E16 evidence | E17 acceptance criterion |
|---|---|---|---|
| Head and cheeks | A more coherent facial silhouette and cheek transition, closer to the reference in these views | R14-derived head is preferred to rejected R15; projected texture still carries too much of the likeness | Preserve the accepted head envelope; check front and both oblique silhouettes before adding detail |
| Living eye | Eyelids and eye opening read more naturally in the screenshot, including its neutral-material view | The coloured frontal view is more convincing than the neutral-material eye; contour discontinuities remain | A shaped upper/lower lid, visible canthi and eye seated behind the lids; no white/spherical replacement that changes the expression |
| Skeletal eye and orbit | Socket, cheek and nose appear more integrated | E16 has a dark cylindrical-looking socket and a very conspicuous eye, with simplified surrounding bone | Keep the user-requested eye inside; assess socket depth and brow/cheek connections from the side |
| Smile and teeth | Teeth appear integrated into the smile and jaw | E16 teeth still look like repeated small blocks and the dark mouth margin is abrupt | Differentiate central/lateral incisors and canines, round incisal edges, follow a curved arch and keep crowns inside the intended mouth envelope |
| Skull and nasal opening | More continuous transitions around the orbit, maxilla and nose | E16 repaired the nasal boundary but does not yet provide a complete anatomical reconstruction | Continuous nasal/orbital walls in clay; no jagged slit, detached patch or texture-only cavity |
| Neck and shoulders | Read as a continuous form with visible anatomical structure | E16 visibly reduces the head/neck step; shape and skin continuity still need refinement | Smooth head-to-neck transition, plausible clavicles and tendons without cable-like relief or a detached neck ring |
| Hair mass | Broad waves and roots follow the reference more closely | E15/E16 show repeated tubular locks and a cap-like hairline; root gap remains conspicuous | Coherent major waves with finer secondary strands; roots cover the cap edge; deliberate brown/grey split with natural variation |
| Dress and torso | Seams, neckline and folds better describe the reference garment | E16 seats seams nearer the cloth and softens colour blotches; bust and folds remain stylised | Garment follows torso volume; neckline/sleeves connect; cloth thickness stays consistent; no floating seam cords |
| Materials | Useful visible texture impression, but lighting and screenshot resolution prevent numerical ranking | E16 uses packed maps and modified cloth colour maps; projected light/shadow remains a limitation on the face | Separate colour, roughness and relief; test under a second light direction; pores do not replace missing anatomy |
| Scene context | Film-strip prop and surrounding forms appear in the earlier screenshots | E15/E16 character exports do not reproduce the forest, moon or film strip | State whether the deliverable is the character alone or the complete scene |

**Baseline conclusion:** Meshy achieves stronger visible likeness and more coherent anatomy in these particular supplied examples. E16 makes local technical corrections but remains an unfinished reconstruction. Its export checks establish that geometry, UVs and active textures survive an FBX round trip; they do not establish that the character matches the illustration.

## Measured and unmeasured quantities

| Quantity | E15 | E16 | Meshy screenshot |
|---|---:|---:|---|
| Exported triangles | 1,990,254 | 2,008,003 | 3,057,126 displayed in the earlier UI; not independently read from its mesh |
| E16 mesh objects | — | 419 | Unmeasured |
| E16 active missing texture images | — | 0 in the reported FBX import | Unmeasured |
| Visual acceptance by user | Preferred to R15; still defective | Not accepted as faithful | User considers the displayed likeness better |
| Watertightness / print readiness | Not certified | Not certified | Not tested by us |
| Animation deformation quality | Not tested here | Not tested here | Not tested here |

R15 was reported at 6,419,299 triangles and was rejected for a worse head shape. That regression is a direct project example of why polygon count is not the acceptance target. Counts should accompany a render and an artifact hash, never replace the visual result.

## Complementary strengths and next experiment

Meshy provides image-driven geometry/texturing workflows. Its documented multi-image API accepts up to four views and can return PBR maps and several export formats. That makes it a plausible optional source for a base asset, subject to available access and the user's chosen workflow. These documented capabilities do not prove the quality of any untested output. [Meshy Multi-Image to 3D API](https://docs.meshy.ai/en/api/multi-image-to-3d)

FORGE's inspectable Blender workflow can apply object counts, board dimensions, material assignments and local changes to an existing mesh, then verify an exported result. Our proposed combined experiment is: use the same authorized input, preserve the unmodified base, repair a bounded feature in Blender, and compare both the textured and neutral-material exports from identical cameras. Record failed candidates as well as improvements.

For chessboards the user's reports concern cell count, alternating colours and texture placement; those are precise, testable constraints. The inspected private source includes exact board contracts and a visual-QA trainer, but no completed L4 visual-training summary or weight file was recovered from the reviewed repository tree. That is not a statement about unavailable files on the earlier VM. For faces, corresponding checks concern measured landmarks, silhouette, orbital placement and surface continuity. A board checker does not teach facial anatomy automatically. Any transfer claim needs a separate character evaluation.

## Earlier couture character and fan

The repository's earlier `docs/reviews/meshy-reference/README.md` contains a separate real-mesh audit, unlike the screenshot-only split-woman comparison. It compared an imported Meshy bust with a FORGE full figure. The framing covered the upper part of FORGE approximately; it was not a registered pixel-error benchmark.

| Earlier couture evidence | Finding and scope |
|---|---|
| Meshy geometry | 3,079,530 imported triangles in the audited bust |
| FORGE geometry | 592,396 imported triangles in the audited full figure; different body coverage |
| Visible likeness | The archived review found Meshy closer around cheek/lip shape, hair near the ear, collar, grip and diagonal garment folds |
| Fan | The archived review described a differently proportioned FORGE fan; Sebastian separately reported that some fan geometry was better in an earlier Astra attempt |
| Materials | The first untextured Meshy FBX lacked UVs/images; the later upload resolved the missing texture package, with a UV-mapped FBX and higher-resolution maps |
| Workflow contribution | The audit introduced artifact-linked measurements, re-imported clay views and checks that distinguish connected textures from merely present image files |

The earlier fan advantage remains a **user-reported observation about a particular attempt**, not a reproduced result that overrides the archived audit. Recover that exact reference/version pair before making a public superiority claim. Likewise, do not describe the initial untextured Meshy file as proof that Meshy cannot provide textures: the archived follow-up explicitly resolved that condition.

## Publication rules

Show the source label on every comparison. Do not invent numerical likeness scores. Do not imply that Meshy created FORGE edits, that FORGE created Meshy's base, or that a synthetic illustration is an exported model. A public Product Hunt presentation should link inspectable results and describe remaining limitations alongside the progress.
