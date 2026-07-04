---
name: project-d2-complete
description: "D.2 multi-target export shipped 2026-06-04 — single org source → Hugo + PDF + Word artifacts via auto-triggered B.4 hook; spec, plan, all 22 tasks closed"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4af348b0-8716-4f87-a22c-765743be0ab4
---

**Shipped 2026-06-04** to master (`6882356..b9aff3e`, 16 commits) + main (`a6336f3..5be2d7a`, 22 commits). Closes Phase 3 sub-project D.2 (multi-target export — Hugo + PDF + Word from one literate org source).

**Pipeline:** `M-x a3-publish-deliberate <essay.org>` → B.4 essay handler runs → after-essay-publish hook fires → D.2 orchestrator (`a3madkour-publish-multi.el`) runs PDF + Word backends in parallel error envelopes → frontmatter patched with `multi_export: true` + `downloads:{pdf,word}` → essay-meta partial renders the cluster.

**Gate**: source must carry `#+multi_export: t`. Without it the hook is a no-op.

**Architecture** (dotfiles modules under `~/dotfiles/emacs-configs/custom/lisp/`):
- `a3madkour-publish-multi-filter.el` — opt-in detection, visibility-tag filter (5 tags: WEB_ONLY / PAPER_ONLY / NOEXPORT_WEB / NOEXPORT_PDF / NOEXPORT_WORD), D.1 vocab → backend-specific annotations, `[[#id]]` cross-ref rewriter, **visibility-tag strip** (removes our tags from kept headlines so they don't render as section-header chrome).
- `a3madkour-publish-multi-pdf.el` — PDF backend. Registers `madkour-paper` in `org-latex-classes`, let-binds `org-latex-default-class` around `org-latex-export-to-latex`, converts referenced SVGs → PDF via rsvg-convert, runs xelatex → biber → xelatex → xelatex loop, success-gated on `(file-exists-p pdf)` not exit code (xelatex returns rc=1 on harmless warnings).
- `a3madkour-publish-multi-word.el` — Word backend. Pandoc bypasses Emacs export hooks, so `--serialize-filtered` manually mirrors the four filter passes (visibility / strip-tags / vocab / crossref) into a temp .org file before handing to pandoc. Lua filter (`d2-blocks.lua`) handles D.1 vocab numbering + paragraph styling against `reference.docx`'s 24 paragraph styles.
- `a3madkour-publish-multi.el` — orchestrator. Parallel PDF + Word with `condition-case`; partial success emits whichever artifacts succeeded.
- `a3madkour-publish-multi-filter-test.el` — 17 ert tests covering visibility filter / strip / vocab / crossref.

**Architecture** (site templates under `tools/templates/`):
- `madkour-paper.cls` — LaTeX class. `\LoadClass[11pt]{article}` + amsthm + 12 `\newtheorem` envs (theorem-family shares counter; definition/example/remark/note independent counters; conjecture/axiom plain style; proof built-in).
- `reference.docx` — Word reference doc with 24 paragraph styles. Bootstrapped via `pandoc --print-default-data-file reference.docx` then 24 paragraph styles injected into `word/styles.xml`: 6 strong-tier kinds × 2 (Header+Body) = 12, 5 soft-tier × 2 = 10, Proof × 2 = 2. Strong = bold + burgundy `#7A1F2B`; soft = bold + ink-soft `#3A3A3A`; chrome-less = italic. Header styles chain `w:next` to their paired body.
- `d2-blocks.lua` — pandoc filter. Walks Divs whose class matches one of 12 D.1 vocab kinds, prepends a styled header paragraph (`pandoc.Span` with `custom-style="<Kind> Header"`), wraps body paragraphs in `<Kind> Body` style, appends ∎ to proof body. Family counter shared (theorem/lemma/corollary/proposition/claim), independent counters per other kind, proof unnumbered.

**Architecture** (site Hugo):
- `layouts/partials/essay-downloads.html` — separate from essay-meta so download buttons don't leak into bento cards (essay-card + essay-card-featured invoke essay-meta but NOT essay-downloads).
- `layouts/essays/single.html` calls both essay-meta + essay-downloads.
- CSS §11 — `.essay-downloads-line` row with "Download:" eyebrow label + larger pills (`var(--text-sm)`, padding 2px 10px) + burgundy hover fill. Uses existing tokens; contrast check still green.
- `tools/check_org_assets.py` — extended to harvest refs from `downloads:` frontmatter (both inline-flow and block-flow shapes); pdf/docx artifacts no longer flagged as orphans.

**Bugs caught in spot-check** (5 fixes + 2 follow-ups filed):
1. `\documentclass{article}` (not `madkour-paper`) — labels vanished. Fix: register class entry + let-bind `org-latex-default-class`. Commit `90ad9e9`.
2. Asset-ref linter flagged pdf/docx as orphans. Fix: extend `_extract_refs` to read `downloads:` map. Commit `beb3699`.
3. Download links resolved as root-relative (`/example-multi.pdf`) → 404. Fix: `Page.Resources.GetMatch` → `.RelPermalink`. Commit `73cdec9`.
4. Visibility tags leaked into headings (`PAPER_ONLY` / `NOEXPORT_WORD` floating as right-margin `\textsc{TAG}` chrome on kept sections). Fix: new `--strip-visibility-tags' pass after `--apply-visibility'. Commits `b8f7256` (initial), `6795951` (regex-only rewrite — `org-map-entries` + `org-set-tags` hung interactive Emacs on cache re-parse), `5be2d7a` (multi-word.el's `serialize-filtered` was bypassing the hook and needed manual wiring).
5. Download buttons leaked into bento essay cards via essay-card → essay-meta. Fix: split into separate `essay-downloads.html` partial only called from `essays/single.html`. Commit `b5e94c3`.

