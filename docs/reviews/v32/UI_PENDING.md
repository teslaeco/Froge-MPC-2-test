# UI polling audit (v31 baseline, proposed v32 patch)

This directory contains a proposed targeted change, **not an applied or tested Site change**.
The exact published Site checkout could not be downloaded (HTTP 500). Do not replace the
Site component with `github-RemoteGenerator.tsx`; that file is older than the Site source.

## Evidence

- GitHub commit inspected: `41550bd4853abf564203641774931f7fcd0947a9`.
- `docs/reviews/v30/site.patch` is the published Site delta against
  `16ff84334e26466f44240836e1d9a18db432eddd`; its RemoteGenerator blob changes
  `73ea896` → `eac5fda`.
- `docs/reviews/v31/site.patch` does not change RemoteGenerator.
- The v30 patch adds `statusSerial`, but only cancellation increments it.
- Selection, form reset, and generation still increment only `serial`.
- The status effect is keyed only by `active?.id`. A new submission keeps the previous
  active ID until its POST returns. Old GET/GLB responses therefore remain eligible
  during that interval, even when the new model request has already started.
- Checks after `onResult`, in `catch`, and when scheduling another poll do not compare
  either serial. A stale failure can restart polling the previous job.

## Proposed change

`remote-poll-race.apply.patch` uses the apply_patch format and touches only
`src/blender/RemoteGenerator.tsx`. Apply it from the restored exact Site checkout.
It increments `statusSerial` synchronously at selection/reset/new generation/manual
preview, and binds each poll effect to its original `serial`. Both values are checked
after asynchronous work, on failures, and before scheduling the next poll. An old
online handler cannot restart its old job while a new POST is still pending.

Cancellation still increments only `statusSerial`, so its existing polling effect can
resume with a fresh request after a failed cancel or a nonterminal server reply.
Late cancel/preview errors are ignored after selection changes.

## Regression tests supplied

Copy `remote-poll-race.test.tsx` to `src/tests/remote-poll-race.test.tsx` in the exact Site.
The three cases hold the new POST pending while an older GET succeeds, an older GET
fails with a retryable error, or an older GLB download completes. They assert that no
old model reaches `onResult`, no old job overwrites the active job, no old online
handler restarts polling, and exactly one new POST is sent with the user's new prompt.

These tests have **not run**: the current Site source and its dependencies were not
available when this audit was prepared. Run them alongside the existing cancellation
and lost-acknowledgement UI regressions after restoring the exact source. Do not claim
the frontend is fixed or deployed until those gates pass and a deployment succeeds.
