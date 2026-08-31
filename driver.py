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
import difflib
import random
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pexpect
import yaml

PROMPT_SETTLE = 0.4  # brief pause after spawning, before we start typing
TYPO_RATE = 0.03      # write_vim simulate_typos: chance per alnum char


def load_scenario(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


FLAVOURS_DIR = Path(__file__).resolve().parent / "flavours"
FLAVOURS_MANIFEST = FLAVOURS_DIR / "flavours.yaml"


def resolve_flavour_image(flavour_id: str) -> str:
    """Resolve a flavour id to a built, runnable image tag, building it from
    its Dockerfile on first use and reusing the cached tag afterward."""
    manifest = yaml.safe_load(FLAVOURS_MANIFEST.read_text())
    entry = next((f for f in manifest if f["id"] == flavour_id), None)
    if entry is None:
        raise ValueError(
            f"Unknown flavour '{flavour_id}' — no entry in {FLAVOURS_MANIFEST}"
        )

    tag = f"termreel-flavour-{flavour_id}"
    inspect = subprocess.run(
        ["docker", "image", "inspect", tag],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if inspect.returncode != 0:
        build_context = (Path(__file__).resolve().parent / entry["dockerfile"]).parent
        subprocess.run(["docker", "build", "-t", tag, str(build_context)], check=True)
    return tag


def start_container(cfg: dict) -> str:
    """Start a detached container we can exec into. Returns container name."""
    docker_cfg = cfg["docker"]
    name = docker_cfg["container_name"]

    # Clean up any leftover container from a previous run.
    subprocess.run(["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    mount_host = str(Path(docker_cfg["mount_host_path"]).resolve())
    Path(mount_host).mkdir(parents=True, exist_ok=True)

    image = resolve_flavour_image(docker_cfg["flavour"])

    cmd = [
        "docker", "run", "-d",
        "--name", name,
        "-v", f"{mount_host}:{docker_cfg['mount_container_path']}",
        "-w", docker_cfg.get("workdir", docker_cfg["mount_container_path"]),
        image,
        "sleep", "infinity",
    ]
    subprocess.run(cmd, check=True)
    return name


def stop_container(name: str):
    subprocess.run(["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _char_delay(base_delay: float, jitter_pct: float, ch: str) -> float:
    jitter = base_delay * jitter_pct
    delay = max(0.01, random.uniform(base_delay - jitter, base_delay + jitter))
    # Occasionally simulate a slightly longer pause (thinking / punctuation).
    if ch in ",.(){}[]" and random.random() < 0.3:
        delay += base_delay * 2
    return delay


def human_type(child: pexpect.spawn, text: str, base_cps: float, jitter_pct: float):
    """Send text one character at a time with randomized delay, like a human typing."""
    base_delay = 1.0 / base_cps
    for ch in text:
        child.send(ch)
        time.sleep(_char_delay(base_delay, jitter_pct, ch))


_QWERTY_ROWS = ["1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"]


def _build_qwerty_adjacency() -> dict:
    adjacency: dict = {}
    for row in _QWERTY_ROWS:
        for i, ch in enumerate(row):
            adjacency[ch] = [row[j] for j in (i - 1, i + 1) if 0 <= j < len(row)]
    return adjacency


QWERTY_ADJACENCY = _build_qwerty_adjacency()


def human_type_with_typos(child: pexpect.spawn, text: str, base_cps: float, jitter_pct: float):
    """Like human_type, but occasionally fat-fingers a nearby key, pauses,
    backspaces, and retypes correctly - write_vim's simulate_typos option."""
    base_delay = 1.0 / base_cps
    for ch in text:
        lower = ch.lower()
        if lower in QWERTY_ADJACENCY and random.random() < TYPO_RATE:
            wrong = random.choice(QWERTY_ADJACENCY[lower])
            wrong = wrong.upper() if ch.isupper() else wrong
            child.send(wrong)
            time.sleep(_char_delay(base_delay, jitter_pct, wrong))
            time.sleep(base_delay * random.uniform(2, 4))  # notice the mistake
            child.send("\x7f")  # backspace
            time.sleep(_char_delay(base_delay, jitter_pct, "\x7f"))
        child.send(ch)
        time.sleep(_char_delay(base_delay, jitter_pct, ch))


def run_command(child: pexpect.spawn, text: str, timing: dict):
    human_type(child, text, timing["base_cps"], timing["jitter_pct"])
    child.send("\r")
    time.sleep(timing.get("settle", 0.3))


def _read_container_file(container_name: str, path: str) -> str | None:
    """Returns the file's current text content, or None if it doesn't
    exist. Runs outside the recorded pty (plain subprocess), so it never
    shows up in the .cast."""
    result = subprocess.run(
        ["docker", "exec", container_name, "cat", path],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def _write_vim_blank(child: pexpect.spawn, content: str, timing: dict, typist):
    child.send(":%d\r")  # clear whatever vim opened with
    time.sleep(0.2)
    child.send("i")
    # vim's own autoindent (left on - see run_write_vim) supplies leading
    # whitespace as each line is typed; typing it ourselves too would
    # double it up. \r is Enter under vim's raw terminal mode, same as
    # everywhere else in this file.
    stripped = "\r".join(line.lstrip() for line in content.split("\n"))
    typist(child, stripped, timing["base_cps"], timing["jitter_pct"])
    child.send("\x1b")


def _insert_lines(child: pexpect.spawn, lines: list, timing: dict, typist, at_eof: bool):
    # 'Go' appends after the last line when inserting past the end of the
    # buffer; 'O' opens a new line above the current one everywhere else,
    # since the cursor is already sitting on the line the insertion should
    # precede.
    child.send("Go" if at_eof else "O")
    stripped = "\r".join(line.lstrip() for line in lines)
    typist(child, stripped, timing["base_cps"], timing["jitter_pct"])
    child.send("\x1b0")


def _edit_line(child: pexpect.spawn, before_line: str, after_line: str, timing: dict, typist):
    """Character-level diff of one changed line: only the differing span
    gets deleted/retyped, the rest of the line is left untouched."""
    offset = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before_line, after_line).get_opcodes():
        if tag == "equal":
            continue
        col = i1 + offset + 1  # 1-indexed vim column, adjusted for edits already applied on this line
        if tag in ("delete", "replace"):
            child.send(f"{col}|{i2 - i1}x")
            offset -= (i2 - i1)
        if tag in ("insert", "replace"):
            child.send(f"{col}|i")
            typist(child, after_line[j1:j2], timing["base_cps"], timing["jitter_pct"])
            child.send("\x1b")
            offset += (j2 - j1)


def _write_vim_diff(child: pexpect.spawn, before: str, after: str, timing: dict, typist):
    """Edits the buffer (currently holding `before`) in place into `after`,
    via a line-level diff with character-level diffing of same-count
    replace blocks - see FR-CLI-010."""
    before_lines, after_lines = before.split("\n"), after.split("\n")
    total = len(before_lines)
    sm = difflib.SequenceMatcher(None, before_lines, after_lines)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        at_eof = i2 >= total  # inserting/replacing past the last before-line
        if tag == "equal":
            n = i2 - i1
            if n:
                child.send(f"{n}j0")
        elif tag == "delete":
            child.send(f"{i2 - i1}dd0")
        elif tag == "insert":
            _insert_lines(child, after_lines[j1:j2], timing, typist, at_eof)
        elif tag == "replace":
            if (i2 - i1) == (j2 - j1):
                for bline, aline in zip(before_lines[i1:i2], after_lines[j1:j2]):
                    _edit_line(child, bline, aline, timing, typist)
                    child.send("j0")
            else:
                child.send(f"{i2 - i1}dd0")
                _insert_lines(child, after_lines[j1:j2], timing, typist, at_eof)


def run_write_vim(child: pexpect.spawn, step: dict, timing: dict, container_name: str):
    content = Path(step["content_file"]).read_text()
    path = step["path"]
    typist = human_type_with_typos if step.get("simulate_typos") else human_type

    base_content = None if step.get("force_blank") else _read_container_file(container_name, path)

    # -n: no swapfile (avoids "swap file exists" prompts on repeat runs).
    # -i NONE: no viminfo file. No indent-related flags - vim's bundled
    # defaults.vim already does `syntax on` + `filetype plugin indent on`,
    # so indentation is driven live by vim itself, same as a real vim
    # setup. Deliberate, accepted trade-off: vim's guessed indent can drift
    # from the source's actual indentation, so a newly-typed line isn't
    # guaranteed byte-identical to content - no correction pass is applied.
    open_cmd = f"vim -n -i NONE {path}"
    human_type(child, open_cmd, timing["base_cps"], timing["jitter_pct"])
    child.send("\r")
    time.sleep(0.5)  # let vim's UI draw before driving it
    child.send("\x1b")  # ensure normal mode

    if not base_content:
        _write_vim_blank(child, content, timing, typist)
    else:
        _write_vim_diff(child, base_content, content, timing, typist)

    child.send(":wq\r")
    time.sleep(timing.get("settle", 0.3))


def do_step(child: pexpect.spawn, step: dict, timing: dict, cols: int, container_name: str):
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

    elif step_type == "write_vim":
        run_write_vim(child, step, timing, container_name)

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
            do_step(child, step, timing, args.cols, container_name)

        # Exit the inner shell, which ends the asciinema recording.
        child.send("exit\r")
        child.expect(pexpect.EOF, timeout=10)

    finally:
        print(f"[*] Stopping container {container_name}")
        stop_container(container_name)

    print(f"[+] Done. Recording saved to {args.out}")


if __name__ == "__main__":
    main()
