# Render pipeline (web app) (`FR-REND-*`)

The web app never reimplements recording/rendering logic — it materializes a
DB-backed scenario to disk and shells out to the unmodified root
`driver.py`/`render.sh` (see [FR-CLI-*](./cli-pipeline.md) and
`backend/app/render_pipeline.py`).

## FR-REND-001 — Start a render job

- **Priority:** Must
- **Statement:** A scenario author requests a render of a scenario with a
  chosen theme; the system creates a job and enqueues it for async
  processing rather than rendering inline.
- **Acceptance criteria:**
  - `POST /api/scenarios/{id}/render` with `{theme?}` (`theme` defaults to
    `"dracula"`).
  - `404` if the scenario doesn't exist; `400` if the scenario has zero
    steps (`"scenario has no steps to render"`).
  - A `RenderJob` row is created with `status=queued` and enqueued onto the
    RQ queue (`app.tasks.render_scenario_job`) before the response returns.

## FR-REND-002 — Render job status lifecycle

- **Priority:** Must
- **Statement:** A render job moves through a fixed set of statuses that
  reflect what stage of the pipeline it's in, and callers can observe the
  current status at any time.
- **Acceptance criteria:**
  - Statuses: `queued` → `running` → (`done` | `failed`); no other
    transitions exist (`JobStatus` enum).
  - `started_at` is set when the worker picks the job up; `finished_at` is
    set on both `done` and `failed`.

## FR-REND-003 — Isolated per-job workspace

- **Priority:** Must
- **Statement:** Rendering a scenario never mutates the scenario's shared
  source directory in place; each render job gets its own copy so
  concurrent renders of the same scenario cannot clobber each other.
- **Acceptance criteria:**
  - The worker copies `docker.mount_host_path` (or the repo-root
    `demo-repo/` fallback if the configured path is missing) into
    `backend/data/workspaces/<job_id>/` before invoking `driver.py`.
  - The materialized scenario YAML's `docker.mount_host_path` points at
    this per-job workspace, and `docker.container_name` is suffixed with
    the job ID, so concurrent jobs never collide on a container name either.
  - `write_file` steps with inline `content` (not `content_file`) are
    spilled to `<workspace>/_step_content/step_<i>_<basename>` before the
    scenario YAML is written, since `driver.py` only understands
    `content_file`.

## FR-REND-004 — Run the pipeline and capture output

- **Priority:** Must
- **Statement:** A queued render job runs `driver.py` to produce a `.cast`
  recording, then `render.sh` to produce the themed `.gif`/`.mp4`,
  streaming stdout/stderr from both — including the in-container session
  itself — to `job.log` as it's produced, for diagnosis.
