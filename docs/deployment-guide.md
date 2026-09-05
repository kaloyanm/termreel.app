# Deployment Guide

This document covers both local development setup and production deployment of Termreel.

## Prerequisites

Termreel requires several external tools on PATH:

- **Docker** (v27+): Container runtime for scenarios and build tools
  - Installation: https://docs.docker.com/get-docker/
  - Verify: `docker version`

- **asciinema** (v3): Terminal session recording
  - Installation: https://asciinema.org/docs/installation
  - Verify: `asciinema --version`

- **agg** (asciinema GIF): Cast → GIF renderer
  - Installation: https://github.com/asciinema/agg#installation
  - Verify: `agg --version`

- **ffmpeg** (v7+): Video processing (cast → MP4)
  - Installation: https://ffmpeg.org/download.html (or package manager)
  - Verify: `ffmpeg -version`

- **redis-server**: In-memory queue backend (dev only; Compose handles it in production)
  - Installation: https://redis.io/docs/getting-started/installation/
  - Verify: `redis-server --version`

- **uv** (Python package manager): For root and backend deps
  - Installation: https://docs.astral.sh/uv/getting-started/installation/
  - Verify: `uv --version`

- **bun** (JavaScript runtime): For frontend
  - Installation: https://bun.sh/docs/installation
  - Verify: `bun --version`

If any tool is missing, the CLI pipeline or dev stack will fail with a clear error message.

## Local Development

### Quick Start

```bash
cd /home/mirchevka/Workplace/termreel.app
./dev.sh
```

**What this does**:

1. Starts `redis-server` in the background (if not already running)
2. Starts the FastAPI backend on `http://127.0.0.1:8000`
3. Starts the RQ render worker (same process as the backend)
4. Polls `/api/health` up to 30 seconds for the backend to be ready
5. Starts the Bun dev server (frontend) on `http://127.0.0.1:5173`
6. Opens the browser (if available) to the frontend
7. On exit (`Ctrl+C`), shuts down all services cleanly

**Output**:

```
✓ Redis running at redis://127.0.0.1:6379/0
✓ Backend starting... (uvicorn on 8000)
✓ Worker starting...
✓ Waiting for API health...
✓ API ready!
✓ Frontend starting... (http://127.0.0.1:5173)
```

### Verify Installation

```bash
# Test the CLI pipeline standalone (no web app needed)
cd /home/mirchevka/Workplace/termreel.app
uv sync  # Install root deps
python3 driver.py scenario.example.yaml --out /tmp/test.cast
# If successful, produces /tmp/test.cast (asciinema recording)
```

### Manual Component Startup (if not using dev.sh)

**Terminal 1: Redis**
```bash
redis-server --daemonize yes
# Or in foreground: redis-server
```

**Terminal 2: Backend API**
```bash
cd /home/mirchevka/Workplace/termreel.app/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
# Runs on http://127.0.0.1:8000; auto-reloads on code changes
```

**Terminal 3: RQ Worker**
```bash
cd /home/mirchevka/Workplace/termreel.app/backend
uv run python -m app.worker
# Processes render jobs from the Redis queue
```

**Terminal 4: Frontend**
```bash
cd /home/mirchevka/Workplace/termreel.app/frontend
bun install  # First time only
bun run dev
# Runs on http://127.0.0.1:5173; auto-rebuilds on changes
```

Then open http://127.0.0.1:5173 in a browser.

### Testing

```bash
cd /home/mirchevka/Workplace/termreel.app/backend
uv run pytest  # Run all tests (in-memory SQLite)
uv run pytest tests/test_api.py::test_scenario_rejects_unknown_flavour  # Run one test
uv run pytest -v  # Verbose output
```

