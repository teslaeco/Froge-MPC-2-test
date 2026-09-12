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
were not disguised as successes or rewritten to pass. Final focused tests and
native Blender CI are pending at this checkpoint. No new paid API generation.

Site47 is unchanged. No Oracle SSH session is available here; v33 is not installed.
The submitted bad model has not yet been geometrically repaired or visually
accepted. Finish native checks and save v33 installer/instructions. After installation,
apply the prompt to the original reference, inspect actual renders, and retain draft
status until the remaining visual defects are corrected.