- **Acceptance criteria:**
  - `driver.py` is invoked with the job's own venv Python
    (`REPO_ROOT/.venv/bin/python3`, falling back to `python3` on PATH,
    always with `-u` for unbuffered output) and the materialized YAML.
  - `render.sh` is invoked with the resulting `.cast`, an output basename,
    and the job's theme.
  - Combined stdout/stderr from both invocations is streamed line-by-line
    to `job.log` (`render_pipeline.py::_run_streaming`, `subprocess.Popen`
    rather than a buffered `subprocess.run`), prefixed with the command
    line that produced it, regardless of success or failure.
  - `driver.py` mirrors the pty content of its `pexpect` child
    (`child.logfile_read = sys.stdout`) to its own stdout, so the
    interactive container session — typed commands and their real output,
    not just infra-level docker/render.sh output — flows through the same
    capture path. This stays within
    [NFR-002](../non-functional-and-constraints.md#nfr-002--backend-does-not-reimplement-the-cli-pipeline):
    the mirroring lives in `driver.py` itself, not duplicated in the backend.
  - ANSI/terminal control sequences are stripped (`render_pipeline.py::_ANSI_RE`)
    before storage, so `job.log` reads as plain text.

**Change note (2026-08-31, grill-me design session → implemented same day):**
previously, captured output was infra-level only (docker start/stop,
driver.py's own progress prints, agg/ffmpeg output) and fully buffered
until each subprocess exited — a scenario step that failed *inside* the
container produced no diagnosable log, and nothing was visible while a job
was still running. Both gaps are now closed (see `driver.py`,
`backend/app/render_pipeline.py`, [FR-REND-010](#fr-rend-010--render-log-streams-while-the-job-runs)).

## FR-REND-005 — Failure surfaces to the caller

- **Priority:** Must
- **Statement:** If either pipeline stage fails, the job is marked failed
  with a human-readable error and the captured log, rather than left
  hanging or silently discarded.
- **Acceptance criteria:**
  - `driver.py` exiting non-zero, or not producing a `.cast` file, fails
    the job with `"driver.py failed to record the session"`.
  - `render.sh` exiting non-zero, or not producing the final `.mp4`, fails
    the job with `"render.sh failed to produce a video"`.
  - Any other exception during the run (e.g. workspace materialization:
    bad YAML, missing scenario config keys, file-copy errors) is caught,
    surfaces as `"unexpected error: <exc>"` rather than crashing the worker
    process, and appends the full traceback (`traceback.format_exc()`) to
    `job.log` (`tasks.py::render_scenario_job`), so every failure path —
    not just the two named pipeline stages — ends up with detailed logs.

**Change note (2026-08-31, grill-me design session → implemented same day):**
the catch-all branch previously set `job.error` but never touched
`job.log`, so an unexpected failure lost all detail beyond the one-line
exception string. Closed same day — see `backend/app/tasks.py`.

## FR-REND-006 — List / get render jobs

- **Priority:** Must
- **Statement:** A scenario author lists every render job ever created for
  a scenario (newest first), or polls a single job by ID for its current
  status/output.
- **Acceptance criteria:**
  - `GET /api/scenarios/{id}/jobs` orders by `created_at desc`.
  - `GET /api/jobs/{id}` returns `404` if the job doesn't exist.
  - A `done` job's response includes `cast_url`/`gif_url`/`mp4_url`
    resolved under `/media` (`serialize.job_to_read`).

## FR-REND-007 — Client-side status polling

- **Priority:** Should
- **Statement:** While a job is `queued` or `running`, the UI keeps
  checking its status on an interval and stops once it reaches a terminal
  state, without requiring a manual refresh.
- **Acceptance criteria:**
  - `ScenarioCard` and the scenario editor poll `GET /api/jobs/{id}` (or
    the scenario's job list) via `refetchInterval`/`setInterval` only while
    `status` is `queued`/`running`.
  - There is no websocket or server-push channel; this is a deliberate,
    accepted trade-off at current scale (see `NFR-005`).

## FR-REND-008 — Render job timeout

- **Priority:** Should
- **Statement:** A render job that runs unreasonably long is terminated by
  the queue rather than blocking the worker indefinitely.
- **Acceptance criteria:**
  - Jobs are enqueued with `job_timeout=1800` (30 minutes) — see `NFR-006`.

## FR-REND-009 — Detailed render log available on demand

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; motivated by a single-line `job.error` on the scenario widget not
  being enough to diagnose a failed render — see
  [FR-REND-004](#fr-rend-004--run-the-pipeline-and-capture-output)/[FR-REND-005](#fr-rend-005--failure-surfaces-to-the-caller)).
- **Priority:** Should
- **Statement:** A scenario author viewing their **latest** render job for a
  scenario can open its full captured log on demand, not just the short
  error string, without that log being shipped as part of routine
  status-polling payloads.
- **Acceptance criteria:**
  - `GET /api/jobs/{job_id}/log` returns `job.log` as plain text (mirrors
    the existing `GET /api/scenarios/{id}/yaml` plain-text convention);
    `RenderJobRead`/`job_to_read` continue to omit `log` so the regularly
    polled `Scenario`/job payload stays small.
  - A "View logs" trigger (`frontend/src/components/app/JobLogDialog.tsx`,
    reusing `dialog.tsx`; a plain scrollable `<pre>` for the log body rather
    than `scroll-area.tsx`, matching the existing YAML-preview pattern) opens
    a dialog in both `ScenarioCard` and `ScenarioEditorPage`, scoped to
    `scenario.latest_job` only — no job-history browsing UI (the existing
    `GET /api/scenarios/{id}/jobs` list endpoint and `Jobs.get` binding stay
    unused for this feature, deliberately out of scope).
  - The dialog only fetches the log while it's actually open (not merely
    because a job exists), to avoid background polling nobody's watching.
- **Dependencies:** [FR-REND-004](#fr-rend-004--run-the-pipeline-and-capture-output),
  [FR-REND-005](#fr-rend-005--failure-surfaces-to-the-caller) (what ends up
  in `job.log` in the first place).

## FR-REND-010 — Render log streams while the job runs

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build).
- **Priority:** Should
- **Statement:** While a job is `queued`/`running`, an open log dialog shows
  the log growing in near-real-time rather than only revealing content once
  the job reaches a terminal state.
- **Acceptance criteria:**
  - `render_pipeline.py` invokes `driver.py`/`render.sh` via `Popen` with
    incremental line reads instead of `subprocess.run(capture_output=True)`
    (which buffers everything until process exit), calling back into the
    caller with each new (ANSI-stripped) chunk as it arrives.
  - `tasks.py::render_scenario_job` appends each chunk to `job.log`,
    committing to the DB throttled to roughly once per 0.5s rather than per
    line, so the DB isn't hammered by a fast-typing session.
  - The log dialog ([FR-REND-009](#fr-rend-009--detailed-render-log-available-on-demand))
    polls `GET /api/jobs/{job_id}/log` on the same ~2s cadence used
    elsewhere for job-status polling ([FR-REND-007](#fr-rend-007--client-side-status-polling))
    while it is open and the job is `queued`/`running`, and stops polling
    once the job reaches a terminal status.
- **Dependencies:** [FR-REND-004](#fr-rend-004--run-the-pipeline-and-capture-output)
  (streaming replaces its buffered capture mechanism),
  [FR-REND-009](#fr-rend-009--detailed-render-log-available-on-demand) (the
  endpoint being polled).
