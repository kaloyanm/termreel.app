"""Bridges a Scenario DB row to the existing driver.py / render.sh toolchain.

Deliberately does not reimplement recording/rendering: it materializes the
scenario into the same YAML shape as scenario.example.yaml, then shells out
to the untouched root-level driver.py (asciinema + docker + pexpect) and
render.sh (agg + ffmpeg), exactly as described in the repo README.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from app.config import DEMO_REPO_DIR, DRIVER_PY, MEDIA_DIR, RENDER_SH, REPO_ROOT, WORKSPACES_DIR

ROOT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"


class RenderError(RuntimeError):
    def __init__(self, message: str, log: str = ""):
        super().__init__(message)
        self.log = log


def _materialize_workspace(job_id: str, docker_cfg: dict[str, Any]) -> Path:
    """Copy the scenario's source mount into an isolated per-job directory
    so concurrent renders of the same scenario never clobber each other."""
    workspace = WORKSPACES_DIR / job_id
    workspace.mkdir(parents=True, exist_ok=True)

    src = Path(docker_cfg.get("mount_host_path", "./demo-repo"))
    if not src.is_absolute():
        src = (REPO_ROOT / src).resolve()
    if not src.exists():
        src = DEMO_REPO_DIR

    if src.exists():
        for item in src.iterdir():
            dest = workspace / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    return workspace


def _materialize_scenario_yaml(
    job_id: str,
    title: str,
    docker_cfg: dict[str, Any],
    typing_cfg: dict[str, Any],
    steps: list[dict[str, Any]],
    workspace: Path,
) -> Path:
    artifacts_dir = workspace / "_step_content"
    artifacts_dir.mkdir(exist_ok=True)

    materialized_steps = []
    for i, step in enumerate(steps):
        step = dict(step)
        if step.get("type") == "write_file" and step.get("content") is not None:
            content_path = artifacts_dir / f"step_{i}_{Path(step['path']).name}"
            content_path.write_text(step["content"])
            step["content_file"] = str(content_path)
            step.pop("content", None)
        materialized_steps.append({k: v for k, v in step.items() if v is not None})

    docker_cfg = dict(docker_cfg)
    docker_cfg["container_name"] = f"{docker_cfg['container_name']}_{job_id}"
    docker_cfg["mount_host_path"] = str(workspace)

    scenario_doc = {
        "title": title,
        "docker": docker_cfg,
        "typing": typing_cfg,
        "steps": materialized_steps,
    }

    yaml_path = workspace / "scenario.yaml"
    yaml_path.write_text(yaml.safe_dump(scenario_doc, sort_keys=False))
    return yaml_path


def run_render(
    job_id: str,
    scenario_title: str,
    docker_cfg: dict[str, Any],
    typing_cfg: dict[str, Any],
    steps: list[dict[str, Any]],
    theme: str = "dracula",
) -> dict[str, str]:
    """Runs the full pipeline for one job. Returns relative media paths.

    Raises RenderError with captured stdout/stderr on any failure.
    """
    workspace = _materialize_workspace(job_id, docker_cfg)
    yaml_path = _materialize_scenario_yaml(
        job_id, scenario_title, docker_cfg, typing_cfg, steps, workspace
    )

    job_media_dir = MEDIA_DIR / job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)
    cast_path = job_media_dir / "session.cast"
    out_base = job_media_dir / "episode"

    log_parts = []

    driver_python = ROOT_PYTHON if ROOT_PYTHON.exists() else "python3"
    driver_cmd = [
        str(driver_python), str(DRIVER_PY), str(yaml_path), "--out", str(cast_path),
    ]
    proc = subprocess.run(driver_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    log_parts.append("$ " + " ".join(driver_cmd) + "\n" + proc.stdout + proc.stderr)
    if proc.returncode != 0 or not cast_path.exists():
        raise RenderError("driver.py failed to record the session", "\n".join(log_parts))

    render_cmd = [str(RENDER_SH), str(cast_path), str(out_base), theme]
    proc = subprocess.run(render_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    log_parts.append("$ " + " ".join(render_cmd) + "\n" + proc.stdout + proc.stderr)
    gif_path = out_base.with_suffix(".gif")
    mp4_path = out_base.with_suffix(".mp4")
    if proc.returncode != 0 or not mp4_path.exists():
        raise RenderError("render.sh failed to produce a video", "\n".join(log_parts))

    return {
        "cast_path": str(cast_path.relative_to(MEDIA_DIR)),
        "gif_path": str(gif_path.relative_to(MEDIA_DIR)),
        "mp4_path": str(mp4_path.relative_to(MEDIA_DIR)),
        "log": "\n".join(log_parts),
    }