**Follow-ups CLEARED 2026-06-04** (post-ship session):
- `M-x a3-publish-deliberate` window-pop → fixed in dotfiles `d0e6116` (let-bind `org-export-show-temporary-export-buffer` nil in multi-pdf/run + publish-export/export-file).
- `url-history.yaml` key churn → fixed in dotfiles `63236f3` (`--canonicalize-entry` re-orders to id / current_url / history / state before yaml-encode; 3 ert tests; byte-stable across runs).
- Figure-ref round-trip → fixed in dotfiles `cea5d2d` (`[[file:X]]` was filtered out by asset-shape predicate; strip `file:` prefix in `--extract-asset-refs`; also adds public `a3madkour-pub-assets/list-referenced-files` adapter so D.2's SVG-conversion actually runs). User re-publish needed to verify end-to-end.
- D.1 `:title "Multi word"` quote-strip → documented as known limitation in [[feedback-d1-attr-shortcode-unquoted-titles]]. Workaround (unquoted single-word titles) sufficient; only one real usage in current content and it already follows the workaround. Real fix deferred until a multi-word title need surfaces.

**Test counts at ship:**
- dotfiles: 17 ert (multi-filter alone) + 514 total ert + 36 integration
- site: 30 org-assets tests (3 new) + 67 page-weight + 8 smoke; CI 63 steps, all green except LHCI (chromium not on local PATH — expected per `reference_ci_local_lhci_deps.md`)

**Real essay fixture**: `~/org/essays/example-multi.org` — minimal D.1 vocab exerciser + 4 visibility-tag headings + intentionally skipped figure/cite/crossref content (filed as separate follow-ups). Bundle at `content/essays/example-multi/`.

**Related memories**: [[reference-org-element-cache-hang]] (the interactive-Emacs cache trap that bit `--translate-vocab` AND `--strip-visibility-tags` separately), [[reference-org-set-tags-clobbers-match-data]] (the regex match-data trap that broke the regex rewrite first attempt — `split-string` / `member` clobber match data), [[project-d2-spec-queued]] (now superseded), [[project-d2-pdf-qa-followup]] (now closed — QA pass surfaced the documentclass + tag-strip bugs).
