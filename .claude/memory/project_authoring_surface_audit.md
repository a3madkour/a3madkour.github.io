---
name: project_authoring_surface_audit
description: "2026-09-27 audit of the full authoring surface — what can be authored from Emacs today and what cannot. Four-tier gap list, decomposed into slices A1/A2/B1/C."
metadata:
  node_type: memory
  type: project
---

**2026-09-27.** Audited every artifact a human must create or edit to publish content,
and what the Emacs-side path is for each. Read from handler registration, data-file
writers and asset paths — not from CLAUDE.md.

## Two mechanism classes

Naming this split is what stopped the design building two pipelines when one of them
should be four small commands.

- **Class A — org through the publish pipeline.** Org file → handler → emitted into the
  site repo, with a manifest entry, an unpublish path and a linter contract. Everything
  shipped so far is class A.
- **Class B — direct site-repo edit.** An Emacs command that opens and edits a site file
  in place with schema awareness (completing-read over the live taxonomy, scaffolds,
  validation). No manifest, no unpublish, no org source. `a3-library-insert-item` is
  already class B in spirit.

Section index pages and curated YAML are class B by nature: they are structural files with
no reason to have an org source. Forcing them through the pipeline would mean inventing an
org representation for a YAML curation list.

## Sections with a handler

Living: `garden`, `library/{reading,listening,playing,watching}`,
`research/{themes,questions}`, `recipes`.
Deliberate: `essays`, `works/poetry`.

## The four-tier gap

1. **No path, real content** — `works/games`, `works/music`. Both are in
   `a3madkour-pub/sections` but registered in neither dispatch alist, so publishing
   errors. → slice **A1**, spec `2026-09-28-works-games-music-handlers-design.md`.
2. **Contested ownership** — `streams`. `tools/poll_streams.py:132` already writes
   `content/streams/<slug>/index.md` as an idempotent auto-stub on live→offline. So
   streams content has a machine author and no human enrichment path. Chosen resolution:
   **poller queues, Emacs adopts** — the poller stops writing bundles and appends to a
   machine-owned capture queue; an Emacs command turns a queue entry into an org file. This
   also dodges a cross-language slug-agreement trap (Python `slugify` vs elisp
   `slug/slugify` would have to agree forever, with no test able to see both — the P3.4
   failure mode across repos). → slice **A2**.
3. **Structural pages** — 19 `_index.md` files including the homepage and all four library
   leaves, plus `about` and `credits`. Hand-edited markdown, no org source, no Emacs
   route. Nobody had named this gap before. → slice **B1**.
4. **Curated YAML** — `filter-chips.yaml`, `library-shelves.yaml`, `library-media.yaml`,
   `streams-schedule.yaml`. Hand-edited, no affordance. (`streams-schedule.yaml` says so
   in its own header: "The cron Action never modifies this file.") → slice **B1**.

Out of scope by choice: icons (hand-drawn by constraint), explorables (code, not content),
`tools/fetch_library_covers.py` (works, but it is the one author-driven step not reachable
from Emacs).

## Data-file ownership

| File | Writer |
|---|---|
| `citations.yaml` | elisp bib resolver, via `a3-sync-citations` |
| `reading/listening/playing/watching.yaml` | elisp `library.el` under living publish |
| `url-history.yaml` | elisp `history.el` (the manifest) |
| `streams-live.yaml`, `streams-twitch-cache.yaml` | Python cron poller |
| `streams-schedule.yaml`, `filter-chips.yaml`, `library-shelves.yaml`, `library-media.yaml` | **hand-edited, no Emacs path** |

## Decisions taken during the brainstorm

- Boundary: tiers 1–4. "Author everything from Emacs" is meant literally.
- Sequencing: handlers first, then the guide (slice C), so the guide never ships with a
  "not yet" section.
- Slicing: A1 (games+music) → A2 (streams) → B1 (direct-edit commands) → C (guide).

## Audit rows deliberately left closed

From the publish-pipeline audit ([[project_publish_pipeline_audit]]), eight rows were
assessed and declined with written rationale: P2.2, P3.2, P3.5, P3.6, P3.8, P4.5, P5.2,
and P3.4. Of these, only **P3.4** (unify `library--title-to-slug` with `slug/slugify` —
NFD vs NFKD, changes library URLs) is a genuine open user decision, and **P3.8** (dedup 13
`with-tmp-*` test macros, mirroring the site's R5.4) is worth doing. The other six should
stay closed; reopening them is churn, not close-out.
