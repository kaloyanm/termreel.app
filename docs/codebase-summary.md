# Codebase Summary

This document provides a directory-by-directory map of the Termreel codebase, identifying module responsibilities and key files.

## Top-Level Structure

```
termreel.app/
├── root/              # CLI recording pipeline (standalone Python tool)
├── backend/           # FastAPI web application
├── frontend/          # React TypeScript UI
├── flavours/          # Pre-built Docker environments
├── docs/              # This documentation
└── [scripts]          # dev.sh, render.sh, docker-compose.yaml
```

## Root Layer: CLI Recording Pipeline

The CLI pipeline is a standalone Python tool that does not require the web app. It can be run independently via the command line.

### Core Files

- **`driver.py`** (main entry point)
  - Parses scenario YAML files
  - `do_step()`: dispatcher for 5 step types (command, comment, write_file, write_vim, presenterm)
  - `start_container()`: spawns Docker container, resolves flavour images
  - `run_command()`: shells out commands via pexpect PTY
  - `run_write_file()`: pastes file content via heredoc
  - `run_write_vim()`: types content into vim, supports diff-driven live-editing with optional typo simulation
  - `run_presenterm()`: pipes markdown to presenterm (full-screen slideshow), syncs synthetic terminal attributes
  - `resolve_flavour_image()`: builds/caches Docker flavours by tag
  - ~500 LOC, entry point: `python3 driver.py scenario.yaml --out session.cast`

- **`render.sh`** (post-processing script)
  - Converts asciinema `.cast` file to MP4 + GIF
  - Uses `agg` (cast → gif) then `ffmpeg` (gif → mp4)
  - Configurable theme and rendering parameters
  - Invoked by `render_pipeline.py` after recording completes

- **`scenario.example.yaml`**
  - Complete example scenario showing all step types
  - Docker flavour reference (currently `"rust"`)
  - Typing config (base_cps, jitter_pct)
  - Environment variables, pause timing

### Support Files

- **`pyproject.toml`** (root project deps)
  - Separate from `backend/pyproject.toml` (deliberately, to avoid dependency conflicts)
  - Contains: pexpect, pyyaml, docker (Python client), etc.
  - Run `uv sync` from repo root to install

## Backend Layer: FastAPI Web Application

The backend is a Python FastAPI + SQLModel + RQ application that wraps the CLI pipeline.

### Directory: `backend/app/`

#### Data Layer

- **`models.py`**: SQLModel ORM models
  - `Project` → `Playlist` → `Scenario` → `RenderJob` (strict hierarchy)
  - Cascade delete at every level; deleting a Project cascades all the way down
  - `Scenario.docker`, `Scenario.typing`, `Scenario.steps`: JSON columns shaped exactly like the CLI's YAML format
  - `RenderJob.status`: Enum (queued, running, done, failed)
  - `RenderJob.log`: Text field for streamed log output
  - All timestamps stored as UTC

- **`schemas.py`**: Pydantic request/response models
  - `ScenarioStep`: Union type for all 5 step types with per-type required fields
  - `ScenarioRead`: response includes `latest_job` (computed join)
  - `RenderJobRead`: response includes `/media/{path}` URLs for rendered artifacts
  - Model validators enforce step-type constraints (e.g., `write_vim` content length guardrail)

- **`db.py`**: SQLite setup
  - Creates `backend/data/db.sqlite`
  - Single connection per app, no connection pooling (single-operator tool)

#### Render Pipeline Bridge

- **`render_pipeline.py`**: The critical bridge from database to CLI
  - `run_render(job_id, scenario_title, docker_cfg, typing_cfg, steps, on_log, theme)`: main entry point
  - `_materialize_workspace()`: copies mount_host_path (or `demo-repo/`) into an isolated `WORKSPACES_DIR/{job_id}/` dir
  - `_materialize_scenario_yaml()`: writes inline `content` for write_file/write_vim/presenterm steps to disk as `content_file`, rewrites container/path refs, dumps final YAML
  - `_run_subprocess()`: shells out to `driver.py` and `render.sh`, streams stdout/stderr to DB via `on_log` callback
  - Raises `RenderError` on missing outputs or non-zero exit code
  - All workspace/media dirs are job-scoped; no global state

