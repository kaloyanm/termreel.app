# Project Roadmap

This roadmap is based on open items actually documented in the codebase, not invented features. It reflects decisions that are genuinely pending or capabilities that are intentionally deferred.

## Current Status (as of 2026-09-05)

**Version**: Pre-release (v0.1)

**Stability**: Feature-complete for the core recording/rendering loop. All critical paths (project/scenario authoring, async render queue, multi-step scenarios, render logging) are implemented and tested.

**Test Coverage**: API integration tests exist for CRUD flow, step validation, flavour resolution, and typing guardrails. End-to-end tests against real Docker/asciinema/agg/ffmpeg are a documented gap — most CLI-pipeline features depend on these external tools and aren't exercised by the automated test suite.

## Open Decisions (Blocking Future Roadmap)

These are genuine product questions, not technical unknowns. Resolution of these will shape the roadmap.

### 1. Authentication & Multi-User Support (Strategic)

**Current state**: No authentication; single-operator tool with global read/write access to all projects/scenarios.

**Question**: Should Termreel eventually support multiple users with per-project access control, or remain a single-operator personal tool?

**Impact**:
- If **No**: Deployment stays simple; no session management, no user model, no RBAC.
- If **Yes**: Requires a major architectural change (add User model, auth flow, permission checks in all routers).

**Status**: Open question as of baseline (2026-08-30).

### 2. Media Cleanup on Cascade Delete (Technical)

**Current state**: Deleting a project cascades all database rows (playlists, scenarios, jobs) but does not delete the corresponding media files on disk (`backend/data/media/{job_id}/`).

**Question**: Should cascade delete also clean up media files, or is the current behavior (accumulate media indefinitely) intentional?

**Impact**:
- If **cleanup now**: Add cascade-aware cleanup logic to `routers/projects.py`, `routers/playlists.py`, `routers/scenarios.py` delete handlers. Risk: slow cascade deletes on projects with many rendered jobs.
- If **defer**: Media cleanup is a future FR when disk usage becomes a problem. Current behavior is acceptable for a single-operator tool.

**Status**: Open question as of baseline (2026-08-30).

## Candidate Future Enhancements (Prioritized)

These are capabilities identified during development but not blocking v0.1. They would address real limitations.

### A. Per-Slide Timing for Presenterm (Medium Effort)

**Current state**: All slides advance at the same fixed `slide_pause` interval.

**Desired**: Support per-slide pause intervals via `<!-- pause: X.Y -->` markers in the markdown content, or a per-slide pause list in the schema.

**Rationale**: Some slides may need more time to read than others; uniform timing is a first-pass simplification.

**Scope**: Backend schema change (optional `pauses` array on `presenterm` step), UI form update, `driver.py` update to respect per-slide pauses.

**Status**: Documented in changelog 2026-09-01 as an "accepted v1 gap, rather than bundled into presenterm step."

### B. Render-Length Guardrail for Presenterm (Low Effort)

**Current state**: No guardrail on total presentation time (slide_count × slide_pause); a scenario with 100 slides at 10s each would queue a 1000s render.

**Desired**: Warn (or reject) at scenario save time if presentation would take too long.

**Rationale**: Parallel to the `write_vim` typing-time guardrail; prevents accidental long renders.

**Scope**: Backend validation in `routers/scenarios.py` (add per-step estimate logic for `presenterm`), UI error message.

**Status**: Documented in changelog 2026-09-01 as "explicitly deferred as an accepted v1 gap."

### C. Incremental Reveals for Presenterm (Medium Effort)

**Current state**: `presenterm` slides advance as whole blocks; no mid-slide pauses.

**Desired**: Support presenterm's built-in `<!-- pause -->` marker for incremental reveals (bullet points appearing one at a time).

**Rationale**: More sophisticated presentations, especially tutorials with step-by-step walkthroughs.

**Scope**: Backend schema change (optional `incremental_reveals` flag), UI form update, `driver.py` pass-through of pause markers.

**Status**: Documented in changelog 2026-09-01 as "not support ... (deferred to a future iteration)."

### D. Push Notifications for Render Status (Low Effort)

**Current state**: Frontend polls `/api/jobs/{id}` every 2 seconds.

**Desired**: WebSocket or Server-Sent Events (SSE) for real-time status updates.

**Rationale**: Eliminates polling overhead; smoother UX for waiting on renders.

**Scope**: Add WebSocket handler to FastAPI, emit events as job status changes, frontend subscribes.

