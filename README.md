# yt-terminal-recorder

A prototype pipeline for generating "automated coding session" YouTube videos:
a scenario file describes what happens, a script types it into a real Docker
container, and the session is recorded and rendered to video.

```
scenario.yaml --> driver.py --> session.cast --> render.sh --> mp4
                     |
                     +-- starts a Docker container
                     +-- drives it via a pty (pexpect)
                     +-- asciinema records the whole terminal session
```

## Why this approach

- **Reproducible**: the scenario file is the single source of truth. Re-run
  it and you get the same episode again (useful if a take goes wrong,
  or you want to change theme/font after the fact).
- **Real code execution**: because it's an actual Docker container, `go run`,
  test failures, compiler errors, etc. are all genuine — not faked text.
- **Decoupled recording from rendering**: `asciinema` records structured
  terminal events (timing + text), not pixels. You can restyle the video
  (theme, font, speed) without re-running the container.

## Setup

```bash
pip install -r requirements.txt
# also needs on PATH: docker, asciinema, agg, ffmpeg
```

- Docker: https://docs.docker.com/get-docker/
- asciinema: https://asciinema.org/docs/installation
- agg (cast -> gif renderer): https://github.com/asciinema/agg
- ffmpeg: standard package manager install

## 1. Write a scenario

See `scenario.example.yaml`. Key fields:

- `docker.image` / `mount_host_path`: what environment and source code
  the episode uses (mounted into the container so it's inspectable/editable).
- `typing.base_cps` / `jitter_pct`: how "human" the typing looks.
- `steps`: the ordered list of things that happen — `command`, `comment`
  (a typed `# ...` line for narration-in-terminal), or `write_file`
  (types a heredoc header, then pastes a file's contents in).

## 2. Record

```bash
python3 driver.py scenario.example.yaml --out session.cast
```

This starts the container, execs into it via `asciinema rec`, types out
each step with jittered timing, then tears the container down.

## 3. Render

```bash
./render.sh session.cast episode01 dracula
```

Produces `episode01.gif` and `episode01.mp4`. Swap the theme argument for
any asciinema-supported theme, or tweak font size/speed in `render.sh`.

## 4. Post-process (outside this repo)

Drop `episode01.mp4` into your editor of choice to add voiceover, music,
intro/outro, captions, etc. Since the terminal recording is just one clean
layer, this composits easily.

## Extending the scenario format

The `do_step()` function in `driver.py` is a small dispatcher — adding a
new step type (e.g. `run_editor` to drive `vim`/`nano` on screen, or
`split_pane` for a tmux layout) just means adding a new branch there and
a corresponding block in the YAML schema.

## Known rough edges (this is a sketch, not production)

- No error recovery mid-recording — if a command hangs, the script hangs.
  A production version would add `pexpect` timeouts per step and a
  "skip/abort" path.
- `write_file` pastes content in one shot rather than typing it — typing
  a whole file character-by-character is slow and rarely looks better on
  screen; consider a fast "paste" animation instead if you want more polish.
- Terminal size, font, and color scheme are only controlled at render time
  (via `agg`/theme), not at record time — good for flexibility, but means
  what you see in a live `asciinema play` differs from the final render.
- No audio/narration sync logic yet — timing narration to `pause_after`
  values is currently manual.
