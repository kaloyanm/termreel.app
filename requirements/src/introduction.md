# Introduction

## Scope

termreel generates "automated coding session" videos: a scenario (a title, a
Docker environment, and an ordered list of terminal steps) is driven into a
real Docker container, recorded with `asciinema`, and rendered to a themed
GIF/MP4 with `agg` + `ffmpeg`.

The product is two layers over the same pipeline:

- **CLI pipeline** (`driver.py` + `render.sh`, repo root) — hand-edit a
  scenario YAML file, record, render. Standalone, no web app required.
- **Web app "termreel"** (`backend/` + `frontend/`) — the same pipeline
  wrapped behind Projects → Playlists → Scenarios, a browser-based scenario
  editor, and an async render queue. It shells out to the *unmodified* root
  `driver.py`/`render.sh` rather than reimplementing them — see
  [Non-functional requirements & constraints](./non-functional-and-constraints.md).

## Release / product focus

This baseline documents the **current, working state of the repository**
(brownfield capture), not a forward-looking roadmap. It exists so future
feature discussions have a stable set of FR IDs to extend, supersede, or
deprecate rather than starting from a blank page.

## Audience

- Whoever is extending termreel (adding step types, editor features, queue
  behavior).
- Anyone authoring scenario content, whether through the CLI YAML files or
  the web editor.

## Glossary

| Term | Meaning |
|---|---|
| Scenario | One "episode": a title, a `docker` config, a `typing` config, and an ordered list of `steps`. Stored as a DB row in the web app; a YAML file in the CLI pipeline. |
| Step | One unit of on-screen action: `command`, `comment`, or `write_file`. |
| Render job | One request to turn a scenario into a `.cast` recording and then a `.gif`/`.mp4`. Has its own lifecycle independent of the scenario it was created from. |
| Cast file | An `asciinema` recording: structured terminal events (timing + text), not pixels — enables re-rendering with a different theme/font without re-running the container. |
| Workspace | A per-render-job filesystem directory, copied from the scenario's `docker.mount_host_path`, that isolates concurrent renders of the same scenario from each other. |
| Flavour | A named, pre-built Docker environment (a Dockerfile under `flavours/`, e.g. "Rust") that a scenario selects by id (`docker.flavour`) instead of a free-text image reference. Authored in advance by whoever maintains the repo, not by scenario authors. |

## Out of scope

- **Authentication / authorization / multi-tenancy.** There is no user
  model anywhere in the schema; every project/playlist/scenario is globally
  visible and mutable. Treat as a single-operator local tool unless a future
  FR introduces accounts.
- **Post-production** (voiceover, music, captions, intro/outro) — explicitly
  left to an external video editor per the README.
- **Mid-recording error recovery.** If a command hangs inside the container,
  `driver.py` hangs; there is no per-step timeout or skip/abort path today.
- **Narration/audio timing sync** — `pause_after` values are set manually;
  no automatic sync logic exists.
