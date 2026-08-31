# Scenario authoring & export (`FR-EDIT-*`)

Scenario content (`docker` / `typing` / `steps`) is stored in the DB in the
exact shape of `scenario.example.yaml`, so it round-trips to a YAML file
`driver.py` can consume unchanged — see
[Non-functional requirements & constraints](../non-functional-and-constraints.md).

## FR-EDIT-001 — Step schema validation

- **Priority:** Must
- **Statement:** Each step an author writes is one of three types, each
  with its own required fields; the system rejects a step missing its
  required fields before it is ever persisted.
- **Acceptance criteria:**
  - `type: command` and `type: comment` steps require non-empty `text`.
  - `type: write_file` steps require `path`, and require **either**
    `content` (inline) **or** `content_file` (path to a file on the
    filesystem the driver runs against).
  - A step failing these rules is rejected with a `422` on
    `POST`/`PUT` (Pydantic `model_validator` on `ScenarioStep`), before it
    reaches the database.
  - Every step optionally carries `pause_after` (seconds to wait after the
    step, overriding `typing.default_pause_after`).

## FR-EDIT-002 — Docker environment config

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; see [Changelog](../changelog.md)). Supersedes the original
  free-text `docker.image` design captured in the 2026-08-30 baseline.
- **Priority:** Must
- **Statement:** A scenario declares which **Flavour** — a named, pre-built
  Docker environment with its own Dockerfile — the recording runs in, and
  which host directory is mounted into the container as the episode's
  source tree. Flavours are authored in advance (by whoever maintains the
  repo, not scenario authors) under `flavours/`; a scenario picks one by id
  from a fixed catalog rather than typing a raw image reference.