#### Job Queue (RQ)

- **`queue.py`**: RQ queue setup
  - Single queue named `"renders"` backed by Redis
  - Enqueues render jobs with `job_timeout=1800` (30 minutes)

- **`tasks.py`**: Job worker function
  - `render_scenario_job(job_id)`: fetches the job and scenario from DB, calls `render_pipeline.run_render()`, updates status to done/failed

- **`worker.py`**: RQ worker process entrypoint
  - Run via `python -m app.worker`
  - Requires Redis running on REDIS_URL (default localhost:6379)
  - Runs one job at a time (no concurrency)

#### API Routes

All routes prefixed `/api/`:

- **`routers/projects.py`**: `/api/projects`
  - POST (create), GET list/one, PATCH (update), DELETE (cascade)

- **`routers/playlists.py`**: `/api/projects/{projectId}/playlists`
  - Nested under projects; same CRUD operations

- **`routers/scenarios.py`**: `/api/playlists/{playlistId}/scenarios`
  - Nested under playlists
  - Validates `docker.flavour` against manifest at save time (422 on unknown)
  - GET `.../yaml` exports the driver.py-format YAML (must match frontend's client-side render)
  - Enforces `write_vim` typing-time guardrail (reject if content takes > 60s to type)

- **`routers/jobs.py`**: `/api/jobs`
  - POST `/{scenarioId}/render` enqueues a render
  - GET `/{jobId}` polls job status
  - GET `/{jobId}/log` streams plaintext log (no ANSI sequences)

- **`routers/flavours.py`**: `/api/flavours`
  - GET list of available flavours from `flavours/flavours.yaml` manifest
  - No CRUD (flavours are authored by maintainers, not via the app)

#### Serialization

- **`serialize.py`**: ORM → Pydantic converters
  - `project_to_read()`, `playlist_to_read()`, `scenario_to_read()`, `job_to_read()`
  - Maps stored relative paths (`media/job_123/...`) to public URLs (`/media/job_123/...`)
  - Computes `Scenario.latest_job` (join with RenderJob, sorted by creation date)

#### Core Application

- **`main.py`**: FastAPI app setup
  - Mounts StaticFiles at `/media` (rendered artifacts, gitignored `backend/data/media/`)
  - Conditionally mounts frontend SPA at `/` (only if `frontend/dist/` exists after production build)
  - Registers all routers
  - CORS middleware (default `*`)
  - OpenTelemetry instrumentation (appsignal APM)
  - Health check endpoint `/api/health`

- **`config.py`**: Configuration
  - `WORKSPACES_DIR`: `backend/data/workspaces/{job_id}`
  - `MEDIA_DIR`: `backend/data/media/`
  - `DB_PATH`: `backend/data/db.sqlite`
  - Read from env; defaults are all under `backend/data/` (gitignored)

### Directory: `backend/tests/`

- **`test_api.py`**: Complete API test suite (single file)
  - In-memory SQLite for each test
  - Covers CRUD flow (project → playlist → scenario → render)
  - Step validation (all 5 types, required fields)
  - Flavour validation
  - Typing-time guardrail
  - Render requires steps (not empty)
  - Run via `cd backend && uv run pytest`

### Configuration: `backend/pyproject.toml`

- Separate uv project from root (deliberate design)
- FastAPI, SQLModel, pydantic, redis, rq, uvicorn, pytest
- Run `uv sync` from `backend/` dir

## Frontend Layer: React TypeScript UI

The frontend is a React 19 + TanStack Query + react-router v7 + shadcn/ui SPA.

### Directory: `frontend/src/`

#### Routing & Pages

- **`main.tsx`**: App entry point
  - BrowserRouter, TanStack QueryClientProvider, theme provider
  - Mounts React app to `#root`

- **`pages/Landing.tsx`**: Marketing landing page (`/`)
  - Hero section, feature highlights, call-to-action
  - Uses `SiteHeader` / `SiteFooter` (shared marketing components)

- **`pages/UseCases.tsx`**: Use cases page (`/use-cases`)
  - Card grid of use-case scenarios
  - Routes from the shared header nav

- **`pages/AppShell.tsx`**: Main app layout (`/app`)
  - Sidebar with navigation (Projects, Playlists, etc.)
  - react-router `Outlet` for nested pages
  - Common header/footer for authenticated views

- **`pages/ProjectsPage.tsx`**: List all projects (`/app/projects`)
  - CRUD (create, read, update, delete projects)

- **`pages/ProjectPage.tsx`**: One project detail (`/app/projects/:projectId`)
  - Shows playlists nested under this project

- **`pages/PlaylistPage.tsx`**: Playlist grid (`/app/playlists/:playlistId`)
  - Shows scenario cards (one per scenario)
  - Each card has render status polling + action buttons

- **`pages/ScenarioEditorPage.tsx`**: Scenario authoring (`/app/scenarios/:scenarioId`)
  - Tabs: Steps (form), Config (docker/typing/env), YAML Preview
  - Ordered list of StepEditor components
  - Render button (enqueues job, starts polling)
  - Uses `setInterval` to poll `/api/jobs/{id}` every 2s while running
  - Client-side YAML render via `js-yaml` (must match backend's `/yaml` output exactly)

#### Components

- **`components/app/StepEditor.tsx`**: Per-step form
  - One editor per step type (command, comment, write_file, write_vim, presenterm)
  - Dynamic form fields based on `ScenarioStep.type`
  - File upload for `write_file`/`write_vim` content

- **`components/app/ScenarioCard.tsx`**: Playlist grid card
  - Displays scenario title, last-render status
  - Own `useQuery` w/ `refetchInterval: isActive ? 2000 : false`
  - Job status badge; download links on completion

- **`components/app/JobLogDialog.tsx`**: Render log viewer
  - Modal dialog showing streamed log
  - Polls `/api/jobs/{id}/log` while open
  - Plaintext display (ANSI sequences already stripped by backend)

- **`components/app/New*Dialog.tsx`**: Create flows
  - `NewProjectDialog`, `NewPlaylistDialog`, `NewScenarioDialog`
  - Modal forms with validation

- **`components/marketing/SiteHeader.tsx`**: Shared site header
  - Logo, navigation (Home, Use Cases, App link)
  - Used on both marketing pages

- **`components/marketing/SiteFooter.tsx`**: Shared site footer
  - Links, copyright, etc.

- **`components/ui/`**: shadcn/ui Base UI-backed components
  - Button, Card, Dialog, Input, Textarea, Badge, Alert, etc.
  - All use `render` prop for polymorphism (not Radix's `asChild`)
  - Tailwind v4 styling

#### API Layer

- **`lib/api.ts`**: Typed axios wrappers per resource
  - `Projects`, `Playlists`, `Scenarios`, `Jobs`, `Flavours` namespaces
  - One method per endpoint (POST create, GET read, PATCH update, DELETE delete, etc.)
  - Base URL `/api`; `/media` requests use StaticFiles from backend

- **`lib/types.ts`**: Hand-maintained Pydantic mirror
  - `Project`, `Playlist`, `Scenario`, `RenderJob`, `DockerConfig`, `TypingConfig`, `ScenarioStep`, `Flavour`
  - No codegen; kept in sync manually
  - Exact field name matching (camelCase for TypeScript, snake_case for backend models via axios serialization)

#### Configuration

- **`vite.config.ts`**: Vite dev server config
  - Proxies `/api` and `/media` to `http://127.0.0.1:8000` (backend)
  - Enables development without CORS issues

- **`tailwind.config.ts`**: Tailwind v4 setup
- **`tsconfig.json`**: TypeScript strict mode
- **`biome.json`**: Oxlint config (linting)

### Configuration: `frontend/package.json`

- Bun package manager
- React 19, TanStack Query v5, react-router v7, axios, js-yaml
- shadcn/ui, Tailwind CSS v4
- Oxlint (linter), TypeScript (compiler)
- Scripts: `dev` (vite dev), `build` (tsc + vite build), `lint` (oxlint)

## Docker & Deployment

### Flavours (Pre-Built Environments)

- **`flavours/flavours.yaml`**: Manifest of available Docker environments
  - Lists: id, display_name, dockerfile (relative path), description
  - Only one flavour today: `"rust"`

- **`flavours/rust/Dockerfile`**: Rust 1.60.0-bullseye + tools
  - Base: `rust:1.60.0-bullseye`
  - Installs: vim, git, curl, presenterm (prebuilt binary)
  - Used for `write_vim` steps and presenterm slideshow steps

### Root Dockerfile (Production Image)

- **`Dockerfile`** (repo root): Multi-stage build
  - Stage 1 (`frontend-build`): Bun build, produces `dist/`
  - Stage 2 (`runtime`): Python 3.12-slim, installs:
    - Root `uv sync --frozen` (CLI pipeline deps)
    - Backend `uv sync --frozen` (FastAPI, RQ, etc.)
    - Docker CLI client (for building flavour images at runtime)
    - Static FFmpeg binary (mwader/static-ffmpeg:7.1)
    - Prebuilt agg + asciinema v3 binaries
  - Exposes ports 8000 (FastAPI), 5173 (frontend served static)
  - Healthcheck on `/api/health`

### docker-compose.yaml (Production Topology)

4-service topology for production:

- **`redis`**: In-memory queue backend (internal only)
  - No exposed ports; accessed by web/worker via `redis://redis:6379`

- **`dind`** (Docker-in-Docker): `docker:27-dind`
  - Privileged, isolated from host Docker
  - Mounted at `tcp://dind:2375` (no TLS in dev)
  - Used by `driver.py` at render time (started inside containers via env var)

- **`web`**: FastAPI app
  - Port `8000` (exposed for external access)
  - Serves API + static frontend (if built)
  - Healthcheck on `/api/health`
  - Volume: `termreel-data:/app/backend/data` (shared with worker)
  - Env: `REDIS_URL=redis://redis:6379/0`, `DOCKER_HOST=tcp://dind:2375`

- **`worker`**: RQ worker (same image as web)
  - No exposed ports
  - Runs `python -m app.worker`
  - Same Redis + Docker access as web
  - Volume: `termreel-data:/app/backend/data` (shared with web)

**Named volumes:**
- `termreel-data`: Shared `/app/backend/data` (SQLite, media, workspaces)
- `dind-storage`: Docker image/container storage for dind

## Development Scripts

- **`dev.sh`**: Start the full local stack
  - Starts redis (if not running)
  - Backgrounds `uvicorn` (API on port 8000)
  - Backgrounds RQ worker
  - Polls `/api/health` up to 30s
  - Starts Bun dev server (frontend on port 5173)
  - Trap cleanup on exit

## Data Storage

All persistent data is under `backend/data/` (gitignored):

- **`db.sqlite`**: SQLite database (Project, Playlist, Scenario, RenderJob tables)
- **`media/`**: Rendered artifacts (MP4, GIF, JSON metadata)
  - Organized by job_id: `media/{job_id}/{artifact_name}.{mp4,gif,json}`
- **`workspaces/`**: Per-job isolated filesystem mounts
  - Organized by job_id: `workspaces/{job_id}/` (copied from mount_host_path at render time)

Nothing survives a fresh checkout; all re-renders from scenarios in the DB.

## Key Architectural Patterns

1. **Cascade delete hierarchy**: Project → Playlist → Scenario → RenderJob, with foreign key cascade at every level.
2. **Job-scoped isolation**: Each render job has its own workspace and media directories, preventing concurrent-render interference.
3. **CLI pipeline as external service**: Backend never reimplements recording/rendering; always shells out to root `driver.py`/`render.sh`.
4. **Polling-based status**: No websockets; frontend polls on a 2s interval while job is running.
5. **Exact YAML round-tripping**: Backend's YAML export format is identical to CLI pipeline input format, enabling perfect fidelity.
6. **Separate uv projects**: Root and backend are independent projects with separate lock files and venvs to avoid dependency conflicts.
