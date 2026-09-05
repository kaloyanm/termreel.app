# Code Standards & Structure Conventions

This document describes the coding standards and structural conventions actually observed in the Termreel codebase. These are patterns derived from existing code; follow them when adding new code to maintain consistency.

## Python (Root + Backend)

### File Organization

- **Module structure**: One responsibility per file (e.g., `models.py` for ORM, `schemas.py` for Pydantic, `tasks.py` for RQ jobs)
- **Import order**: Standard library, third-party, local imports (implicit grouping)
- **Naming**: snake_case for modules, functions, and variables
- **Line length**: No hard limit enforced; aim for readability (120-140 char typical)

### Functions & Methods

- **Type hints**: All function signatures include type hints (e.g., `def run_render(job_id: int, ...) -> str:`)
- **Docstrings**: Used sparingly; code is self-documenting where possible
- **Error handling**: Explicit exception types (e.g., `RenderError`) rather than generic `Exception`
- **Logging**: None in the codebase; use callback functions (like `on_log` in `render_pipeline.py`) for structured output

### Classes

- **SQLModel/Pydantic models**: Use SQLModel for both ORM and validation in one class
  - Field constraints via Pydantic validators (e.g., `model_validator(mode='after')`)
  - JSON columns for structured data (`Scenario.steps`, `Scenario.docker`, `Scenario.typing`)
  - Cascade delete at the ORM level, not business logic

- **No class hierarchies**: Simple, flat models; inheritance avoided unless it truly simplifies the design

### Testing

- **Single test file**: `backend/tests/test_api.py` is one comprehensive file, not split by module
- **Test structure**: In-memory SQLite per test; fixtures for common setup
- **Coverage**: API integration tests (CRUD flow, step validation, flavour validation); no unit test isolation
- **Execution**: `cd backend && uv run pytest` (pytest.ini configured for local discovery)

### Dependencies (Backend)

- **Explicit version pinning**: `uv sync --frozen` uses locked versions from `uv.lock`
- **No vendoring**: All dependencies installed via uv
- **Service dependencies**: Redis, Docker (external, not vendored)

### Dependencies (Root/CLI)

- **Minimal core deps**: pexpect, pyyaml, docker (Python SDK)
- **Separate from backend**: Root `pyproject.toml` and `backend/pyproject.toml` are independent projects, never merged into a workspace

## TypeScript / React

### File Organization

- **Pages vs Components**: Pages live in `src/pages/`, reusable components in `src/components/`
  - **Category subdirs**: `components/app/` (app-specific), `components/ui/` (shadcn/ui primitives), `components/marketing/` (shared site components)
- **Naming**: PascalCase for components (e.g., `ScenarioCard.tsx`), camelCase for utilities (e.g., `api.ts`)
- **One component per file**: Each `.tsx` file exports one React component (possibly nested helpers)
- **Index files**: No index.ts re-exports; import directly from the component file

### Type Safety

- **Strict TypeScript**: `tsconfig.json` enables strict mode throughout
- **Manual type mirroring**: `lib/types.ts` mirrors backend Pydantic schemas by hand (no codegen)
  - Keep in sync manually; update `types.ts` whenever backend schemas change
  - Field names use TypeScript conventions (camelCase); axios serializes to snake_case for API calls
- **Avoid `any`**: Type all props, state, and API responses

### Component Patterns

- **Functional components with hooks**: All components are functional (no class components)
  - React 19 + TanStack Query v5 (React Query) for server state
  - `useState` for local UI state
  - `useQuery`/`useMutation` for async operations
- **Props interface per component**: Each component defines its own props interface at the top of the file
- **No default exports for utils**: Named exports for consistency
- **Custom hooks**: Rare; most logic lives inline in components

### State Management

- **TanStack Query for server state**: All API data fetched via `useQuery` or `useMutation`
  - `refetchInterval` for polling (e.g., job status every 2s while running)
  - No global Redux/Zustand; unnecessary for single-operator tool
- **Local UI state with useState**: Dialog open/close, form inputs, etc.
- **No optimistic updates**: Responses are authoritative; UI updates on API success

### Styling

