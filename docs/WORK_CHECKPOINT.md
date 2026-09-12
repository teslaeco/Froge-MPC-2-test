# 2026-09-12 — R12 measured analysis and PARTIAL correction, failed nose/neck changes reverted

Final review status: NOT ACCEPTED as faithful reconstruction. User criticism is justified: 4800 / 6858 sampled front/head points from R11 remain on original 1M surface within 1e-5 units (~70%); forehead 622/622. Sampling is not area-weighted or whole-model percentage. Do not represent flat barycentric subdivisions as reconstructed detail.

Retained R12 changes: asymmetric scalp and 52 root meshes instead of old triangular panel plus 76 transverse rails; removed floating Half_mandible and duplicate orbital rim; varied crown heights and recessed lower teeth; coherent projected forehead UV; small corset curvature adjustment. Existing long wave guides retained. No new global flat subdivision.

FAILED AND REVERTED: nasal border relaxation, separate annular patch, angularly sorted boundary stitching; last attempt produced visibly folded rectangular region. finalize.py restores original R11 head/cavity and reapplies coherent frontal UVs. Neck cutting/fitting attempt also reverted to R11. Do not claim nose or neck repaired. Current scalp still panel-like, hair coarse, teeth regular, garment simplified, likeness inadequate. No claim print-ready.

Final FBX reimport: 1,955,886 triangles, 417 mesh objects / 417 with UV, no missing texture images. Actual FBX renders viewed: face, neutral clay face, front, left, back. Comparison freezes R11 camera/light setup. Seven standalone deliverables saved successfully with per-item metadata confirmed: 3 comparison/view PNGs, FBX, BLEND, GLB and Polish detailed analysis. Artifact identities/hashes in docs/reviews/reconstruction-r12. Old R11 preserved. Source previous checkpoint dfaf4e39d59edccc7ad4ed9d4eee62adfd1a8fd6; this final source commit contains scripts and exact reports.

Next useful repair: trace connected edge loops around nasal opening rather than angular point sorting; establish sound local topology and inspect clay front/profile before exporting. Rebuild hairline as fine rooted strands rather than visible cap, fit facial landmarks, connect head/neck anatomy, reconstruct garment construction. Do not restart whole model or pad triangle count. This stage is partial, not completion of requested quality.

No Oracle/Site deployment, paid API call or GPU quota change this turn. See README for exact staged reproduction and which scripts produce rejected intermediate versions.