**Constraints**: Revisit only if concurrent-job volume grows (single-operator tool doesn't need this today).

**Status**: Deferred; acceptable at current scale (2026-08-30 baseline).

### E. Per-Step Timeout & Error Recovery (Medium Effort)

**Current state**: If a shell command hangs, the entire render hangs indefinitely.

**Desired**: Per-step timeout; failed steps trigger skip/abort dialog (or auto-skip based on policy).

**Rationale**: Robustness; production-grade error recovery.

**Scope**: Backend timeout per step (not just global 30-min render timeout), pexpect timeout configuration, RQ job handler for timeout recovery.

**Constraints**: Requires interaction with the user mid-render (skip/abort) or a skip-policy field in the scenario schema.

**Status**: Documented in README.md as a known rough edge: "No error recovery mid-recording — if a command hangs, the script hangs."

### F. Flavour Pre-Build & Registry (Low Effort)

**Current state**: Flavours are built on-demand and cached locally by Docker tag.

**Desired**: Pre-build flavours and push to a Docker registry (e.g., Docker Hub, private registry) for faster cold-start in production.

**Rationale**: Deployment scalability; no need to rebuild flavours on every container start.

**Scope**: CI/CD step to build and push flavour images, backend configuration to pull from registry instead of building.

**Status**: Not yet documented as a gap; candidate enhancement.

### G. Scenario Templates & Presets (Medium Effort)

**Current state**: Every scenario is authored from scratch.

**Desired**: Template library (e.g., "Go CLI demo", "Rust web server", "Node.js API") with pre-configured docker/typing/steps.

**Rationale**: Accelerates scenario authoring for common patterns.

**Scope**: New `Template` model and API resource, frontend template browser, copy-template-to-scenario flow.

**Status**: Not yet documented; candidate enhancement.

### H. Scenario Import/Export (Low Effort)

**Current state**: Scenarios exist only in the DB; no standardized export beyond the YAML endpoint.

**Desired**: Export full project as ZIP (all scenarios + media) or import scenarios from YAML files.

**Rationale**: Portability; sharing scenario collections with other users; version control of scenarios.

**Scope**: New endpoints `/api/projects/{id}/export` (ZIP), `/api/projects/import` (ZIP), frontend UI.

**Status**: Not yet documented; candidate enhancement.

### I. Database Migration to PostgreSQL (Medium Effort)

**Current state**: SQLite (single-operator, suitable for dev; not for production concurrency).

**Desired**: Migrate to PostgreSQL for production deployments (multi-operator, concurrent renders).

**Rationale**: Scalability; production-grade reliability.

**Scope**: Update `backend/config.py` to support PostgreSQL connection string, add Alembic migration framework, backfill existing SQLite data, test with docker-compose.

**Constraints**: Blocked on deciding whether multi-user support (Open Decision #1) is desired.

**Status**: Not yet documented as a gap; candidate enhancement.

## Known Limitations (Accepted as v0.1)

These are not blocking ship; they're acknowledged trade-offs or gaps.

| Limitation | Status | Mitigation |
|---|---|---|
| No auth / no RBAC | Accepted | Single-operator assumption |
| Media not cleaned on cascade delete | Accepted | Monitor disk usage; see Open Decision #2 |
| Polling-only status (no websockets) | Accepted | Sufficient for single operator |
| Per-step timeouts missing | Accepted | Known rough edge; if command hangs, render hangs |
| Frontend has 3 polling loops (not consolidated) | Technical debt | Works; refactor later for elegance |
| Manual TypeScript type mirroring | Technical debt | No codegen; kept in sync manually |
| End-to-end render tests missing | Test coverage gap | CLI features need real docker/asciinema/ffmpeg |

## Release History

### v0.1 (Current, pre-release)

**Implemented Features**:
- Project/Playlist/Scenario CRUD with cascade delete
- Interactive scenario authoring form
- Five step types: command, comment, write_file, write_vim, presenterm
- YAML export (matches CLI pipeline format exactly)
- Async render queue (RQ) with 30-min timeout
- Detailed render logs (streamed in real-time)
- Docker flavours (pre-built environments)
- Flavour validation at scenario save time
- Typing-time guardrail for write_vim
- Landing page + Use Cases marketing pages
- Local dev stack (`./dev.sh`)

**Date**: 2026-08-30 (baseline audit), 2026-08-31 (write_vim/flavours/detailed logs), 2026-09-01 (presenterm)

---

## Next Steps for Contributors

1. **If adding a new feature**: Check this roadmap and the [Project Changelog](./project-changelog.md) for implementation history and context. Update this file if the feature is planned or aligns with a candidate enhancement.

2. **If encountering the auth limitation**: Don't add ad-hoc auth; refer to Open Decision #1. Multi-user support is a breaking architectural change, not an incremental feature.

3. **If adding new step types**: Update `driver.py`'s `do_step()` dispatcher, add schema to `backend/app/schemas.py`, add form UI to `frontend/src/components/app/StepEditor.tsx`, add tests to `backend/tests/test_api.py`.

4. **If scaling to multiple operators**: Revisit Open Decisions #1 (auth) and #2 (media cleanup), consider Candidate Enhancement #I (PostgreSQL), and re-prioritize the roadmap.

---

## Related Documentation

- **[Project Overview & PDR](./project-overview-pdr.md)**: Product scope, success metrics, and architectural decisions.
- **[System Architecture](./system-architecture.md)**: Data flow, component interactions, database schema.
- **[Code Standards](./code-standards.md)**: Coding conventions, patterns, extensibility points.
- **[Project Changelog](./project-changelog.md)**: Implementation history and design decisions by date.
