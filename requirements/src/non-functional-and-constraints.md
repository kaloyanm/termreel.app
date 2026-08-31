# Non-functional requirements & constraints

## NFR-001 — No auth / single-operator tool

Every project/playlist/scenario/job is globally readable and writable; there
is no user model, session, or permission check anywhere in `backend/app/`.
Any FR implying "the author" does something implicitly means "whoever can
reach the API/UI." Treat introducing accounts as a breaking architectural
change, not an incremental FR.

## NFR-002 — Backend does not reimplement the CLI pipeline

**This is a repo-level invariant, not a preference:** `render_pipeline.py`
must shell out to the unmodified root `driver.py`/`render.sh` rather than
duplicating their recording/rendering logic. Any fix to recording/rendering
behavior belongs in `driver.py`/`render.sh`; a PR that reimplements pieces
of it in the backend is out of policy regardless of the FR it's serving.
Bounds: [FR-REND-004](./functional-requirements/render-pipeline.md#fr-rend-004--run-the-pipeline-and-capture-output).

## NFR-003 — Root and backend are separate uv projects

`pyproject.toml` (root) and `backend/pyproject.toml` are deliberately
separate uv projects with independent `.venv`s/lockfiles — a shared
`[tool.uv.workspace]` was tried and caused the two projects' dependencies to
clobber each other in one venv. Do not reintroduce a workspace.

## NFR-004 — Cascade deletes do not clean up media on disk

Deleting a project/playlist/scenario cascades the DB rows
([FR-CORE-004](./functional-requirements/core-management.md#fr-core-004--delete-project-cascades),
[FR-CORE-012](./functional-requirements/core-management.md#fr-core-012--update--delete-playlist),
[FR-CORE-023](./functional-requirements/core-management.md#fr-core-023--delete-scenario-cascades))
but does not delete the corresponding `backend/data/media/<job_id>/` or
`backend/data/workspaces/<job_id>/` directories. This is current behavior,
not a stated design goal — flag it as a candidate FR if disk usage becomes a
problem (see open question in [Changelog](./changelog.md)).

## NFR-005 — Status polling only, no push channel

The frontend polls `GET /api/jobs/{id}` on an interval
([FR-REND-007](./functional-requirements/render-pipeline.md#fr-rend-007--client-side-status-polling))
rather than receiving a websocket/SSE push. Acceptable at current scale
(single operator, low job concurrency); revisit if concurrent-job volume
grows.

## NFR-006 — Render job timeout: 30 minutes

Jobs are enqueued with RQ `job_timeout=1800`
([FR-REND-008](./functional-requirements/render-pipeline.md#fr-rend-008--render-job-timeout)).
A scenario whose recording legitimately needs longer than 30 minutes will be
killed mid-render with no partial-result recovery.

## NFR-007 — External tool dependencies

The full stack requires, on `PATH` / running: `docker`, `asciinema`, `agg`,
`ffmpeg`, `redis-server`, plus `uv` (backend) and `bun` (frontend). None of
these are vendored or containerized for the app itself — `./dev.sh` assumes
they're already installed on the host.

## NFR-008 — Data storage layout

`backend/data/` (SQLite DB, `media/`, `workspaces/`) is gitignored and
untracked; nothing in the render pipeline is expected to survive a fresh
checkout without re-rendering.
