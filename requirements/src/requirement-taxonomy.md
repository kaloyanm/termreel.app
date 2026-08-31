# Requirement taxonomy

## ID scheme

`FR-<domain>-<number>`, three-digit number, stable for the life of the
requirement once assigned (preserve/update/extend, never renumber).

| Domain prefix | Chapter |
|---|---|
| `CORE` | [Project / playlist / scenario management](./functional-requirements/core-management.md) |
| `EDIT` | [Scenario authoring & export](./functional-requirements/scenario-authoring.md) |
| `REND` | [Render pipeline (web app)](./functional-requirements/render-pipeline.md) |
| `CLI` | [CLI recording & rendering pipeline](./functional-requirements/cli-pipeline.md) |

Non-functional constraints use `NFR-###` and live in
[Non-functional requirements & constraints](./non-functional-and-constraints.md);
they are referenced from FRs where they bound behavior (e.g. render timeout).

## Priority levels (MoSCoW)

- **Must** — the system does not meaningfully function without this; already
  load-bearing in the current implementation.
- **Should** — present and working today, but the product is usable without
  it in a degraded form.
- **Could** — documented capability/extension point, not a mandatory
  behavior (e.g. "the format is extensible").

## Status of this baseline

Every FR in this book was captured by **auditing the existing codebase**
(README.md, CLAUDE.md, `backend/app/**`, `driver.py`, `render.sh`,
`scenario.example.yaml`) on 2026-08-30, not from a requirements discussion.
They describe the system **as it behaves today** (brownfield "as-is"
documentation per the skill's editing rules) — no aspirational behavior has
been invented. Future discussions should update/extend these via the normal
preserve/update/extend workflow, recording deltas in the
[Changelog](./changelog.md).

Starting 2026-08-31, FRs/criteria agreed in a design discussion but **not
yet implemented** are marked `**Status:** Planned — not yet implemented` at
the point they're added, so the baseline never silently claims shipped
behavior that isn't there. Once built, the Planned marker is replaced with
an `Implemented <date>` status as part of that PR (no ID renumbering) — see
[FR-REND-009](./functional-requirements/render-pipeline.md#fr-rend-009--detailed-render-log-available-on-demand)/[FR-REND-010](./functional-requirements/render-pipeline.md#fr-rend-010--render-log-streams-while-the-job-runs)
for the first FRs to go through the full planned → implemented cycle, same
day.
