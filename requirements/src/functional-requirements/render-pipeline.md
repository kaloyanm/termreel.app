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
  capturing full stdout/stderr from both for diagnosis.
- **Acceptance criteria:**
  - `driver.py` is invoked with the job's own venv Python
    (`REPO_ROOT/.venv/bin/python3`, falling back to `python3` on PATH) and
    the materialized YAML.
  - `render.sh` is invoked with the resulting `.cast`, an output basename,
    and the job's theme.
  - Combined stdout/stderr from both invocations is appended to `job.log`,
    prefixed with the command line that produced it, regardless of
    success or failure.

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
  - Any other exception during the run is caught and surfaces as
    `"unexpected error: <exc>"` rather than crashing the worker process.

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
