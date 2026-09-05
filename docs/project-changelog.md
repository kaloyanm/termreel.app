# Project Changelog

This document tracks significant changes and milestones in Termreel's development.

## 2026-09-01 — Presenterm Step Type

A new step type, `presenterm`, renders Markdown files as full-screen terminal slideshows via the presenterm tool. The step writes slide content into the container silently (never appearing in the recording) and drives slide-advance keystrokes automatically from an auto-detected slide count.

**Implementation notes:**
- Content is written to the container via an unrecorded subprocess, keeping markdown source out of the terminal recording
- Slide count is computed as: the number of `<!-- end_slide -->` markers in the body, plus 1, plus 1 more if the file opens with a YAML front matter block
- The step sends a synthetic Device Attributes response to unblock presenterm's terminal probe (normally answered by a real terminal emulator)
- Includes a configurable `slide_pause` field (default 2.0s) controlling the delay before each slide advance
- Added to the existing `rust` flavour via a prebuilt musl release binary (avoiding Rust MSRV mismatches and glibc coupling)

**Verified:** End-to-end against real Docker + presenterm, including two bugs surfaced and fixed the same day (release tarball extracts to a versioned subdirectory, and presenterm blocks on terminal attributes).

**Known limitations:** `<!-- pause -->` incremental-reveal markers not supported; no per-slide pause durations; no guardrail on total presentation time (`slide_count × slide_pause`); these are accepted v1 gaps.

## 2026-08-31 — Use Cases Marketing Page

Added a second public marketing page at `/use-cases` that clearly articulates what Termreel is for and who it serves. The page includes a grid of concrete use cases (educators, devtools maintainers, solo content creators, etc.) and links back to the main app.

**Implementation:** Extracted `SiteHeader` and `SiteFooter` components from the Landing page so both marketing routes share consistent chrome. Added a `/use-cases` route to the frontend router.

## 2026-08-31 — Flavours: Pre-Built Docker Environments

Replaced the previous free-text `docker.image` field with a fixed `docker.flavour` catalog. Scenarios now select from pre-built, pre-tested environments (currently: "Rust 1.60.0 with vim, git, and presenterm") instead of typing raw image references.

**Implementation details:**
- Flavours are declared in `flavours/flavours.yaml` manifest and live as `flavours/{id}/Dockerfile` directories
- On-demand build with tag-based caching: first call for a flavour builds the image and tags it `termreel-flavour-{id}`; subsequent calls check tag existence (fast)
- Flavour resolution lives in `driver.py`'s `start_container()` to preserve standalone CLI usability
- Backend validates `docker.flavour` against the manifest at scenario save time (422 on unknown id)
- Frontend fetches `/api/flavours` once and joins display names client-side (no denormalization into every Scenario response)

**Trade-off:** Caching is by Docker image tag, not by Dockerfile content hash. Editing a flavour's Dockerfile requires a manual `docker rmi termreel-flavour-{id}` to force a rebuild.

## 2026-08-31 — Write_vim Step Type

A fourth step type, `write_vim`, visibly types file content into vim in the recorded terminal, character by character, so the recording reads as live programming rather than a heredoc paste.

**Implementation details:**
- **Blank mode:** Opens vim with no swapfile/viminfo, clears the buffer, types content with vim's own autoindent left on, and saves with `:wq`
- **Diff/live-edit mode:** Reads the existing file from the container via `docker exec` (outside the recorded PTY), computes a character-level diff, and drives vim motions (navigate, delete, insert) to transform the file in place
- **Typo simulation:** Optional per-step toggle (`simulate_typos`) adds occasional human-like typos (wrong nearby key, pause, backspace, correct character)
- **Typing-time guardrail:** Rejects scenarios at save time if a `write_vim` step's content would take > 60 seconds to type (prevents accidental multi-minute renders)
- **Indentation trade-off:** Vim's own autoindent is left on for visual authenticity; no correction pass ensures exact byte-for-byte reproduction

**File seeding:** Both `write_file` and `write_vim` steps support client-side file upload, populating `content` from a local file instead of manual text entry.

## 2026-08-31 — Detailed Render Logs with Streaming

Expanded render job logging from a single-line error string to a full streaming log showing the in-container terminal session, driver.py progress, and agg/ffmpeg output.

**Changes:**
- `driver.py` mirrors the pexpect PTY session to its stdout (previously only infra-level output was captured)
- Backend switches from buffered `subprocess.run(capture_output=True)` to `subprocess.Popen` with incremental line reads
- Log output is streamed to the database via callback every ~0.5s, not buffered until process exit
- ANSI/terminal control sequences are stripped before storage for clean plaintext logs
- Added a new `GET /api/jobs/{id}/log` endpoint and a "View logs" dialog in both the scenario card and scenario editor
- Frontend polls the log endpoint every 2 seconds while the job runs

**Result:** A failed render now reveals detailed diagnostics (e.g. "bash: asciinema: command not found") instead of a generic error string. The catch-all exception handler also appends full tracebacks to the log.

## 2026-08-30 — Initial Baseline

Captured the initial, working state of the codebase via code audit:

- Core CRUD (projects, playlists, scenarios, render jobs) with cascade-delete semantics
- Step types: `command`, `comment`, `write_file`
- Docker container orchestration with pexpect PTY recording
- Async render queue (RQ + Redis) with job status polling
- SQLModel ORM with JSON columns for scenario config and steps
- React frontend with project/playlist/scenario browsing and scenario editor
- CLI pipeline (`driver.py` + `render.sh`) as standalone tool
- Marketing landing page

### Open Questions from Initial Baseline

1. **Media cleanup on cascade delete:** Should deleting a project also delete its render jobs' media files on disk? Currently, only database rows cascade; media files persist indefinitely.

2. **Authentication:** Is the current single-operator, no-auth model permanent, or a placeholder for a future multi-user accounts feature?

Both documented as open decisions (not defects or design oversights) to be resolved based on product feedback.
