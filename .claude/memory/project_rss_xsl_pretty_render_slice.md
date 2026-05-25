---
name: rss-xsl-pretty-render-slice
description: "Phase 8 deferral — essays RSS feed renders styled via XSL stylesheet, header RSS icon collapsed to always link essays; shipped 2026-05-13"
metadata: 
  node_type: memory
  type: project
  originSessionId: db0fe890-9229-4849-89d1-9d213bd28e0d
---

Phase 8 deferral cleared. Shipped 2026-05-13 (pushed `84d4d36..5d56dbd` to origin/master).

**Scope:** essays feed only.

**Files added:**
- `assets/feed/feed.xsl` — hand-authored XSL 1.0 with inline `<style>` (tokens cloned from main.css `:root`), `prefers-color-scheme` for dark mode, two named templates (`pubdate-iso` + `pubdate-display`) parsing RFC-822 dates via positional `substring()` slicing.
- `tools/check_rss_xsl.py` + `tools/test_check_rss_xsl.py` — new linter pair (15th-or-16th depending on Citation export shipping order; spec leaves the N unbound).

**Files modified:**
- `layouts/essays/rss.xml` — prepended `<?xml-stylesheet ?>` PI via Hugo's `resources.Get "feed/feed.xsl" | RelPermalink | safeHTML` pattern; PI is line 3 of the template (after the no-output `$pages` + `$title` directives), line 1 of rendered output.
- `layouts/partials/header.html` — collapsed per-section RSS icon routing to always link `/essays/index.xml` (was switching essays → essays, garden → garden, else → home; per user's "RSS is only for essays regardless of where I am" feedback during browser verification).
- `.github/workflows/hugo.yaml` — added 2 CI steps (40 → 42 named steps).
- `CLAUDE.md` — shipped entry added; Final QA + Phase 8 follow-up entries updated to drop the deferred RSS UX item; only garden path-log retrieval remains as the open Phase 8 deferral.

**Specs / plans committed:**
- `docs/superpowers/specs/2026-05-13-rss-xsl-pretty-render-design.md` (commit `33aa5f4`; token-value fix in `daba92f`).
- `docs/superpowers/plans/2026-05-13-rss-xsl-pretty-render.md` (commit `e8ab33f`).

**Linter coverage:** 7 assertions across 3 groups — XSL shape (5: exists, parses, root is xsl:stylesheet, has `template match="/"`, has inline `<style>` sentinel), essays PI placement (2: present, before `<rss>`), garden scope guard (1: PI absent). 5-fixture sibling test using `tempfile.TemporaryDirectory()` per the project's `check_garden_links.py` convention.

**Process:** subagent-driven-development. 8 plan tasks, 4 implementer-dispatches + 1 manual edit (header collapse) + 1 self-edit (regex simplification nit from code reviewer); spec+code-quality reviews on Tasks 1-4, light review on Tasks 5-7 due to small / mostly-verification scope. One mid-stream brainstorm gap surfaced (header chrome routing) saved as feedback memory [[chrome-routing-follows-scope]].

**Remaining Phase 8 work:** interactive QA walkthrough items (kbd / SR / colour-blindness / mobile / perf — all need a human at hardware) + garden path-log retrieval (spec stub at `docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md`).

See also: [[phase-8-slice-3-final-qa]], [[phase-8-a11y-close-out]], [[chrome-routing-follows-scope]].
