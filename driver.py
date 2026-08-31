#!/usr/bin/env python3
"""
driver.py — reads a scenario YAML file, starts a Docker container, and
"types" a sequence of terminal commands into it with human-like timing
while asciinema records the whole session to a .cast file.

Pipeline:
    scenario.yaml --> driver.py --> session.cast --> (render.sh) --> mp4/gif

Requirements:
    pip install pexpect pyyaml
    asciinema and docker must be installed and on PATH.

Usage:
    python3 driver.py scenario.example.yaml --out session.cast
"""

import argparse
import random
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pexpect
import yaml

PROMPT_SETTLE = 0.4  # brief pause after spawning, before we start typing


def load_scenario(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def start_container(cfg: dict) -> str:
    """Start a detached container we can exec into. Returns container name."""
    docker_cfg = cfg["docker"]
    name = docker_cfg["container_name"]

    # Clean up any leftover container from a previous run.
    subprocess.run(["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    mount_host = str(Path(docker_cfg["mount_host_path"]).resolve())
    Path(mount_host).mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run", "-d",
        "--name", name,
        "-v", f"{mount_host}:{docker_cfg['mount_container_path']}",
        "-w", docker_cfg.get("workdir", docker_cfg["mount_container_path"]),
        docker_cfg["image"],
        "sleep", "infinity",
    ]
    subprocess.run(cmd, check=True)
    return name


def stop_container(name: str):
    subprocess.run(["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def human_type(child: pexpect.spawn, text: str, base_cps: float, jitter_pct: float):
    """Send text one character at a time with randomized delay, like a human typing."""
    base_delay = 1.0 / base_cps
    for ch in text:
        child.send(ch)
        jitter = base_delay * jitter_pct
        delay = max(0.01, random.uniform(base_delay - jitter, base_delay + jitter))
        # Occasionally simulate a slightly longer pause (thinking / punctuation).
        if ch in ",.(){}[]" and random.random() < 0.3:
            delay += base_delay * 2
        time.sleep(delay)


def run_command(child: pexpect.spawn, text: str, timing: dict):
    human_type(child, text, timing["base_cps"], timing["jitter_pct"])
    child.send("\r")
    time.sleep(timing.get("settle", 0.3))


def do_step(child: pexpect.spawn, step: dict, timing: dict, cols: int):
    step_type = step["type"]

    if step_type == "command":
        run_command(child, step["text"], timing)

    elif step_type == "comment":
        # A line typed past the pty's column width relies on the terminal
        # and bash's readline agreeing on where it wraps, which in practice
        # (through asciinema -> docker exec's own pty layering) drifts and
        # makes readline redraw over the same line instead of moving down.
        # Sidestep that entirely by wrapping narration into several short
        # "# ..." lines ourselves, each its own real Enter-terminated line.
        wrap_width = max(20, cols - 4)
        for line in textwrap.wrap(step["text"], width=wrap_width) or [""]:
            run_command(child, f"# {line}", timing)

    elif step_type == "write_file":
        # Interactive bash reads heredoc bodies through readline, so a raw
        # tab byte is treated as a completion request (not literal input) -
        # with two similarly-named files in the dir this silently splices a
        # completed filename into the file instead of the tab. Expand tabs
        # to spaces before sending so no raw tab byte ever hits the pty.
        content = Path(step["content_file"]).read_text().expandtabs(4)
        # Type the opening line visibly, then paste the body at once
        # (typing a whole file char-by-char is slow and adds nothing visually).
        opening = f"cat > {step['path']} << 'EOF'"
        human_type(child, opening, timing["base_cps"], timing["jitter_pct"])
        child.send("\r")
        time.sleep(0.2)
        child.send(content + "\r")
        child.send("EOF\r")
        time.sleep(timing.get("settle", 0.3))

    else:
        raise ValueError(f"Unknown step type: {step_type}")

    time.sleep(step.get("pause_after", timing.get("default_pause_after", 1.0)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", help="Path to scenario YAML file")
    parser.add_argument("--out", default="session.cast", help="Output asciinema .cast path")
    parser.add_argument("--cols", type=int, default=120)
    parser.add_argument("--rows", type=int, default=30)
    args = parser.parse_args()

    cfg = load_scenario(args.scenario)
    timing = cfg.get("typing", {"base_cps": 14, "jitter_pct": 0.3})

    print(f"[*] Starting container for: {cfg.get('title', args.scenario)}")
    container_name = start_container(cfg)

    try:
        # asciinema records everything that happens on this pty, including
        # the docker exec session we spawn inside it. --window-size pins the
        # recorded pty to the exact size we tell readline to wrap against
        # (see do_step's comment-wrapping). Most base images (e.g. golang's)
        # have no locale configured (LC_CTYPE=POSIX) - without a UTF-8
        # locale, bash's readline miscomputes the on-screen column width of
        # multi-byte characters, so any non-ASCII comment that wraps a line
        # corrupts the display (redraws overwrite the previous row instead
        # of moving down). Forcing LC_ALL fixes readline's column math;
        # C.UTF-8 is a synthetic glibc locale needing no locale-gen.
        rec_cmd = (
            f"asciinema rec --overwrite "
            f"--window-size {args.cols}x{args.rows} "
            f"--command \"docker exec -e LC_ALL=C.UTF-8 -it {container_name} bash\" "
            f"{args.out}"
        )
        print(f"[*] Recording to {args.out}")
        child = pexpect.spawn(
            "/bin/bash", ["-c", rec_cmd],
            dimensions=(args.rows, args.cols),
            encoding="utf-8",
            codec_errors="replace",
            timeout=None,
        )
        # Mirror the pty content (typed commands + their real output) to our
        # own stdout, alongside the progress prints above, so a caller
        # capturing this process's stdout/stderr (e.g. render_pipeline.py)
        # sees what actually happened inside the container, not just that
        # asciinema recorded *something*.
        child.logfile_read = sys.stdout
        time.sleep(PROMPT_SETTLE + 1.0)  # let container shell settle

        for step in cfg["steps"]:
            do_step(child, step, timing, args.cols)

        # Exit the inner shell, which ends the asciinema recording.
        child.send("exit\r")
        child.expect(pexpect.EOF, timeout=10)

    finally:
        print(f"[*] Stopping container {container_name}")
        stop_container(container_name)

    print(f"[+] Done. Recording saved to {args.out}")


if __name__ == "__main__":
    main()
