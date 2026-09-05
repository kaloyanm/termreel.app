# Termreel: Project Overview & Product Development Requirements

## What is Termreel?

Termreel is a tool for creating professional "automated coding session" videos — think of it as a scenario-driven screencast recorder that automates the typing and command execution in a real Docker container, then renders the terminal session to video. It's useful for creating tutorial content, demos, and educational videos where the narrative is predetermined but the execution must be genuine.

## Core Use Cases

1. **Tutorial content**: A creator authors a scenario describing what code to type and what commands to run, the tool records the terminal session in a real Docker container, and produces a clean MP4/GIF for editing and voiceover.
2. **Live-coding demos**: Present reproducible coding walkthroughs without the latency or typing errors of true live sessions.
3. **Technical documentation**: Embed automatically-generated terminal walkthroughs into docs or product pages (e.g. "getting started" guides).

## Two-Layer Architecture

Termreel has two distinct layers:

### Layer 1: CLI Recording Pipeline (Root `driver.py` + `render.sh`)

A standalone, Python-based tool that takes a scenario YAML file and automates terminal interaction in a Docker container:

- **Scenario format**: YAML file describing the steps (commands, comments, file writes, vim editing, or presentation slides) that happen in sequence.
- **Recording**: Starts a Docker container, execs into it via `asciinema` (structured terminal recording), types each step with configurable timing and optional typo simulation, then records the full terminal session to an asciinema `.cast` file.
- **Rendering**: Converts the `.cast` file to MP4 and GIF using `agg` and `ffmpeg`, with configurable theme and playback speed.
- **No dependencies on the web app**: This layer works standalone via the command line and requires only `docker`, `asciinema`, `agg`, `ffmpeg` on the host PATH.

### Layer 2: Web Application (Backend + Frontend)

A full-stack web UI that wraps the CLI pipeline, adding:

- **Project/Playlist/Scenario management**: Scenarios are authored in a browser-based editor and organized into playlists and projects instead of hand-edited YAML.
- **Async render queue**: Renders are queued via RQ (Redis Queue) and processed in the background; the UI polls for job status and downloads the rendered media.
- **Database persistence**: SQLite (SQLModel ORM) stores the project hierarchy with cascade delete semantics.
- **Interactive editor**: Form-based UI for configuring steps, environment variables, typing parameters, and Docker flavours.

**Key invariant:** The backend's `render_pipeline.py` shells out to the *unmodified* root `driver.py`/`render.sh` rather than reimplementing the recording/rendering logic. Any fix to core recording or rendering behavior belongs in the CLI layer.

## Product Scope

### In Scope (Implemented)

