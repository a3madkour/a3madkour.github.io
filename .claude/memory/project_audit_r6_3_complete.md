---
name: audit-r6-3-complete
description: R6.3 built-HTML link-integrity crawl SHIPPED 2026-07-05 (da7a7a5..f8f0e1b) — 33rd linter pair; CLOSES THE ENTIRE audit-remediation roadmap (R1–R6 all done)
metadata: 
  node_type: memory
  type: project
  originSessionId: 889a5f3c-3a85-4fd5-a10c-2092dc7137e1
---

# Audit R6.3 — built-HTML link-integrity crawl (shipped) — CLOSES THE WHOLE ROADMAP

**2026-07-05.** Subagent-driven, on master. Branch `da7a7a5..f8f0e1b` (8 commits incl. design+plan). Spec/plan: `docs/superpowers/{specs,plans}/2026-07-05-r6.3-html-link-integrity-*`. Pushed `3e61b81..f8f0e1b`; deploy watched.

**This closes the ENTIRE 2026-07-03 six-lens audit-remediation roadmap — R1 through R6, every row done or deliberately deferred-then-built.** R6.3 was the last trigger-gated row; the author chose to build the trigger fixtures now rather than wait ([[feedback_trigger_gated_make_fixture]]). Roadmap doc all R6 boxes ☑.

**What shipped (33rd linter pair `tools/check_html_links.py`):** a stdlib `html.parser` crawler over the built `public/` — every internal `<a href>` must resolve to a file, every `#fragment` to a real `id`/`name` anchor in the target doc. `run(public: Path)` seam (a "public-path" outlier, post-build, sibling of check_smoke/check_anchor_link — NOT pre-build). External/mailto/tel/data/js/protocol-relative/empty skipped; same-domain absolute stripped→internal. File resolution: `/`→index.html, `/foo/`→foo/index.html, `/foo`→foo/index.html|foo.html, `/foo.ext`→that file. `#`/`#top` always valid; non-HTML targets skip fragment checks. Design was Option A (full integrity incl. anchors); external checking rejected (no network in CI).

**Key finding that shaped it:** Hugo's HTML minifier **strips attribute quotes** (`href=/essays/`) → a regex crawler would miss most of the ~3,416 hrefs across 123 pages. `html.parser` mandatory (also gives free `<script>` CDATA handling so JSON graph blobs aren't parsed as tags).

**R6.3 EARNED ITS KEEP immediately** — first real-site run caught 2 pre-existing broken links: (1) `#thm-does-not-exist` = the INTENTIONAL `ref-block-unresolved` forward-ref fixture → crawler now skips `<a class~="ref-block-unresolved">` (documented intentional marker); (2) `/tags/fiction/` = a **real 404** — `library/umbrella-shelf.html` emitted a tag-shelf "See all" → `/tags/<tag>/` unconditionally, but library shelves are **data-driven** (`data/reading.yaml`) and Hugo builds taxonomies only from CONTENT frontmatter, so no `/tags/fiction/` page exists. Fixed by gating see_all on `with site.GetPage`.

**Fixtures (augment-existing):** essay `example-five` → cross-page anchor `/garden/bayesian-statistics/#tldr`; garden `bayesian-statistics` → cross-section `/essays/example-five/`. Dummy prose, valid.

**Verification:** crawler green on clean build · 23 tests · full regression (pre-build linters + build + smoke/anchor/html-links + pagefind + **E2E 9/9**) · final opus review READY (only cosmetic Minors, one fixed: CLAUDE.md run()-param outlier list). CLAUDE.md → "Thirty-three linter pairs".

**Process note:** Task 2 was discovery-driven — controller ran the crawler to size it, diagnosed both findings, then dispatched the implementer with exact fixes. A reviewer subagent stalled once (watchdog 600s) → re-dispatched fresh, fine.

See [[audit-r6-1-complete]], [[audit-r6-2-complete]], [[audit-remediation-roadmap]], [[reference_dev_server_stale_draft_page_weights]]. **The audit roadmap is fully closed. Backlog empty.**
