# Changelog

## 2026-08-31 — write_vim step type (planned, then implemented same day)

- Prompted by: wanting a step type that visibly types a file into `vim` in
  the recorded terminal, character by character, so it reads as someone
  live-programming rather than a heredoc paste.
- Captured via a `grill-me` design session (see the `Planned` marker
  convention in [Status of this baseline](./requirement-taxonomy.md#status-of-this-baseline)).
- Added [FR-CLI-009](./functional-requirements/cli-pipeline.md#fr-cli-009--write_vim-step-blank-mode)
  (blank-buffer type-out, vim's own autoindent left on, best-effort content
  match — no correction pass), [FR-CLI-010](./functional-requirements/cli-pipeline.md#fr-cli-010--write_vim-step-diffliveedit-mode)
  (auto-detected diff/live-edit mode against the container's current file,
  line-level + character-level `difflib` diff driving vim motions), and
  [FR-CLI-011](./functional-requirements/cli-pipeline.md#fr-cli-011--typo-simulation-for-write_vim)
  (optional per-step typo simulation).
- Added [FR-EDIT-005](./functional-requirements/scenario-authoring.md#fr-edit-005--write_vim-step-schema)
  (the `write_vim` step's schema: `simulate_typos`/`force_blank`),
  [FR-EDIT-006](./functional-requirements/scenario-authoring.md#fr-edit-006--upload-a-file-to-seed-step-content)
  (an "Upload file" control seeding `content` for `write_file`/`write_vim`
  steps), and [FR-EDIT-007](./functional-requirements/scenario-authoring.md#fr-edit-007--typing-time-guardrail-on-write_vim-content)
  (save-time rejection of a `write_vim` step whose content would take too
  long to type).
- Verified: `backend/tests/test_api.py` (all 8, including 4 new write_vim
  tests) and `frontend`'s `tsc -b && vite build`/`oxlint` all pass. The
  vim-motion diff logic (`_write_vim_diff`/`_edit_line`) was sanity-checked
  offline against fake input (no real pty), confirming it runs without
  crashing and produces plausible keystroke sequences for both an
  added-lines edit and a same-line-count word-level edit — **not** verified
  against a real `docker`+`vim` recording end-to-end, consistent with the
  documented test-coverage gap for the rest of `FR-CLI-*`
  (see [Traceability](./traceability.md)).

### Decisions made during the design session (interview, one branch at a time)

- Indentation: vim's own autoindent stays on (visual authenticity over
  guaranteed byte-exact output) — explicitly rejected the alternative of
  disabling autoindent for exact reproduction, and separately rejected
  adding a silent post-type correction pass to force exactness.
- Typo simulation: a per-step toggle (`simulate_typos`), not a fixed global
  behavior for all typing.
- Existing-file handling: write_vim supports true live-editing of existing
  content (diff-driven), not just always-blank writes like `write_file` —
  with `force_blank` as an explicit opt-out.
- Before-state source for the diff: read live from the container via
  `docker exec ... cat`, not an explicit `base_content` field the author
  would have to maintain — accepted the larger structural change (threading
  `container_name` into `driver.py`'s `do_step`) for the ergonomic win.
- Diff granularity: character-level within a changed line (not word/token-
  level, not line-only) — the most surgical, most complex of the offered
  options.
- Upload control: available on both `write_file` and `write_vim`, not
  scoped narrowly to `write_vim` alone, since they share the same UI field
  block.
- Large content: got a real guardrail (not left as a documented limitation)
  — reject at save time (422) rather than silently degrading render time by
  auto-speeding-up overflow content.
- Step name: `write_vim`, confirmed.

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
