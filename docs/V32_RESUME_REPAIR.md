# V32 — resumed generator repair, 2026-09-12

## Current observed service state

The live Studio displays Oracle v29 and offers v31. Latest saved Site is 47
(source e3d60697db43744f6c09157328560c66a031f9a2). Full and shallow source
clones both fail with HTTP 500 / expected packfile. No Site deployment occurred.
Browser session can read the owner's jobs; earlier 401 log entries are not proof
that the user's current authenticated session is broken.

Job dab89472-8019-4d83-b486-bcbf7c693eed reports a saved draft and edit failure:
Standard portretu: brakuje rzes dopasowanych do obu powiek.
The form AND its saved prompt contain a prior generation status sentence
(580.6 seconds), not a character brief. Clicking reuse prompt reproduces that
stored value. Its original entry mechanism has not been established; do not
claim that the current UI automatically overwrote it or invent a replacement.

## Source changes

- Drain the complete Code Mode call after finish_model until CLI acknowledgement
  or exit, bounded by the existing deadline. Do not kill delayed final reads at
  two seconds. Verified results survive a missing acknowledgement; no extra
  provider request after completion.
- Bound MCP snapshots by serialized wire size; page large scene/edit/report
  sections with revision and SHA256 checks. Agent guidance explains pagination.
- Keep heads, eyes, hands, nails and eyelash metadata separate during helper
  joins. Keep structural/UV/atlas/lash gates; return exact counts and offending
  object names. Preserve expected anatomy counts across edits and write atomic
  anatomy-failure.json for a rejected candidate.
- Full v32 program update with pinned reuse of five unchanged assets, rollback,
  CLI and Blender checks. Paid-trial receipt identity remains v31 to prevent a
  duplicate paid trial when upgrading. No paid generation was requested here.
- Native anatomy regression added to CI and the installer. No native Blender
  is installed in this local environment; native result remains pending.
- UI polling race patch and three regression cases saved under reviews/v32.
  They are NOT applied to the inaccessible canonical Site and NOT tested here.

## Checks actually run

98 unique offline Python tests passed (56 lifecycle/MCP/worker tests and 44
update/delta/connector/OpenAI tests, two delta cases overlap). Python compilation
passed. Update initially lacked recovered texture assets; all five were restored
from the existing v25 package and verified against the current SHA256 manifest.
The update tests then passed. No mocked test result is a real AI generation.
Package v32 compiled and ZIP integrity passed: 366626 bytes, 65 payload paths,
payload SHA256 76fab3c63c083313a03b3612d2d0d360bc9aa140301f4176646114498d23cbcc.

## Remaining gates

1. Run native Blender and actual pinned Codex smoke on CI, inspect failures.
2. Restore canonical Site source; apply/test the polling race patch and publish
   with the existing private audience. Do not replace the Site with old GitHub UI.
3. Install verified worker on existing Oracle (authorized SSH session/key is not
   present here), confirm v32 health. Package creation is not installation.
4. Restore the intended character brief using its original source and test two
   consecutive distinct generations only within the user's approved API budget.
   Inspect actual GLBs, all views and materials. Likeness remains unverified.
