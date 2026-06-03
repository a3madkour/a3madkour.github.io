---
name: project-d2-pdf-qa-followup
description: D.2 PDF backend export works end-to-end (Task 21 interactive run 2026-06-03); visual/content QA of the produced PDF is deferred to a later pass
metadata: 
  node_type: memory
  type: project
  originSessionId: d7fc28b7-3a2d-4df8-9f6f-fceb6b93385a
---

**Status:** D.2 PDF pipeline is functionally green. `M-x a3-publish-deliberate ~/org/essays/example-multi.org` produces a valid PDF (~18 KB, 1 page) and moves it into the Hugo bundle. Two in-session bugs were fixed and committed (`6b1b476` in dotfiles).

**Why:** First interactive end-to-end run surfaced two issues batch tests didn't catch:
1. `--translate-vocab` hung in `re-search-forward` on file-backed buffers — org-element cache invalidation thrashed each delete/insert. Fixed via collect-then-mutate + `inhibit-modification-hooks t`.
2. `--compile-tex` early-exited on xelatex's non-zero rc from harmless "Label(s) may have changed" / font-substitution warnings, even though the PDF built. Fixed by gating success on `(file-exists-p pdf)` instead of every-step exit code.

**Deferred QA items** for a later D.2 pass — open these when sitting with the produced PDF:
- Does the PDF visually carry the D.1 vocab tiers (theorem/lemma family italic body, definition bold header, proof ∎)? amsthm defaults may need tuning in `madkour-paper.cls` per spec §4 LaTeX subsection.
- Are the visibility tags actually filtering correctly in the PDF? Spot-check: `:WEB_ONLY:` / `:NOEXPORT_PDF:` subtrees should be absent; `:PAPER_ONLY:` should remain.
- Are figures rendering at appropriate scale? `\includegraphics` defaults may need a `\linewidth`/`\textwidth` constraint.
- Are the `\hyperref` cross-refs surviving the `@@latex:...@@` snippet path correctly when the fixture grows to include them? (Fixture currently has no `[[#id]]` link — that's also a Task 21 deferral; D.1's `#+attr_shortcode: :id` doesn't satisfy ox-hugo's link resolver, documented limitation.)
- Bibliography rendering — currently no `[cite:@key]` in the fixture (would need a real `library.bib` key). Test once a real essay flows through D.2.
- Font substitution warning ("Some font shapes were not available") — verify whether substitutes are acceptable for finished output or load specific fonts via `\setmainfont{…}` in the class.

**How to apply:** When the next D.2-touching slice scheduled, start with: read this memory, open the produced PDF (`content/essays/<slug>/<slug>.pdf` for any multi-export essay), walk the bullet list above, file targeted fixes. Treat each as a small follow-up commit rather than a slice.

Related: [[project-d2-spec-queued]] (now superseded — D.2 is shipped). The Word backend still needs `reference.docx` (Task 10) before its half of the pipeline can be QA'd.
