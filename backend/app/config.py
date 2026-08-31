import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
WORKSPACES_DIR = DATA_DIR / "workspaces"
DB_PATH = DATA_DIR / "app.db"

DRIVER_PY = REPO_ROOT / "driver.py"
RENDER_SH = REPO_ROOT / "render.sh"
DEMO_REPO_DIR = REPO_ROOT / "demo-repo"
FLAVOURS_DIR = REPO_ROOT / "flavours"
FLAVOURS_MANIFEST = FLAVOURS_DIR / "flavours.yaml"
FRONTEND_DIST_DIR = REPO_ROOT / "frontend" / "dist"

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
RENDER_QUEUE_NAME = "renders"

# Comma-separated list, e.g. "https://termreel.app". Defaults to "*" for local dev.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = ["*"] if _allowed_origins == "*" else [
    o.strip() for o in _allowed_origins.split(",") if o.strip()
]

for d in (DATA_DIR, MEDIA_DIR, WORKSPACES_DIR):
    d.mkdir(parents=True, exist_ok=True)
