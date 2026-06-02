---
name: b-slug-on-concept-followup
description: "B.1.1 garden handler emits `slug:` frontmatter on every published garden bundle. The garden-fixtures linter rejects `slug` on concept-flavor notes, so any ref-note promoted to garden via `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden` fails CI. Workaround applied 2026-06-02: hand-edit slug out of the bundle. Durable fix: B emits without slug on concepts (or linter adds slug to concept allowlist)."
metadata:
  node_type: memory
  type: project
---

**Status:** queued for B.1.x follow-up. Workaround applied 2026-06-02; durable fix pending.

## The bug

When a ref-note (`~/org/notes/ref-notes/<key>.org`) gets promoted to a garden bundle via `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`, B.1.1's garden handler emits the bundle's frontmatter with an explicit `slug: "<dir-name>"` field.

`tools/check_garden_fixtures.py` enforces strict per-flavor field allowlists:

```python
CONCEPT_FIELDS = ALWAYS_REQUIRED | {"tags", "summary", "topic_map", "roam_refs", "year", "weight", "source_stream"}
```

`slug` is **not** in `CONCEPT_FIELDS` (nor in `MEDIA_FIELDS` or `REFERENCE_FIELDS`). So the linter fails on any concept-flavor bundle that carries it:

```
content/garden/mei-r-wom-2026/index.md: 'slug' not permitted on concept notes
```

## How it bit us

F's spot-check (2026-06-01) promoted `~/org/notes/ref-notes/meiRWoMRetrievalaugmentedWorld2026.org` to a garden bundle at `content/garden/mei-r-wom-2026/`. The bundle landed with `slug:`. The fixture commit `930bcec` (F session) shipped it without checking that linter pair locally, so it slipped into origin/master.

The site CI failed on that exact line **six pushes in a row** (F backfill, F merge, C memory, C math validator, D.1 cleanup, D.1 affordance-strip) over ~13 hours before anyone caught it. Discovered during D.1's "prepare for next session" checklist when `gh run list` surfaced consecutive failures.

This was a process miss per [[feedback-always-run-ci-locally]] — the local-CI script catches this kind of thing.

## Workaround applied 2026-06-02

Hand-edited `content/garden/mei-r-wom-2026/index.md` to remove the `slug:` line. Hugo derives the URL path from the bundle directory name (`/garden/mei-r-wom-2026/`) regardless, so the URL is unchanged.

The next time the author publishes a ref-note as garden, B.1.1 will re-emit `slug:` and CI will fail again unless the durable fix is shipped.

## Durable fix options

**Option A — Fix B's emit (recommended).** Update `a3madkour-publish-garden.el` to skip the `slug:` field when the bundle directory name already matches what the slug would be (which is always, for the default case). Net effect: no slug emitted for any garden bundle.

- Pro: clean output, matches what the linter wants.
- Con: small handler edit; ert sibling update.
- Where: dotfiles `a3madkour-publish-garden.el` — find the frontmatter assembly and remove the slug line.

**Option B — Add slug to CONCEPT_FIELDS in the linter.** Loosen `tools/check_garden_fixtures.py` to permit `slug:` on all three garden flavors (concept/media/reference).

- Pro: tiny site-side change; no dotfiles touched.
- Con: doesn't solve the underlying "we emit data the linter says we shouldn't" oddness. Allowlists are there for a reason; adding fields to satisfy a buggy emitter is the wrong direction.

**Option C — Both.** Strip in B (durable), loosen the linter (defense-in-depth in case future emitters add slug back).

Recommend A (clean fix in B). C if other handler-side emit-then-lint mismatches show up.

## Triggers to do this

- Next time the author promotes a ref-note to garden (otherwise it bites again).
- Or as part of any B.1.x follow-up batch.
- Could land alongside ([[b4-complete]] follow-up #1 — orphan-sweep over-deletion) since both are B.x.

## Pre-work reads

1. `a3madkour-publish-garden.el` — frontmatter assembly for garden bundles.
2. `tools/check_garden_fixtures.py` — `CONCEPT_FIELDS` allowlist (line 33).
3. [[b1-complete]] — B.1.1 garden handler shipped scope.
4. The current bundle at `content/garden/mei-r-wom-2026/index.md` — post-workaround state for reference.
