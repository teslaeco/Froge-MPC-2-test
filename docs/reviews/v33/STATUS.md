# v33 — deliberate skeletal anatomy, 2026-09-12

Incident: job 49ac337d-0a00-4c94-96ef-d8dfa716d435 used the correct user brief
and 1024x1536 original, with human face landmarks. Screenshots show a deliberately
empty skeletal orbit rejected as a missing eye/lashes and visibly wrong teeth,
seam, face proportions and hair. Live Studio confirms Oracle v32; this supersedes
the earlier checkpoint saying v29. Current browser history is from another session;
its status-as-prompt job is NOT the incident being repaired.

Implemented: explicit per-portrait left/right eye intent with evidence, preserving
ordinary defaults; living-eye side/head identity and per-side lashes; trusted plan
intent restored after edits; nonhuman declaration skips human landmark fitting;
actual evaluated-geometry ray occupancy blocks acceptance of a filled socket;
drafts remain inspectable. This is not a skull reconstruction template and does
not certify likeness. Added detailed reference repair prompt and regression tests.

113 selected local Python tests passed before adding the socket acceptance gate.
Earlier broader legacy suite had two outdated assertions (unrelated reference_views
normalization and prompt wording) and one missing historical ZIP fixture. They
were not disguised as successes or rewritten to pass. Final focused suite: 114 tests passed locally and on Python 3.9/3.12.
Native Blender 4.3.0 passed Codex->MCP->GLB/texture/3renders/FBX, edit-palette
regressions, legitimate missing-eye/lash export, wrong-side/deleted living-eye
rejections and actual rays rejecting an untagged filler globe. The open test orbit
also passes the rays. Full ordinary-person material grouping now preserves lash
identity and passes anatomy verification. These are authored tests, not likeness.
Verified final runtime source: 3475ebac088c8c658508fbfaf9c99b810d2b6f20.
CI run: 34691768540, both jobs succeeded. No new paid API generation.

Site47 is unchanged. No Oracle SSH session is available here; v33 is not installed.
The submitted bad model has not yet been geometrically repaired or visually
accepted. Package: 376816 bytes; SHA256
2edee904365b9f88e000dc6e2a0eb88ae828c50f25f3313966d215a0ecbd6938.
ZIP integrity and all 60 source payloads match local source; 5 base assets are
SHA-pinned. POLECENIE-CODEX.txt is included in the ZIP. After installation,
apply the prompt to the original reference, inspect actual renders, and retain draft
status until the remaining visual defects are corrected.

Saved deliverables: froge-v33.zip Library libfile_a73a1702d70c819197915524cd3130ef v0;
FORGE-v33-instrukcja.md Library libfile_2bd151e4bcc48191be248ec6655bd52b v0.
Both saves succeeded and local identity metadata applied. Source saved, not deployed.
