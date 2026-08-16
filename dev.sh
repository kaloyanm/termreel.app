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

echo "[*] Starting frontend (http://127.0.0.1:5173)"
(cd frontend && bun run dev) &

wait
