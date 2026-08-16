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

REDIS_URL = "redis://127.0.0.1:6379/0"
RENDER_QUEUE_NAME = "renders"

for d in (DATA_DIR, MEDIA_DIR, WORKSPACES_DIR):
    d.mkdir(parents=True, exist_ok=True)
