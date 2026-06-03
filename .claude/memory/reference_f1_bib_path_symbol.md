---
name: reference-f1-bib-path-symbol
description: "F.1's bibliography defcustom is `a3madkour-pub-bib/library-path` (slash-separated form), not `a3madkour-pub-bib-path` (hyphen form)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d7fc28b7-3a2d-4df8-9f6f-fceb6b93385a
---

**Symbol:** `a3madkour-pub-bib/library-path` — defined in `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el:29`.

The naming style is slash-separated (`a3madkour-pub-bib/library-path`), matching F.1's namespace convention (`a3madkour-pub-bib/bbt-endpoint`, `a3madkour-pub-bib/citations-output`, etc.). Not the hyphen-separated form (`a3madkour-pub-bib-path`).

**How to apply:** When a new dotfiles module needs to read the bibliography path, `(require 'a3madkour-publish-bib)` and reference `a3madkour-pub-bib/library-path`. Add a `boundp` guard if the module should load before F.1.

**Where I lapsed:** D.2 Task 12 plan referenced `a3madkour-pub-bib-path`. Caught and corrected by the implementer (commit `6921ebf` in dotfiles). The plan-author got the name wrong by guessing the convention rather than grepping.

Related: [[feedback-class-rename-grep-full-codebase]] — same lesson, applied to defcustom names this time.
