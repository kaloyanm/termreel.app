# Traceability

Source for every FR in this baseline is the same: **code audit, 2026-08-30**
(`README.md`, `CLAUDE.md`, `backend/app/**`, `driver.py`, `render.sh`,
`scenario.example.yaml`) — no requirements discussion preceded it. Test
references below are what currently exercises the behavior; blanks are
placeholder gaps, not confirmed absence of coverage elsewhere.

| FR ID | Source | Tests |
|---|---|---|
| FR-CORE-001..004 | `backend/app/routers/projects.py`, `models.py` | `backend/tests/test_api.py::test_project_playlist_scenario_flow` |
| FR-CORE-010..012 | `backend/app/routers/playlists.py`, `models.py` | `backend/tests/test_api.py::test_project_playlist_scenario_flow` |
| FR-CORE-020..023 | `backend/app/routers/scenarios.py`, `models.py`, `serialize.py` | `backend/tests/test_api.py::test_project_playlist_scenario_flow` |
| FR-EDIT-001 | `backend/app/schemas.py::ScenarioStep` | `backend/tests/test_api.py::test_scenario_validation_rejects_bad_step` |
| FR-EDIT-002 | `backend/app/schemas.py::DockerConfig`, `backend/app/routers/scenarios.py` (flavour validation), `driver.py::start_container`, `scenario.example.yaml` | `backend/tests/test_api.py::test_scenario_rejects_unknown_flavour` |
| FR-EDIT-003 | `backend/app/schemas.py::TypingConfig`, `scenario.example.yaml` | — |
| FR-EDIT-004 | `backend/app/routers/scenarios.py::get_scenario_yaml`, `frontend/src/pages/ScenarioEditorPage.tsx` | — |
| FR-EDIT-008 | `backend/app/routers/flavours.py`, `backend/app/flavours.py::load_flavours`, `flavours/flavours.yaml` | `backend/tests/test_api.py::test_list_flavours` |
| FR-REND-001 | `backend/app/routers/jobs.py::start_render` | `backend/tests/test_api.py::test_render_requires_steps` |
| FR-REND-002 | `backend/app/models.py::JobStatus`, `tasks.py` | — |
| FR-REND-003 | `backend/app/render_pipeline.py::_materialize_workspace`, `_materialize_scenario_yaml` | — |
| FR-REND-004 | `backend/app/render_pipeline.py::run_render`, `_run_streaming`, `_ANSI_RE`, `driver.py` (`child.logfile_read`) | — |
| FR-REND-005 | `backend/app/render_pipeline.py::RenderError`, `tasks.py::render_scenario_job` (incl. `traceback.format_exc()`) | — |
| FR-REND-006 | `backend/app/routers/jobs.py::list_jobs`, `get_job`, `serialize.py::job_to_read` | — |
| FR-REND-007 | `frontend/src/components/app/ScenarioCard.tsx`, `ScenarioEditorPage.tsx` | — |
| FR-REND-008 | `backend/app/routers/jobs.py::start_render` (`job_timeout=1800`) | — |
| FR-REND-009 | `backend/app/routers/jobs.py::get_job_log`, `frontend/src/components/app/JobLogDialog.tsx` | — |
| FR-REND-010 | `backend/app/render_pipeline.py::_run_streaming`, `backend/app/tasks.py::render_scenario_job::on_log` | — |
| FR-CLI-001 | `scenario.example.yaml`, `driver.py::load_scenario` | — |
| FR-CLI-002 | `driver.py::start_container`, `stop_container` | — |
| FR-CLI-003 | `driver.py::human_type`, `run_command` | — |
| FR-CLI-004 | `driver.py::do_step` (`comment` branch) | — |
| FR-CLI-005 | `driver.py::do_step` (`write_file` branch) | — |
| FR-CLI-006 | `driver.py::main` (`rec_cmd`, `LC_ALL=C.UTF-8`) | — |
| FR-CLI-007 | `render.sh` | — |
| FR-CLI-008 | `driver.py::do_step` dispatcher, README "Extending the scenario format" | — |
| FR-CLI-009..011 | `driver.py::do_step` (`write_vim` branch), `run_write_vim`, `_write_vim_blank`, `_write_vim_diff`, `_edit_line`, `_read_container_file`, `human_type_with_typos` | — (offline-only sanity check of the diff/keystroke logic against fake input, not an automated test; needs real `docker`+`vim` like the rest of `FR-CLI-*`) |
| FR-CLI-012 | `driver.py::start_container`, `resolve_flavour_image` (flavour resolution + build-on-demand), `flavours/flavours.yaml`, `flavours/rust/Dockerfile` | Manually verified end-to-end against real `docker` (build, cache-hit timing, full `driver.py` run) — not an automated test, same gap as the rest of `FR-CLI-*` |
| FR-EDIT-005 | `backend/app/schemas.py::ScenarioStep` (`write_vim`, `simulate_typos`, `force_blank`) | `backend/tests/test_api.py::test_write_vim_step_round_trip`, `::test_write_vim_requires_path_or_content` |
| FR-EDIT-006 | `frontend/src/components/app/StepEditor.tsx` (Upload file control) | — (no frontend test suite in this repo) |
| FR-EDIT-007 | `backend/app/routers/scenarios.py` (create/update handlers) | `backend/tests/test_api.py::test_write_vim_typing_time_guardrail_rejects_oversized_content`, `::test_write_vim_typing_time_guardrail_allows_small_content` |
| FR-SITE-001 | `frontend/src/pages/Landing.tsx` | — (no frontend test suite in this repo) |
| FR-SITE-002 | `frontend/src/components/marketing/SiteHeader.tsx`, `SiteFooter.tsx` | — |
| FR-SITE-003 | `frontend/src/pages/UseCases.tsx`, `frontend/src/App.tsx` (`/use-cases` route) | — |

**Open gap:** most CLI-pipeline FRs (`FR-CLI-*`) and the render-pipeline
integration ([FR-REND-003](./functional-requirements/render-pipeline.md#fr-rend-003--isolated-per-job-workspace)–[FR-REND-005](./functional-requirements/render-pipeline.md#fr-rend-005--failure-surfaces-to-the-caller))
have no automated test coverage — they depend on real `docker`/`asciinema`/`agg`/`ffmpeg`
and aren't exercised by `backend/tests/test_api.py`, which only covers the
CRUD/API surface.
