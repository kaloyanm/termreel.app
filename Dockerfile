# Single image, shared by the "web" (uvicorn) and "worker" (RQ) services in
# docker-compose.yml — they only differ by their CMD override.

# ---- frontend build ----
FROM oven/bun:1 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/ ./
RUN bun run build

# ---- runtime ----
FROM python:3.12-slim AS runtime

# docker-cli: client only — talks to the dind sidecar over DOCKER_HOST, never a local daemon.
# ffmpeg/curl: render.sh's gif->mp4 step, and fetching the agg binary below.
RUN apt-get update && apt-get install -y --no-install-recommends \
      docker-cli ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# agg (asciinema cast -> gif renderer) and asciinema itself: driver.py needs
# the v3 asciinema CLI (--window-size support), which isn't on PyPI — that
# only ships the old v2 Python implementation — so both are fetched as
# prebuilt Rust binary releases, matching whatever arch this image builds
# for (TARGETARCH is set automatically by BuildKit).
ARG TARGETARCH
# v1.9.0+: agg only gained asciicast-v3 support (what asciinema 3.x records) in 2026.
ARG AGG_VERSION=v1.9.0
ARG ASCIINEMA_VERSION=v3.2.1
RUN case "${TARGETARCH}" in \
      amd64) RUST_ARCH=x86_64-unknown-linux-gnu ;; \
      arm64) RUST_ARCH=aarch64-unknown-linux-gnu ;; \
      *) echo "unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /usr/local/bin/agg \
      "https://github.com/asciinema/agg/releases/download/${AGG_VERSION}/agg-${RUST_ARCH}" \
    && curl -fsSL -o /usr/local/bin/asciinema \
      "https://github.com/asciinema/asciinema/releases/download/${ASCIINEMA_VERSION}/asciinema-${RUST_ARCH}" \
    && chmod +x /usr/local/bin/agg /usr/local/bin/asciinema

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Root project's venv: driver.py's own runtime (pexpect, pyyaml, asciinema).
# render_pipeline.py invokes driver.py with this venv's python3 directly.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:${PATH}"

# Backend's venv: FastAPI/RQ app, kept separate per the two-uv-projects setup
# (see CLAUDE.md — a shared workspace made the two projects' deps clobber
# each other).
COPY backend/pyproject.toml backend/uv.lock backend/
RUN cd backend && uv sync --frozen --no-dev

COPY driver.py render.sh scenario.example.yaml ./
COPY demo-repo/ ./demo-repo/
COPY backend/app/ ./backend/app/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN chmod +x render.sh

WORKDIR /app/backend
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
