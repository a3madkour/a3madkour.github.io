---
name: next-slice
description: "Session-start pointer — next slice is B.2 (library handler). B.1.1 shipped 2026-05-26: pre-export id-link rewriter + Hugo unsafe:true config + round-3 spot-check (MAP) verified hugo --minify clean and rendered HTML correct. Per spec §12 sequencing: B.2 → B.3 (research) → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F (citations) → C (math validators) → D (unified markup) → E (explorables)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e3eb273-5835-4b22-88ad-5642b85830f5
---

**Next slice = B.2 — library handler.** B.1.1 shipped 2026-05-26; see [[b1-complete]] (round-3 subsection added).

Per design spec §12 slice ordering: A → B.0 → B.1 → B.1.1 → **B.2 (next)** → B.3 → B.4 → B.5 → B.6 → B.7 → F → C → D → E.

## Why B.2 is structurally different from B.1

B.1 emits one Hugo bundle per garden note (`content/garden/<slug>/index.md`). B.2 (library) emits **per-medium YAML rows** appended to `data/<medium>.yaml` (one of `library-reading.yaml` / `library-listening.yaml` / `library-playing.yaml` / `library-watching.yaml`) — not per-page Hugo bundles. The source is 4 top-level org files in `~/org/notes/` (or similar) with one heading per library item.

See parent spec `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §8 for the full pipeline shape.

Special considerations carried forward from B.1.1:
- **Hugo `unsafe: true` is now site-wide** ([[goldmark-unsafe-for-ox-hugo-html]]). Any future handler that emits `@@html:` snippets via `rewrite-buffer-links` benefits automatically.
- **`finish-publish`'s no-retry on `delete-bundle` 'failed**: still open ([[b1-complete]] round-2 secondary finding). B.2 may or may not encounter this depending on whether library items map to deletable bundles. Currently library emits YAML rows, not bundles, so the `delete-bundle` path isn't exercised — but watch for analogous "stale row in YAML" cleanup gaps in B.2's analogue.
- **Library tags must round-trip** ([[phase-3-library-tag-shelves]]): library-publish must emit org tags as `tags: [...]` in `data/<medium>.yaml`; shelves stay hand-authored in `data/library-shelves.yaml`.
- **Two publish commands** ([[phase-3-two-publish-commands]]): library is in the "frequent + idempotent" set alongside garden + research. B.2's handler registers into `publish-living`'s walker (like B.1's garden handler), not into a deliberate per-post command.

## State of the world at session start

**Site repo (`/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`):**
- master is **8 commits ahead of origin/master**: `82d42a4..7e6702d`. NOT pushed.
- New content: `content/garden/maximum-a-posteriori-map/` (3rd real B-emitted bundle + first cross-linked).
- `data/url-history.yaml` — 4 live entries.
- `hugo.yaml` — `markup.goldmark.renderer.unsafe: true` added.
- 14 Python integration fixtures passing (was 13 pre-B.1.1).
- Working tree clean.

**Dotfiles (`~/dotfiles/`):**
- main is **22 commits ahead of origin/main**: last 6 of those are B.1.1 (`9ab1ea6..8b40026`). NOT pushed.
- 271 ert tests passing.

**Personal notes (`~/org/notes/`):**
- 4 annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`: `bayesian_statistics`, `bias_vs_variance`, `cellular_automata_are_visual_rule_based_systems`, `maximum_a_posteriori` (the last newly added in B.1.1 round-3). NOT git-tracked.

## Recommended session start

1. Read site CLAUDE.md + [[b1-complete]] (round-3 subsection) + [[phase-3-decomposition]].
2. Read parent B spec §8 (library pipeline shape).
3. `superpowers:brainstorming` for B.2 — even though the pattern is established by B.1, the per-medium YAML structure is novel enough to warrant a design pass before writing the plan.
4. Then `superpowers:writing-plans` for the implementation.

## Push decision (carry-forward)

22 unpushed dotfiles commits + 8 unpushed site commits accumulated across A.1.d / B.0 / B.1 / B.1.1. The author may want to push before B.2 starts (signals public progress; CI runs against the actual deployed state) or batch the push with B.2's ship. Either is fine; no urgency.
