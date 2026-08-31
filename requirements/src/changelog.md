# Changelog

## 2026-08-31 — Detailed render logs (planned, then implemented same day)

- Prompted by: clicking Render and getting only a single-line `job.error` on
  the scenario widget isn't enough to diagnose a failed render.
- Captured via a `grill-me` design session (interview + codebase
  exploration) — see the [Status of this
  baseline](./requirement-taxonomy.md#status-of-this-baseline) note on the
  `Planned` marker convention introduced by this entry. Built and verified
  the same day; all FRs below are now `Implemented 2026-08-31`.
- Verified end-to-end against a real render failure (missing `asciinema`
  binary): the log correctly grew across polls while `status=running`
  (confirming true streaming, not buffered-until-exit), captured the
  in-container typed command via the `pexpect` pty mirror, and pinpointed
  `bash: asciinema: command not found` as the real root cause — detail the
  previous single-line `job.error` could never have shown.
- Updated [FR-REND-004](./functional-requirements/render-pipeline.md#fr-rend-004--run-the-pipeline-and-capture-output):
  mirror the in-container `pexpect` session to `driver.py`'s stdout
  (previously only infra-level output was captured) and strip ANSI control
  sequences before storing.
- Updated [FR-REND-005](./functional-requirements/render-pipeline.md#fr-rend-005--failure-surfaces-to-the-caller):
  capture a full traceback into `job.log` for the catch-all
  unexpected-exception path, which previously lost all detail beyond the
  one-line exception string.
- Added [FR-REND-009](./functional-requirements/render-pipeline.md#fr-rend-009--detailed-render-log-available-on-demand)
  (on-demand full log via a new `GET /api/jobs/{id}/log` endpoint + a "View
  logs" dialog, scoped to the latest job only — job-history browsing was
  explicitly descoped) and [FR-REND-010](./functional-requirements/render-pipeline.md#fr-rend-010--render-log-streams-while-the-job-runs)
  (true incremental streaming while the job runs, replacing the buffered
  `subprocess.run(capture_output=True)` capture).

### Decisions made during the design session (recommended option chosen each time)

- In-container session capture: raw pty mirror, not a structured per-step
  rewrite of `driver.py`'s execution model.
- Scope: latest job only, not a job-history browser.
- UI: `Dialog` (not `Sheet`), added to both `ScenarioCard` and
  `ScenarioEditorPage`.
- Log fetched via a dedicated endpoint, kept out of the routinely-polled
  `Scenario`/`RenderJobRead` payload.
- True incremental streaming chosen over the cheaper stage-level-granularity
  or fetch-once-on-terminal alternatives, despite the added cost of moving
  off buffered `subprocess.run`.
- ANSI/control sequences stripped before storage.

## 2026-08-30 — Initial baseline

- Created the requirements mdBook (`requirements/`) via the `requirman`
  skill, seeded entirely from a code audit rather than a discussion.
- Added `FR-CORE-001..023` (project/playlist/scenario CRUD + cascade
  delete), `FR-EDIT-001..004` (step validation, env/typing config, YAML
  export), `FR-REND-001..008` (render job lifecycle, workspace isolation,
  failure handling, polling, timeout), `FR-CLI-001..008` (standalone
  record/render pipeline).
- Added `NFR-001..008` covering auth posture, the "don't reimplement
  driver.py/render.sh" invariant, separate uv projects, cascade-delete
  media-cleanup gap, polling-only status, render timeout, external tool
  deps, and data storage layout.

### Open questions (TBD, not invented)

- Should cascade-deleting a project/playlist/scenario also delete its
  render jobs' media files on disk ([NFR-004](./non-functional-and-constraints.md#nfr-004--cascade-deletes-do-not-clean-up-media-on-disk))?
  No stated intent either way in the code.
- Is single-operator/no-auth ([NFR-001](./non-functional-and-constraints.md#nfr-001--no-auth--single-operator-tool))
  a permanent product decision or a placeholder for a future accounts
  feature? Undecided as of this baseline.