**Test coverage**: API integration tests cover CRUD flow, step validation, flavour resolution, and typing guardrails. See [Codebase Summary](./codebase-summary.md#directory-backendtests) for details.

### Linting & Type Checking

**Backend**:
```bash
cd /home/mirchevka/Workplace/termreel.app/backend
uv run pytest  # No separate linter; tests validate behavior
```

**Frontend**:
```bash
cd /home/mirchevka/Workplace/termreel.app/frontend
bun run lint   # Oxlint (fast, strict linting)
bun run build  # TypeScript + Vite build (checks types)
```

## Production Deployment

### Pre-Build Steps

1. **Build the frontend SPA**:
   ```bash
   cd /home/mirchevka/Workplace/termreel.app/frontend
   bun install
   bun run build
   # Produces frontend/dist/ with optimized static assets
   ```

2. **Create .env file** (optional, all have defaults):
   ```bash
   cat > /home/mirchevka/Workplace/termreel.app/.env << 'EOF'
   REDIS_URL=redis://redis:6379/0
   ALLOWED_ORIGINS=https://yourdomain.com
   DOCKER_HOST=tcp://dind:2375
   EOF
   ```

   **Environment Variables**:
   - `REDIS_URL`: Redis connection string (default `redis://127.0.0.1:6379/0`)
   - `ALLOWED_ORIGINS`: CORS-allowed origins (default `*`); set to specific domain in production
   - `DOCKER_HOST`: Docker daemon socket/URL (default for dind: `tcp://dind:2375`)
   - `DATABASE_URL`: SQLite path (default `backend/data/db.sqlite`)

3. **Verify docker-compose.yaml** (located at repo root):
   ```bash
   cd /home/mirchevka/Workplace/termreel.app
   docker-compose config  # Validates YAML syntax
   ```

### Deploy via docker-compose

```bash
cd /home/mirchevka/Workplace/termreel.app

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web      # API logs
docker-compose logs -f worker   # Render worker logs
docker-compose logs -f redis    # Redis logs
docker-compose logs -f dind     # Docker-in-Docker logs

# Stop all services
docker-compose down

# Clean up (remove volumes, including data)
docker-compose down -v
```

**What gets started**:

| Service | Image | Purpose | Port | Volume |
|---------|-------|---------|------|--------|
| `web` | `termreel:latest` | FastAPI + static frontend | 8000 | `termreel-data` |
| `worker` | `termreel:latest` | RQ render worker | none | `termreel-data` |
| `redis` | `redis:7-alpine` | Queue backend | none | none (ephemeral) |
| `dind` | `docker:27-dind` | Docker-in-Docker | 2375 | `dind-storage` |

### Build Docker Image

If the image doesn't exist or you need to rebuild:

```bash
cd /home/mirchevka/Workplace/termreel.app

# Build image (multi-stage: frontend build → runtime)
docker build -t termreel:latest .

# Tag for a registry (optional)
docker tag termreel:latest myregistry.com/termreel:1.0.0
docker push myregistry.com/termreel:1.0.0
```

**Build stages**:
1. `frontend-build`: Bun build (produces `dist/`)
2. `runtime`: Python 3.12-slim + CLI tools + prebuilt binaries + static frontend

**Image size**: ~800 MB (includes docker-cli, ffmpeg, agg, asciinema binaries)

### Persistent Data

All app data is stored under `backend/data/` (mounted as a Docker volume):

```
backend/data/
├── db.sqlite           # SQLite database
├── media/              # Rendered MP4/GIF files
│   └── {job_id}/
│       ├── episode.mp4
│       ├── episode.gif
│       └── metadata.json
└── workspaces/         # Per-job isolated filesystems
    └── {job_id}/
        └── (scenario files and mounted content)
```

**Volume management**:

```bash
# Backup before deleting
docker cp termreel-termreel-data-1:/app/backend/data ./data-backup

# Inspect volume
docker volume inspect termreel-termreel-data-1

# Clean up media (if implementing cleanup logic in future)
docker exec termreel-web-1 rm -rf /app/backend/data/media/*
```

**Important**: Media files are **not** automatically cleaned up when scenarios are deleted. Cascade deletes remove database rows but leave media files on disk under `backend/data/media/`. Monitor disk usage and implement cleanup if needed (see [Project Roadmap](./project-roadmap.md#2-media-cleanup-on-cascade-delete-technical)).

### Health Checks

The backend exposes `/api/health`:

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

Docker Compose healthcheck (automatic):
```
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Scaling Considerations

**Current setup is single-operator, not horizontally scalable**. To scale to multiple concurrent renders:

1. **Add more worker services** in docker-compose (all share the same Redis queue and `termreel-data` volume)
2. **Switch to PostgreSQL** (SQLite is single-writer; concurrent writes fail)
3. **Add push notifications** (replace polling with WebSockets/SSE)
4. **Implement authentication** (Open Decision #1 in [Roadmap](./project-roadmap.md))

See [System Architecture](./system-architecture.md#scalability-considerations) for details.

## Docker-in-Docker (dind) Troubleshooting

The `dind` service (Docker-in-Docker) allows the backend and worker to build and run Docker containers for scenarios.

### Common Issues

**Issue**: Worker can't reach dind
```bash
# Check dind is running
docker-compose ps dind

# Verify TCP connection
docker exec termreel-worker-1 nc -zv dind 2375
# Expected: Connection to dind 2375 port [tcp/*] succeeded!
```

**Issue**: "permission denied" when building flavours
```bash
# dind requires privileged mode (already set in docker-compose.yaml)
# If you're modifying the config, ensure:
# - privileged: true
# - DOCKER_HOST: tcp://dind:2375
```

**Issue**: Flavour images not found during render
```bash
# Check if image exists in dind
docker exec termreel-dind-1 docker images

# Force rebuild (deletes cached image)
docker exec termreel-dind-1 docker rmi termreel-flavour-rust

# Next render will rebuild automatically
```

### Manual Flavour Management

From inside a worker container:

```bash
# List built flavours
docker -H tcp://dind:2375 images termreel-flavour-*

# Inspect a flavour
docker -H tcp://dind:2375 image inspect termreel-flavour-rust

# Delete a flavour (force rebuild)
docker -H tcp://dind:2375 rmi termreel-flavour-rust
```

## Monitoring & Debugging

### View Render Job Logs

1. **Via the web UI**: Click a scenario card → "View Logs" button → see streamed output
2. **Via the API**:
   ```bash
   curl http://127.0.0.1:8000/api/jobs/{job_id}/log
   # Returns plaintext log (ANSI sequences already stripped)
   ```
3. **Via Docker logs**:
   ```bash
   docker-compose logs -f worker | grep render_scenario_job
   ```

### Database Inspection

```bash
# Access SQLite directly (inside the web container)
docker exec -it termreel-web-1 sqlite3 /app/backend/data/db.sqlite

# Common queries
sqlite> SELECT * FROM render_job ORDER BY created_at DESC LIMIT 5;
sqlite> SELECT * FROM scenario WHERE title LIKE '%example%';
sqlite> SELECT COUNT(*) as total_jobs FROM render_job;
```

### Performance Monitoring

**Render queue depth**:
```bash
# Check if jobs are queued but not processing
docker exec termreel-redis-1 redis-cli LLEN "renders"
# Output: number of queued jobs (should be 0 if worker is keeping up)
```

**Worker process**:
```bash
# Check if worker is alive
docker exec termreel-worker-1 ps aux | grep "app.worker"
# If missing, the container crashed; check logs
docker-compose logs worker | tail -50
```

## Upgrading

### Update Code

```bash
# Pull latest changes
cd /home/mirchevka/Workplace/termreel.app
git pull origin main

# Stop running services
docker-compose down

# Rebuild image (picks up new code)
docker build -t termreel:latest .

# Restart services (mounts same volume, preserves DB)
docker-compose up -d

# Verify health
curl http://127.0.0.1:8000/api/health
```

### Database Migrations

Termreel uses SQLModel without explicit migrations (simpler, suitable for early development). If the schema changes:

1. **Backup existing data**:
   ```bash
   docker cp termreel-termreel-data-1:/app/backend/data ./data-backup
   ```

2. **Wipe and recreate** (destructive, only if schema is incompatible):
   ```bash
   docker-compose down -v  # Deletes volume
   docker-compose up -d    # Recreates empty volume
   ```

3. **Or preserve data** (if new schema is backward-compatible):
   ```bash
   docker-compose down
   docker build -t termreel:latest .
   docker-compose up -d    # Reuses existing volume
   ```

Future: If multi-operator support is added, implement proper Alembic migrations.

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs web

# Common issues:
# - Redis not running: docker-compose up -d redis
# - Port 8000 in use: lsof -i :8000
# - Database locked: rm backend/data/db.sqlite (wipes data, use backup if needed)
```

### Frontend shows blank page

```bash
# Check browser console (F12) for errors
# Common issues:
# - Backend not reachable: verify http://127.0.0.1:8000/api/health returns 200
# - Wrong CORS origin: check ALLOWED_ORIGINS env var
# - Build not complete: wait 30s, then refresh
```

### Render job stuck "queued" forever

```bash
# Check if worker is running
docker-compose ps worker

# Check if worker is connected to Redis
docker-compose logs worker | grep "Connected"

# Force restart worker
docker-compose restart worker

# Check job status
docker exec termreel-web-1 sqlite3 /app/backend/data/db.sqlite \
  "SELECT id, status, error FROM render_job ORDER BY created_at DESC LIMIT 1;"
```

### Render job fails with "Docker not found"

```bash
# Verify dind is running and accessible
docker exec termreel-worker-1 docker -H tcp://dind:2375 ps

# If connection fails:
docker-compose logs dind | tail -20
docker-compose restart dind
```

## For Additional Help

- **Architecture details**: See [System Architecture](./system-architecture.md)
- **Code structure**: See [Codebase Summary](./codebase-summary.md)
- **Development workflow**: See [CLAUDE.md](../CLAUDE.md) in the repo
- **Project roadmap**: See [Project Roadmap](./project-roadmap.md)
- **Implementation history**: See [Project Changelog](./project-changelog.md)
