---
name: mdbook-functional-requirements
description: >-
  Maintains a functional requirements mdBook under requirements/ from ongoing
  discussions. Preserves, updates, and extends FRs with a fixed chapter structure
  for any project (greenfield or legacy). Use when the user or conversation
  covers functional requirements, acceptance criteria, scope, FR IDs,
  traceability, or asks to sync or update the requirements book.
---

# mdBook functional requirements sync

## When to apply

- The discussion involves **functional requirements**: features, changes, scope, acceptance criteria, priorities, traceability, or FR wording.
- The user asks to **update**, **sync**, **extend**, or **document** requirements in the book.
- Unless the user opts out, **treat ongoing chat as input** to the book after substantive FR discussion.

## Book location

- **Root:** `requirements/` (mdBook project: `book.toml`, `src/SUMMARY.md`, chapters under `src/`).
- Standard tool: [mdBook](https://rust-lang.github.io/mdBook/).

## Principles: preserve, update, extend

1. **Preserve** — Do not remove or rewrite history silently. Prefer marking items *superseded*, *deprecated*, or *migrated* with dates and IDs. Delete only when the user explicitly asks.
2. **Update** — When meaning changes, edit the right sections; keep **stable FR IDs** when the requirement is the same idea with clearer wording. Add a short **change note** (date + reason) when useful.
3. **Extend** — New capabilities → new sections/FRs and new IDs following the taxonomy below. Record everything in **Changelog**.

## Fixed structure (all projects)

Use this **outline and order** in `SUMMARY.md` and chapter files. Do not reorder top-level parts unless the user explicitly requests renames.

| # | Chapter | Contents |
|---|---------|----------|
| 1 | Introduction | Scope, release/product focus, audience, glossary, **out of scope** |
| 2 | Actors & context | Users, external systems, boundaries; optional mermaid context diagram |
| 3 | Requirement taxonomy | ID scheme (e.g. `FR-###`), priority levels (Must/Should/Could), link to epics/stories if used |
| 4 | Functional requirements | Numbered FRs (one behavior per ID). May be **split by domain** (e.g. negotiation, compensation, experience, localization) as separate files under `src/`; keep **stable FR IDs** across moves. Tables for compactness are OK if no detail is dropped. |
| 5 | Non-functional & constraints | Cross-links; FRs reference NFRs when they bound behavior |
| 6 | Traceability | FR ID → source (e.g. discussion date / ticket) → tests (placeholders OK) |
| 7 | Changelog | Dated entries: what changed, which FR IDs, why |

## FR content pattern

Each functional requirement should include where applicable:

- **ID**, **name**, **priority**
- **Statement:** actor → trigger → system behavior → outcome (implementation-neutral)
- **Preconditions / postconditions**
- **Acceptance criteria** (testable bullets or Given/When/Then)
- **Data & validation** (tables OK)
- **Dependencies** (other FRs or external systems)

## Editing rules

- After substantive FR discussion, **edit the mdBook files**, not only a chat summary.
- **Conflicts:** follow the latest explicit user decision; if unclear, add **TBD** and list open questions—do not invent requirements.
- **Legacy vs new:** document **as-is** first for brownfield; use Changelog for agreed deltas. Same skeleton either way.
- **Wording:** FR statements stay behavior-focused; put technology in assumptions or a **Technical constraints** subsection.

## After updates

Briefly report **which files changed** and which **FR IDs** were added, updated, or deprecated.