- **Acceptance criteria:**
  - `docker.flavour` (a flavour id, e.g. `"rust"`) and
    `docker.container_name` are required. The free-text `docker.image`
    field no longer exists — this is a full replacement, not an additive
    option (no dual-field back-compat; the app has no real user base or
    migration tooling to protect).
  - `docker.flavour` is validated against the flavour catalog
    ([FR-EDIT-008](#fr-edit-008--flavour-catalog-for-scenario-authoring)) on
    `POST`/`PUT`; an unknown id is rejected with `422`, before it reaches
    the database.
  - `docker.mount_host_path` defaults to `./demo-repo`;
    `docker.mount_container_path` defaults to `/repo`.
  - `docker.workdir` is optional (falls back to `mount_container_path` at
    record time — see [FR-CLI-002](./cli-pipeline.md#fr-cli-002--start-and-tear-down-the-container)).
- **Dependencies:** [FR-EDIT-008](#fr-edit-008--flavour-catalog-for-scenario-authoring),
  [FR-CLI-012](./cli-pipeline.md#fr-cli-012--flavour-resolution-and-build-on-demand).

## FR-EDIT-003 — Typing style config

- **Priority:** Should
- **Statement:** A scenario declares how "human" the simulated typing
  looks: base speed, timing jitter, and the default pause after a step.
- **Acceptance criteria:**
  - `typing.base_cps` (characters/sec), `typing.jitter_pct`, and
    `typing.default_pause_after` are all optional with defaults `14`,
    `0.35`, `1.5` respectively.

## FR-EDIT-004 — Export scenario as YAML

- **Priority:** Must
- **Statement:** A scenario author can export any stored scenario as a YAML
  document in the exact schema `driver.py` expects, byte-for-byte
  equivalent to what would be hand-written for the CLI pipeline.
- **Acceptance criteria:**
  - `GET /api/scenarios/{id}/yaml` returns `text/plain` YAML with keys
    `title`, `docker`, `typing`, `steps` in that order
    (`yaml.safe_dump(..., sort_keys=False)`).
  - The frontend's scenario-editor YAML preview tab renders this same
    format **client-side** via `js-yaml` and must match the backend output
    exactly (`ScenarioEditorPage`) — a discrepancy between the two is a
    defect, not an acceptable divergence.
- **Dependencies:** [FR-CLI-001](./cli-pipeline.md#fr-cli-001--author-a-scenario-file).

## FR-EDIT-005 — write_vim step schema

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; see [Changelog](../changelog.md)).
- **Priority:** Should
- **Statement:** A fourth step type, `write_vim`, is authorable with the
  same `path` + (`content` or `content_file`) shape as `write_file`, plus
  two step-local booleans controlling how the recording behaves.
- **Acceptance criteria:**
  - `type: write_vim` steps are validated with the same required-field
    rule as `write_file` ([FR-EDIT-001](#fr-edit-001--step-schema-validation)):
    `path` required, and either `content` or `content_file` required.
  - Two additional optional booleans, both defaulting `false`:
    `simulate_typos` (drives [FR-CLI-011](./cli-pipeline.md#fr-cli-011--typo-simulation-for-write_vim));
    `force_blank` (forces [FR-CLI-009](./cli-pipeline.md#fr-cli-009--write_vim-step-blank-mode)
    even when a file already exists at `path`, instead of the diff-mode
    default in [FR-CLI-010](./cli-pipeline.md#fr-cli-010--write_vim-step-diffliveedit-mode)).
- **Dependencies:** [FR-CLI-009](./cli-pipeline.md#fr-cli-009--write_vim-step-blank-mode)–[FR-CLI-011](./cli-pipeline.md#fr-cli-011--typo-simulation-for-write_vim).

## FR-EDIT-006 — Upload a file to seed step content

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; see [Changelog](../changelog.md)).
- **Priority:** Could
- **Statement:** Authoring a `write_file` or `write_vim` step, an author can
  populate the step's `content` from a local file instead of typing/pasting
  it into the textarea.
- **Acceptance criteria:**
  - An "Upload file" control (client-side `FileReader.readAsText`, no
    backend involvement) sets `content` to the uploaded file's text; if the
    step's `path` is still empty, it's filled from the uploaded file's name.
  - Available for both `write_file` and `write_vim` steps, since they share
    the same path/content field block in the step editor.

## FR-EDIT-007 — Typing-time guardrail on write_vim content

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; see [Changelog](../changelog.md)).
- **Priority:** Should
- **Statement:** Saving a scenario is rejected if a `write_vim` step's
  content would take an unreasonably long time to type at the scenario's
  configured typing speed, so an author can't accidentally queue a
  multi-minute render without a clear signal at save time.
- **Acceptance criteria:**
  - Estimated typing time is `len(content) / typing.base_cps` seconds;
    scenario create/update is rejected with `422` if any `write_vim` step's
    estimate exceeds 60s, naming the offending step and its estimate.
  - The check uses `content` length as a valid upper bound for both
    write_vim modes ([FR-CLI-009](./cli-pipeline.md#fr-cli-009--write_vim-step-blank-mode)/[FR-CLI-010](./cli-pipeline.md#fr-cli-010--write_vim-step-diffliveedit-mode)) —
    diff mode's deletions are instant vim commands, not human-typed, and its
    insertions are always a subset of `content`.
  - Enforced where the *effective* `steps`/`typing` are known (after
    merging a partial `ScenarioUpdate` payload onto the existing DB row),
    not as a bare per-step Pydantic validator, since a step alone has no
    access to the sibling `typing` config and an update payload may omit
    `typing` entirely.
  - A step authored with only `content_file` (no inline `content`) has
    nothing to measure at save time and is skipped by this check.

## FR-EDIT-008 — Flavour catalog for scenario authoring

- **Status:** Implemented 2026-08-31 (grill-me design session, same-day
  build; see [Changelog](../changelog.md)).
- **Priority:** Must
- **Statement:** The set of available Flavours is discoverable so the
  scenario editor can offer a dropdown instead of a free-text image field,
  and so the backend can validate a scenario's `docker.flavour` against
  something real.
- **Acceptance criteria:**
  - `GET /api/flavours` returns the catalog read from `flavours/flavours.yaml`
    (repo root): each entry has `id`, `display_name`, and the Dockerfile
    path it builds from; an optional `description`.
  - The frontend fetches this list once and joins it client-side wherever a
    flavour needs a human-readable label — `NewScenarioDialog` (create-time
    picker, defaulting to the catalog's first entry),
    `ScenarioEditorPage` (environment tab), and `ScenarioCard` (read-only
    display on the playlist grid). The `Scenario` API response itself does
    **not** carry a denormalized display name.
  - Adding a new flavour is a new `flavours/<id>/Dockerfile` plus one
    manifest entry — no DB migration, no code change to the catalog
    endpoint.
- **Dependencies:** [FR-CLI-012](./cli-pipeline.md#fr-cli-012--flavour-resolution-and-build-on-demand)
  (same manifest is the source of truth for both the catalog endpoint and
  the build step).