- [x] Project/Playlist/Scenario CRUD with cascade delete
- [x] Interactive scenario authoring (form UI)
- [x] Step types: `command`, `comment`, `write_file`, `write_vim`, `presenterm`
- [x] YAML export (matches the CLI pipeline's format exactly)
- [x] Async render queue with job-status polling
- [x] Detailed render logs (streamed while the job runs)
- [x] Docker flavours (pre-built environments like "Rust")
- [x] Flavour-aware scenario validation
- [x] Typing-time guardrail (reject `write_vim` steps too long to type in ~60s)
- [x] Marketing site (Landing page + Use Cases page)
- [x] Local dev stack (`./dev.sh` start all services)

### Not in Scope / Open Decisions

- **Authentication**: Currently a single-operator tool with no auth or user model. Every project, playlist, and scenario is globally readable and writable. Whether to add user accounts and access control is an open product decision.
- **Media cleanup on cascade delete**: Deleting a project cascades the database rows but does not delete the corresponding rendered media files on disk under `backend/data/media/`. This is current behavior, not an explicit design goal. Cascade deletion of media on disk is a candidate for a future feature if disk usage becomes a concern.
- **Push notifications**: Status updates use client-side polling (every 2 seconds), not websockets or Server-Sent Events. This is acceptable for the current single-operator, single-job-at-a-time workload. Revisit if concurrent-job volume grows enough to make polling inefficient.

## Glossary

| Term | Meaning |
|---|---|
| **Scenario** | One "episode": a title, a Docker config, a typing config, and an ordered list of steps. Stored as a DB row in the web app; a YAML file in the CLI pipeline. |
| **Step** | One unit of on-screen action: `command`, `comment`, `write_file`, `write_vim`, or `presenterm`. |
| **Render job** | One request to turn a scenario into a `.cast` recording and then a `.gif`/`.mp4`. Has its own lifecycle independent of the scenario it was created from. |
| **Cast file** | An asciinema recording: structured terminal events (timing + text), not pixels — enables re-rendering with a different theme/font without re-running the container. |
| **Workspace** | A per-render-job filesystem directory, copied from the scenario's `docker.mount_host_path`, that isolates concurrent renders of the same scenario from each other. |
| **Flavour** | A named, pre-built Docker environment (a Dockerfile under `flavours/`, e.g. "Rust") that a scenario selects by id (`docker.flavour`) instead of a free-text image reference. Authored in advance by whoever maintains the repo, not by scenario authors. |

## Definitively Out of Scope

- **Post-production** (voiceover, music, captions, intro/outro) — explicitly left to an external video editor.
- **Mid-recording error recovery** — if a command hangs inside the container, the render hangs; there is no per-step timeout or skip/abort path today.
- **Narration/audio timing sync** — `pause_after` values are set manually; no automatic sync logic exists.

## Target Audience

- **Content creators**: Educators, technical bloggers, and tutorial producers who want high-quality terminal recordings with exact reproducibility.
- **DevTools maintainers**: Projects that want to generate "getting started" walkthroughs as part of their documentation pipeline.
- **Solo operators**: The single-operator / no-auth posture fits a self-hosted or personal-use scenario.

## Success Metrics (High-Level)

1. **Scenario fidelity**: A scenario recorded twice produces identical output (determinism).
2. **Developer velocity**: A creator can author and render a scenario in under 5 minutes per minute of video content (subjective, based on feedback).
3. **Code quality**: Step types are extensible; new types can be added to `driver.py`'s `do_step()` dispatcher without breaking existing scenarios.
4. **Reliability**: Render failures are diagnosed via detailed logs; no silent failures.

## System Constraints

- **External tool requirements**: The full stack requires `docker`, `asciinema`, `agg`, `ffmpeg`, `redis-server`, `uv`, and `bun` on PATH. None are vendored or containerized. Failure to locate any is a hard error.
- **Render timeout**: Jobs are enqueued with a 30-minute timeout. Scenarios requiring longer than 30 minutes will be killed mid-render with no partial-result recovery.
- **Separate uv projects**: Root `pyproject.toml` and `backend/pyproject.toml` are deliberately separate uv projects with independent `.venv`s/lockfiles, never merged into a workspace. A shared workspace was tested and caused dependency conflicts.
- **Data layout**: All persistent data (`backend/data/` — SQLite DB, media, workspaces) is gitignored and untracked. Nothing is expected to survive a fresh checkout without re-rendering.

## Key Implementation Decisions

1. **Step types via dispatcher**: New step types are added as branches in `driver.py`'s `do_step()` function, keeping logic close to execution.
2. **Flavour resolution in CLI**: Docker flavour build/resolution lives in the CLI pipeline (`driver.py`), not the backend, preserving standalone CLI usability.
3. **Cascade-first DB design**: Project → Playlist → Scenario → RenderJob form a strict hierarchy with cascade delete at every level; no orphaned records by design.
4. **Polling-only status**: Frontend polls job status via `GET /api/jobs/{id}` on an interval; no websockets.
5. **Exact YAML format preservation**: The backend's YAML export (`GET /scenarios/{id}/yaml`) is shaped exactly like the CLI pipeline's input format for perfect round-tripping.

## For More Detail

- **Architecture details**: See [System Architecture](./system-architecture.md) for data flow diagrams, component interactions, and the render_pipeline.py bridge.
- **Code structure**: See [Codebase Summary](./codebase-summary.md) for directory-by-directory layout and module responsibilities.
- **Code standards**: See [Code Standards & Structure](./code-standards.md) for coding conventions, patterns, and extensibility points.
- **Developer setup**: See [Deployment Guide](./deployment-guide.md) for local dev (`./dev.sh`) and production deployment (docker-compose).
- **Roadmap and open questions**: See [Project Roadmap](./project-roadmap.md) for candidate features and blocking decisions.
