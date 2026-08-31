# CLI recording & rendering pipeline (`FR-CLI-*`)

The original, standalone tool (`driver.py` + `render.sh` at repo root). This
is the pipeline the web app wraps rather than replaces — every FR here is
also, transitively, a dependency of [FR-REND-*](./render-pipeline.md).

## FR-CLI-001 — Author a scenario file

- **Priority:** Must
- **Statement:** An author hand-writes a scenario as a YAML file with a
  title, a `docker` block, a `typing` block, and an ordered `steps` list,
  per `scenario.example.yaml`.
- **Dependencies:** Same step/config shape as
  [FR-EDIT-001](./scenario-authoring.md#fr-edit-001--step-schema-validation)–[FR-EDIT-003](./scenario-authoring.md#fr-edit-003--typing-style-config),
  since the web app's DB rows serialize to exactly this format.

## FR-CLI-002 — Start and tear down the container

- **Priority:** Must
- **Statement:** Recording a scenario starts a detached, disposable Docker
  container with the scenario's source directory mounted in, and always
  removes it afterward, success or failure.
- **Acceptance criteria:**
  - Any pre-existing container with the same `container_name` is force-removed
    before starting (`docker rm -f`), so re-running a scenario is idempotent.
  - The host mount directory is created if missing
    (`Path(mount_host_path).mkdir(parents=True, exist_ok=True)`).
  - The container runs `sleep infinity` and is driven via `docker exec`,
    not `docker run` per step.
  - The container is force-removed in a `finally` block regardless of how
    recording ends (`stop_container`).

## FR-CLI-003 — Record with human-like typing

- **Priority:** Must
- **Statement:** Commands and comments are typed character-by-character
  into the container's shell with randomized per-character delay (and
  occasional longer pauses at punctuation) so the recording looks
  human-typed rather than pasted.
- **Acceptance criteria:**
  - Delay per character is drawn from `base_cps` ± `jitter_pct`, floored at
    `0.01s`.
  - A char in `,.(){}[]` has a 30% chance of an extra ~`2×base_delay` pause.
  - The whole session (the `docker exec` pty) is captured to a `.cast` file
    via `asciinema rec --overwrite --window-size <cols>x<rows>`.

## FR-CLI-004 — Comment step line-wrapping

- **Priority:** Must
- **Statement:** Narration (`comment` steps) is wrapped into multiple short
  `# ...` lines, each its own real Enter-terminated command, instead of one
  long line — because a single line typed past the pty's column width
  desyncs the terminal and bash's readline on wrap, corrupting the display.
- **Acceptance criteria:**
  - Each comment step's `text` is wrapped with `textwrap.wrap(..., width=max(20,
    cols-4))` and each resulting line is typed and Entered separately.

## FR-CLI-005 — write_file steps

- **Priority:** Must
- **Statement:** A `write_file` step visibly types the heredoc opening
  line, then pastes the target file's full content in one shot (not
  character-by-character) to write it into the container.
- **Acceptance criteria:**
  - Content is read from `content_file` and has tabs expanded to 4 spaces
    before sending — a raw tab byte reaching interactive bash's readline is
    interpreted as a completion request, which can silently splice a
    completed filename into the file instead of a literal tab.
  - The opening `cat > <path> << 'EOF'` line is typed with the same
    human-typing timing as commands; the body and closing `EOF` are sent
    as raw writes.

## FR-CLI-006 — Locale forced for multi-byte narration

- **Priority:** Must
- **Statement:** The container shell always runs with a UTF-8 locale, so
  non-ASCII comment text doesn't corrupt line-wrap rendering.
- **Acceptance criteria:**
  - `docker exec` is invoked with `-e LC_ALL=C.UTF-8`; base images (e.g.
    `golang:*`) ship with no locale configured, which otherwise makes
    bash's readline miscompute on-screen column width for multi-byte
    characters.

## FR-CLI-007 — Render cast to gif and mp4

- **Priority:** Must
- **Statement:** Given a `.cast` file, an output basename, and a theme,
  produce a themed `.gif` and a web-ready `.mp4` from it.
- **Acceptance criteria:**
  - `agg --theme <theme> --font-size 18 --speed 1.0 <cast> <base>.gif`
    produces the GIF; theme defaults to `dracula` if omitted.
  - `ffmpeg` converts that GIF to `<base>.mp4` with `-movflags faststart
    -pix_fmt yuv420p` and even-dimension scaling
    (`scale=trunc(iw/2)*2:trunc(ih/2)*2`).
  - `render.sh` exits non-zero (`set -euo pipefail`) if either stage fails,
    which the web app relies on to detect failure
    ([FR-REND-005](./render-pipeline.md#fr-rend-005--failure-surfaces-to-the-caller)).

## FR-CLI-008 — Extensible step types

- **Priority:** Could
- **Statement:** New step types can be added without restructuring the
  pipeline.
- **Acceptance criteria:**
  - Adding a step type means adding one branch to `do_step()` in
    `driver.py` and a corresponding block to the YAML schema — no other
    coupling exists between step types.
