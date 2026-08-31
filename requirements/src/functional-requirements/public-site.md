# Public marketing site (`FR-SITE-*`)

The public marketing site is a small set of unauthenticated pages, separate
from the `/app/*` product shell, that pitches termreel to a prospective
visitor and links into the app. It has no backend/API surface of its own —
purely static frontend routes and content.

## FR-SITE-001 — Landing page

- **Priority:** Must
- **Statement:** A prospective visitor loads `/` and sees a marketing page
  explaining what termreel does and how it works, with a call to action into
  the authenticated app.
- **Acceptance criteria:**
  - `/` renders a hero (headline + one-line pitch), a "How it works" section
    (write a scenario → real execution → recorded, not filmed → rendered to
    video), a "Built for series, not one-offs" feature section (Projects /
    Playlists / Scenario editor), and a closing CTA card linking to
    `/app/projects`.
  - No authentication is required to view it, consistent with
    [NFR-001](../non-functional-and-constraints.md#nfr-001--no-auth--single-operator-tool).

## FR-SITE-002 — Shared site header and footer

- **Priority:** Should
- **Statement:** Every public marketing page shares one header (logo linking
  home, a nav to other marketing pages, an "Open app" button into
  `/app/projects`) and one footer, so chrome stays consistent as more
  marketing pages are added.
- **Acceptance criteria:**
  - `SiteHeader`/`SiteFooter` components are used by every top-level
    marketing route (currently `/` and `/use-cases`); no page duplicates
    the header/footer markup inline.
  - The header nav includes a link to `/use-cases`.
- **Status:** Implemented 2026-08-31 (extracted from `Landing.tsx`'s
  previously-inlined header/footer when `/use-cases` was added).

## FR-SITE-003 — Use cases page

- **Priority:** Should
- **Statement:** A prospective visitor navigates to `/use-cases` and sees a
  set of concrete use cases for the product (who it's for and what they'd
  build with it), ending on the same call-to-action as the landing page.
- **Acceptance criteria:**
  - `/use-cases` is reachable from the site header nav on every marketing
    page.
  - The page renders a grid of use cases, each with an icon, a short title,
    and a one-to-two-sentence description.
  - The page ends with the same "Ready to record your next episode?" CTA
    card (linking to `/app/projects`) used on the landing page.
- **Status:** Implemented 2026-08-31.
