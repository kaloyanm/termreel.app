# Changelog

## 2026-08-30 — Initial baseline

- Created the requirements mdBook (`requirements/`) via the `requirman`
  skill, seeded entirely from a code audit rather than a discussion.
- Added `FR-CORE-001..023` (project/playlist/scenario CRUD + cascade
  delete), `FR-EDIT-001..004` (step validation, env/typing config, YAML
  export), `FR-REND-001..008` (render job lifecycle, workspace isolation,
  failure handling, polling, timeout), `FR-CLI-001..008` (standalone
  record/render pipeline).
- Added `NFR-001..008` covering auth posture, the "don't reimplement
  driver.py/render.sh" invariant, separate uv projects, cascade-delete
  media-cleanup gap, polling-only status, render timeout, external tool
  deps, and data storage layout.

### Open questions (TBD, not invented)

- Should cascade-deleting a project/playlist/scenario also delete its
  render jobs' media files on disk ([NFR-004](./non-functional-and-constraints.md#nfr-004--cascade-deletes-do-not-clean-up-media-on-disk))?
  No stated intent either way in the code.
- Is single-operator/no-auth ([NFR-001](./non-functional-and-constraints.md#nfr-001--no-auth--single-operator-tool))
  a permanent product decision or a placeholder for a future accounts
  feature? Undecided as of this baseline.
