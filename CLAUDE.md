# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repo is two layers:

1. **CLI pipeline** (root-level `driver.py` + `render.sh`): scenario YAML → real Docker container → asciinema recording → agg/ffmpeg render. Standalone, no web app required.
2. **Web app "termreel"** (`backend/` + `frontend/`): wraps #1 behind projects/playlists and an interactive scenario editor.

The key invariant: `backend/app/render_pipeline.py` shells out to the *unmodified* root `driver.py`/`render.sh` rather than reimplementing them. Keep it that way — any fix to the recording/rendering behavior belongs in `driver.py`/`render.sh`, not duplicated in the backend.

## Commands

**Backend** (`cd backend`):
- `uv sync` — install deps
- `uv run uvicorn app.main:app --reload --port 8000` — run the API
- `uv run python -m app.worker` — run the RQ render worker (needs `redis-server` running)
- `uv run pytest` — run tests; single test: `uv run pytest tests/test_api.py::test_name`

**Frontend** (`cd frontend`):
- `bun install`
- `bun run dev` — dev server; proxies `/api` and `/media` to `127.0.0.1:8000` (see `vite.config.ts`)
- `bun run build` — typecheck + build (`tsc -b && vite build`)
- `bun run lint` — oxlint

**Whole stack**: `./dev.sh` from repo root — starts redis (if not already running), the API, the worker, and the frontend together.

**CLI pipeline standalone** (root `uv sync` first): `python3 driver.py scenario.example.yaml --out session.cast` then `./render.sh session.cast episode01 dracula`. Requires `docker`, `asciinema`, `agg`, `ffmpeg` on PATH.

Root `pyproject.toml` and `backend/pyproject.toml` are deliberately separate uv projects with independent `.venv`s/lockfiles, not a uv workspace — a shared workspace was tried and caused the two projects' dependencies to clobber each other in one venv. Don't reintroduce `[tool.uv.workspace]`.

## Architecture

**`driver.py` / `render.sh`** (root) — the recording/render pipeline. `do_step()` in `driver.py` is the step-type dispatcher (`command` / `comment` / `write_file` / `write_vim`); extend here for new step types. Comment steps are wrapped with `textwrap` before typing, and containers are exec'd with `LC_ALL=C.UTF-8` — base images ship with no locale configured, and without one bash's readline miscomputes cursor position for multi-byte text (e.g. Cyrillic), corrupting the terminal display on line wrap. `write_vim` opens vim and types content into it (blank-buffer, or diff-driven against the container's current file via `docker exec ... cat`); indentation is left to vim's own autoindent, a deliberate best-effort trade-off — see `requirements/src/functional-requirements/cli-pipeline.md` (FR-CLI-009..011).

**`backend/app/`** — FastAPI + SQLModel (SQLite) + RQ.
- `models.py`: `Project` → `Playlist` → `Scenario` → `RenderJob`, cascade-deleted top-down. `Scenario.docker`/`typing`/`steps` are JSON columns shaped exactly like `scenario.example.yaml`.
- `render_pipeline.py`: the bridge — materializes a `Scenario` row into a real scenario YAML file plus an isolated per-job workspace dir (copied from `docker.mount_host_path`, defaulting to `demo-repo/`), then shells out to the root `driver.py` and `render.sh`. `write_file`/`write_vim` step content is written to disk here so `driver.py` doesn't need to know about DB-backed content.
- `tasks.py` / `worker.py` / `queue.py`: the RQ job (`render_scenario_job`) that calls `render_pipeline.run_render` and updates `RenderJob` status; `worker.py` is the process entrypoint.
- `routers/`: one file per resource (`projects`, `playlists`, `scenarios`, `jobs`), all prefixed `/api`. `serialize.py` holds the shared DB-row → response-model conversion (`RenderJob` → URLs under `/media`, `Scenario` → includes `latest_job`).
- Rendered artefacts are served from `backend/data/media/` via `StaticFiles` at `/media`; `backend/data/` (db, media, workspaces) is gitignored.

**`frontend/src/`** — Bun + React + TS + shadcn/ui (Base UI-backed shadcn variant — components use the `render` prop for polymorphism, not Radix's `asChild`).
- `pages/`: `Landing` (marketing), `AppShell` (sidebar layout, wraps the rest via react-router `Outlet`), `ProjectsPage` / `ProjectPage` / `PlaylistPage` (CRUD browsers), `ScenarioEditorPage` (steps/environment/YAML-preview tabs; the YAML tab renders client-side via `js-yaml` and matches the backend's `/scenarios/{id}/yaml` output format exactly).
- `components/app/`: dialogs (`NewProjectDialog` etc.), `StepEditor` (per-step form for `command`/`comment`/`write_file`/`write_vim`), `ScenarioCard` (playlist grid card with live job-status polling).
- `lib/api.ts`: typed axios wrappers per resource; `types.ts` mirrors the backend Pydantic schemas by hand (kept in sync manually, no codegen).
- Render status is polled client-side (`refetchInterval` / `setInterval`) while a job is `queued`/`running` — there's no websocket/push.
