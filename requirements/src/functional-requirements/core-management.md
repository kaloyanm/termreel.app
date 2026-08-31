# Project / playlist / scenario management (`FR-CORE-*`)

Projects → Playlists → Scenarios is a strict three-level hierarchy; deletion
cascades top-down. There is no cross-linking (a scenario belongs to exactly
one playlist, a playlist to exactly one project).

## FR-CORE-001 — Create project

- **Priority:** Must
- **Statement:** A scenario author creates a project by supplying a name
  and an optional description; the system returns the new project with a
  generated ID and creation timestamp.
- **Acceptance criteria:**
  - `POST /api/projects` with `{name, description?}` returns `201` and the
    created project.
  - `description` defaults to `""` when omitted.
  - `playlist_count` on the response starts at `0`.

## FR-CORE-002 — List / get projects

- **Priority:** Must
- **Statement:** A scenario author lists all projects, or fetches one by ID.
- **Acceptance criteria:**
  - `GET /api/projects` returns all projects with each one's live
    `playlist_count`.
  - `GET /api/projects/{id}` returns `404` if the project does not exist.

## FR-CORE-003 — Update project

- **Priority:** Must
- **Statement:** A scenario author edits a project's name and/or
  description independently.
- **Acceptance criteria:**
  - `PATCH /api/projects/{id}` accepts a partial body; only supplied fields
    change.
  - `404` if the project does not exist.

## FR-CORE-004 — Delete project (cascades)

- **Priority:** Must
- **Statement:** Deleting a project deletes every playlist inside it, and
  every scenario and render job inside those playlists.
- **Acceptance criteria:**
  - `DELETE /api/projects/{id}` returns `204`.
  - No orphaned `Playlist`, `Scenario`, or `RenderJob` rows remain
    (`cascade="all, delete-orphan"` on both hierarchy levels).
  - Rendered media files on disk for cascaded jobs are **not** automatically
    cleaned up (see `NFR-004` in
    [Non-functional requirements & constraints](../non-functional-and-constraints.md)).

## FR-CORE-010 — Create playlist within a project

- **Priority:** Must
- **Statement:** A scenario author creates a playlist inside a specific
  project by name (+ optional description).
- **Acceptance criteria:**
  - `POST /api/projects/{project_id}/playlists` returns `404` if the parent
    project doesn't exist, else `201` with the created playlist.

## FR-CORE-011 — List / get playlists

- **Priority:** Must
- **Statement:** A scenario author lists playlists within a project, or
  fetches one playlist by ID directly.
- **Acceptance criteria:**
  - `GET /api/projects/{project_id}/playlists` returns `404` if the project
    doesn't exist.
  - `GET /api/playlists/{id}` returns each playlist's live
    `scenario_count`.

## FR-CORE-012 — Update / delete playlist

- **Priority:** Must
- **Statement:** A scenario author edits a playlist's name/description, or
  deletes it (cascading to its scenarios and their render jobs).
- **Acceptance criteria:**
  - `PATCH` / `DELETE /api/playlists/{id}` both `404` on a missing playlist.
  - Delete cascades per `sa_relationship_kwargs={"cascade": "all,
    delete-orphan"}` on `Playlist.scenarios`.

## FR-CORE-020 — Create scenario within a playlist

- **Priority:** Must
- **Statement:** A scenario author creates a scenario inside a playlist by
  supplying a title, a Docker config, an optional typing config, and an
  ordered list of steps.
- **Acceptance criteria:**
  - `POST /api/playlists/{playlist_id}/scenarios` returns `404` if the
    parent playlist doesn't exist.
  - Request body is validated against `ScenarioCreate` — see
    [FR-EDIT-001](./scenario-authoring.md#fr-edit-001--step-schema-validation)
    for per-step rules.
  - `typing` defaults to `{base_cps: 14, jitter_pct: 0.35,
    default_pause_after: 1.5}` when omitted.
- **Dependencies:** [FR-EDIT-001](./scenario-authoring.md#fr-edit-001--step-schema-validation).

## FR-CORE-021 — List / get scenarios

- **Priority:** Must
- **Statement:** A scenario author lists scenarios within a playlist, or
  fetches one scenario by ID; both include the scenario's most recent
  render job, if any.
- **Acceptance criteria:**
  - `GET /api/playlists/{playlist_id}/scenarios` and
    `GET /api/scenarios/{id}` responses embed `latest_job`
    (see [FR-REND-006](./render-pipeline.md#fr-rend-006--list--get-render-jobs)).

## FR-CORE-022 — Update scenario

- **Priority:** Must
- **Statement:** A scenario author edits a scenario's title, Docker config,
  typing config, and/or steps independently; each field is validated on
  write against the same schema as creation.
- **Acceptance criteria:**
  - `PUT /api/scenarios/{id}` accepts a partial body (any subset of
    `title`/`docker`/`typing`/`steps`); only supplied fields change.
  - `updated_at` is refreshed on every successful update.
  - `404` if the scenario does not exist.

## FR-CORE-023 — Delete scenario (cascades)

- **Priority:** Must
- **Statement:** Deleting a scenario deletes every render job created from
  it.
- **Acceptance criteria:**
  - `DELETE /api/scenarios/{id}` returns `204`.
  - No orphaned `RenderJob` rows remain (`Scenario.jobs` cascade).
