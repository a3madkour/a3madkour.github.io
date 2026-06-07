---
name: tier-1-6-complete
description: "Tier 1.6 (B emits slug: on garden concept bundles) — shipped 2026-06-07 in dotfiles 2134de8. Added `(assq-delete-all 'slug out)` to --normalize-garden mirroring the existing flavor/author strip pattern; new ert garden-strips-slug; suite 608 → 609 green. Also marked 1.3 + 1.4 ✓ as retroactively-closed-by-B.2/B.3 (no new code; just roadmap reconciliation)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Bug 1.6 from `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`. Same session marked bugs 1.3 + 1.4 ✓ after verifying they had been closed retroactively by B.2 + B.3.

## Bug 1.6 — root cause

ox-hugo emits `slug:` in the YAML frontmatter (derived from `:CUSTOM_ID:` / `#+HUGO_SLUG:` / title-derivation). B.1's garden normalizer `--normalize-garden` did `(copy-alist raw-alist)` and stripped `flavor` + `author` explicitly but never touched `slug`, so it passed through into the bundle YAML.

`tools/check_garden_fixtures.py` `CONCEPT_FIELDS` allowlist forbids `slug` on every garden flavor. Every ref-note→garden promotion triggered a CI failure that the author had been hand-editing around since 2026-06-02. See [[b-slug-on-concept-followup]] for the original "six pushes in a row" incident.

## Fix

Added `(setq out (assq-delete-all 'slug out))` to `--normalize-garden`, immediately after the existing `author` strip. Docstring updated to enumerate the slug strip + reference bugs 1.6 and 1.4.

Hugo derives the URL from the bundle directory name (set by B's `publish-garden-file`), not from frontmatter `slug:`, so dropping the field has zero URL impact.

## Test

`a3madkour-pub-frontmatter--garden-strips-slug` — passes `(slug . "incoming-from-ox-hugo")` through the normalizer; asserts output has no `slug` key while companion keys (`title`, `tags`) pass through unchanged. Failed against the buggy code, passes after the fix. Suite 608 → 609 ert green.

## Bugs 1.3 + 1.4 — verified already closed

Roadmap was stale. Both bugs were closed retroactively during B.2 and B.3 ship cycles:

- **1.3 (TODO filetag leaks):** `a3madkour-pub-frontmatter/filter-editorial-tags` wired into `--normalize-garden` at line 377-379. Existing ert `garden-tags-strip-editorial` (test file line 260) pins it. Closed in [[b2-complete]]'s "retroactive --filter-editorial-tags closes B.1.x #6" item.
- **1.4 (file mtime vs git mtime):** `last-modified-cascade` helper (steps: drawer → keyword → git-mtime → fs-mtime → today) wired into `--normalize-garden` at line 358. Cascade-* ert tests cover all step orderings (test file lines 267+). Closed in B.3 cascade work.

Marked both rows ✓ in the roadmap with inline "verified 2026-06-07 — no new fix needed" notes. No memory file per bug; this entry serves as the cross-link.

## Commits

Dotfiles only:
- `2134de8` fix(garden): strip `slug:` from frontmatter — closes bug 1.6

Site repo: roadmap rows 1.3 / 1.4 / 1.6 marked ✓ + this memory file + MEMORY.md index entry.

## Cross-references

- Roadmap: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 1
- Source memory: [[b-slug-on-concept-followup]]
- Closure ancestors: [[b2-complete]], [[b1-complete]]
- Next Tier 1 item: 1.5 (library last_modified cascade), then the small batch 1.8 / 1.9 / 1.10, with 1.7 staying deferred