- **Tailwind CSS v4**: All styling via utility classes
- **shadcn/ui components**: Base UI-backed variant
  - Uses `render` prop for polymorphism (not Radix's `asChild`)
  - Customize via Tailwind, not component prop drilling
- **No CSS modules or CSS-in-JS**: Tailwind only
- **Responsive design**: Mobile-first utility classes (sm:, md:, lg:, etc.)

### API Integration

- **Typed axios wrappers**: `lib/api.ts` exports namespaced axios instances
  - Example: `Jobs.render(scenarioId)`, `Scenarios.getYaml(id)`, `Flavours.list()`
  - One method per endpoint; method names match intent (create, read, update, delete, etc.)
- **Error handling**: Catch and surface API errors in the UI (e.g., 422 validation error, 404 not found)
- **Base URL**: Axios configured with base URL `/api`; media files from `/media` (StaticFiles)

### Polling Pattern

Three independent polling loops exist (not ideal, but current implementation):

1. **ScenarioCard.tsx**: Polls via own `refetchInterval` while job is active
2. **JobLogDialog.tsx**: Polls log endpoint while dialog open
3. **ScenarioEditorPage.tsx**: Uses `setInterval` + TanStack `invalidateQueries` while rendering

All three use 2s interval when actively rendering; no polling when job is done/failed. Future improvement: consolidate to a single subscription/observer pattern.

### Router Setup

- **react-router v7**: BrowserRouter at app root
- **Route hierarchy**: Pages are route components; nested routes use `Outlet`
  - `/` (Landing)
  - `/use-cases` (UseCases)
  - `/app` (AppShell layout)
    - `/app/projects` (ProjectsPage)
    - `/app/projects/:projectId` (ProjectPage)
    - `/app/playlists/:playlistId` (PlaylistPage)
    - `/app/scenarios/:scenarioId` (ScenarioEditorPage)

### Linting & Build

- **Oxlint**: Fast, strict linting (no warnings suppressed)
  - Run: `bun run lint`
- **TypeScript**: Full build check
  - Run: `bun run build` (runs `tsc -b && vite build`)
- **Vite**: Build tool and dev server
  - Dev server proxies `/api` and `/media` to backend
  - Production build outputs to `frontend/dist/` (served by backend if present)

## FastAPI Backend

### Route Organization

- **Flat route modules**: One file per resource (`projects.py`, `playlists.py`, `scenarios.py`, `jobs.py`, `flavours.py`)
- **Router registration**: Each module exports a `router: APIRouter`, imported and included in `main.py`
- **Naming**: Route functions are descriptive (e.g., `create_project`, `list_scenarios`, `render_scenario`)
- **Path parameters**: Named consistently (e.g., `:projectId`, `:playlistId`, `:scenarioId`)

### Validation

- **Pydantic model validators**: Enforce constraints at the model level
  - Example: `ScenarioStep` model validator ensures required fields per step type
  - Example: `write_vim` content length guardrail in `scenarios.py` POST handler
- **Custom exceptions**: `RenderError` for render failures; caught and returned as 500
- **HTTP status codes**: 
  - 200 for success
  - 201 for created (POST resource)
  - 422 for validation error (unknown flavour, invalid step, content too long)
  - 404 for not found
  - 500 for server error

### Database

- **SQLModel async/sync**: The codebase uses sync SQLModel (no async SQLAlchemy)
- **Session management**: One session per request; SQLModel Session passed to route handlers
- **No N+1 queries**: Relations are eagerly loaded or joined when needed
- **Cascade behavior**: Defined at the ORM level; deletes cascade automatically

### Job Queue (RQ)

- **Single queue**: Named `"renders"`
- **Job timeout**: 1800 seconds (30 minutes)
- **Status tracking**: Job status stored in RQ queue and reflected in DB `RenderJob.status`
- **Logging**: Streamed to `RenderJob.log` via callback function during job execution

## Database Schema

### Naming Conventions

- **Table names**: Plural snake_case (e.g., `project`, `playlist`, `scenario`, `render_job`)
- **Columns**: snake_case (e.g., `created_at`, `updated_at`, `docker_config`, `job_id`)
- **Foreign keys**: Implicit naming via SQLModel ForeignKey constraint (e.g., `project_id`)
- **Timestamps**: `created_at`, `updated_at` (UTC, datetime fields)

### JSON Columns

Structured data stored as JSON in the DB (intentional denormalization for simplicity):

- `Scenario.docker`: DockerConfig (flavour, mount_host_path)
- `Scenario.typing`: TypingConfig (base_cps, jitter_pct)
- `Scenario.steps`: List[ScenarioStep] (all step data inline)

Rationale: Scenarios are read as whole units; no per-step querying needed. Simpler schema, easier migrations.

### Cascade Semantics

Every level cascades on delete:

- `Project.delete()` → cascades to all `Playlist` rows → cascades to all `Scenario` rows → cascades to all `RenderJob` rows
- No orphaned records by design
- Media on disk is **not** deleted on cascade (render job media files under `backend/data/media/` persist)

## CLI Pipeline (driver.py / render.sh)

### Step Type Dispatcher Pattern

New step types are added as branches in `driver.py`'s `do_step()` function:

```python
def do_step(step, container_name, ...):
    if step.type == "command":
        run_command(...)
    elif step.type == "write_file":
        run_write_file(...)
    elif step.type == "write_vim":
        run_write_vim(...)
    elif step.type == "presenterm":
        run_presenterm(...)
    else:
        raise ValueError(f"Unknown step type: {step.type}")
```

Each step type handler:
- Takes the step dict, container name, and execution context
- Interacts with the container via `docker exec` or `pexpect` PTY
- Raises an exception on failure (caught by the main render loop)

### Locale & Character Encoding

- **Invariant**: All container execs use `LC_ALL=C.UTF-8`
- **Rationale**: Base images have no locale configured; without it, bash's readline miscomputes cursor position for multi-byte text (e.g. Cyrillic), corrupting terminal display on line wrap
- **Impact**: Ensures terminal recording is clean and readable regardless of text content

### Flavour Resolution

Flavours are resolved and built in `driver.py`'s `start_container()` function:

- `resolve_flavour_image(flavour_id)` builds the Dockerfile if not already cached
- Caching is by Docker image tag: `termreel-flavour-{flavour_id}`
- First call for a flavour builds the image; subsequent calls check tag existence (fast)
- Force rebuild by running `docker rmi termreel-flavour-{flavour_id}`

### Workspace Isolation

Each job gets an isolated workspace directory:

- `backend/data/workspaces/{job_id}/` is a fresh copy of `mount_host_path` (default `demo-repo/`)
- The CLI pipeline always runs against this isolated dir, not the host's mount path
- Concurrent renders don't interfere (each has its own workspace)
- Workspace is mounted into the container at `mount_host_path`'s configured location

## Extensibility Points

1. **New step types**: Add a branch to `do_step()` in `driver.py`, add schema to `ScenarioStep` in `backend/schemas.py`, add form UI to `StepEditor.tsx`
2. **New flavours**: Add entry to `flavours/flavours.yaml`, create `flavours/{id}/Dockerfile`
3. **New API endpoints**: Add a route file in `backend/app/routers/`, register in `main.py`
4. **New UI pages**: Create a page component in `frontend/src/pages/`, add route to router setup in `main.tsx`

## Performance Notes

- **Single-operator tool**: No horizontal scaling; all services run in a single process or container
- **Polling interval**: Job status polled every 2 seconds (acceptable for single user; revisit if concurrency grows)
- **Workspace copy overhead**: Each render copies the entire `mount_host_path` directory (quick for small repos; monitor for large monorepos)
- **No connection pooling**: SQLite single connection per app instance (acceptable for single operator)
- **No async I/O**: Backend uses sync FastAPI (sufficient for single-user workload)

## Known Gaps / Technical Debt

- **Three polling loops**: Frontend has three independent polling mechanisms for job status; future refactor could consolidate to a single subscription pattern
- **Manual type mirroring**: `lib/types.ts` must be kept in sync with backend schemas by hand; no codegen
- **Media and workspace cleanup**: Cascade deletes don't clean up rendered media or job workspaces on disk; files accumulate under `backend/data/`
- **No error recovery**: If a command hangs mid-recording, the entire render hangs indefinitely; no per-step timeout or skip/abort path
- **No end-to-end automation test**: Most CLI-pipeline features depend on real Docker/asciinema/agg/ffmpeg and aren't exercised by `backend/tests/test_api.py`, which only covers the CRUD/API surface
- **Local dev proxying**: Frontend dev server proxies to localhost backend; doesn't work if backend isn't on localhost
