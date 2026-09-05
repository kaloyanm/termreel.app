#!/usr/bin/env bash
# dev.sh — starts the whole termreel stack for local development:
# redis, the FastAPI API, the RQ render worker, and the Vite dev server.
#
# Requires (same as the original CLI pipeline): docker, asciinema, agg, ffmpeg,
# plus redis-server, uv and bun on PATH.
set -euo pipefail
cd "$(dirname "$0")"

cleanup() {
  echo "[*] Stopping services..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

if ! redis-cli ping >/dev/null 2>&1; then
  echo "[*] Starting redis-server on 6379"
  redis-server --daemonize yes --port 6379
fi

echo "[*] Starting FastAPI (http://127.0.0.1:8000)"
(cd backend && uv run uvicorn app.main:app --reload --port 8000) &

echo "[*] Starting RQ worker"
(cd backend && uv run python -m app.worker) &

# Vite's dev server (and its proxy to /api) comes up almost instantly, but
# uvicorn's full FastAPI/SQLModel import + --reload watcher setup takes
# noticeably longer - starting the frontend in parallel with no ordering
# raced the frontend's first page load against a backend that wasn't
# listening yet, surfacing as "ECONNREFUSED 127.0.0.1:8000" proxy errors.
echo "[*] Waiting for FastAPI to be ready..."
for _ in $(seq 1 150); do
  curl -s -o /dev/null http://127.0.0.1:8000/api/health && break
  sleep 0.2
done

echo "[*] Starting frontend (http://127.0.0.1:5173)"
(cd frontend && bun run dev) &

wait
