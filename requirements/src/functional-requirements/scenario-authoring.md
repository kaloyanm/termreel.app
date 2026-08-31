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

- **Priority:** Must
- **Statement:** A scenario declares which Docker image the recording runs
  in and which host directory is mounted into the container as the
  episode's source tree.
- **Acceptance criteria:**
  - `docker.image` and `docker.container_name` are required.
  - `docker.mount_host_path` defaults to `./demo-repo`;
    `docker.mount_container_path` defaults to `/repo`.
  - `docker.workdir` is optional (falls back to `mount_container_path` at
    record time — see [FR-CLI-002](./cli-pipeline.md#fr-cli-002--start-and-tear-down-the-container)).

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
