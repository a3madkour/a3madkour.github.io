---
name: org-roam-id-find-returns-cons
description: "org-roam's org-roam-id-find returns (file . pos), NOT a string — cl-letf test stubs commonly mis-stub this and pass while real usage breaks. Wrap or unwrap explicitly."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7ef3bb18-9acf-451e-8f17-f5a28329110c
---

`(org-roam-id-find ID)` from real org-roam (v2.x+ via straight) returns one of:
- `nil` — id not in DB
- `(FILE . POS)` — cons cell where `FILE` is the absolute path containing the node and `POS` is the buffer position of the heading's `:ID:` drawer

It does **NOT** return a plain string. This is non-obvious from the function name + a common mis-stub in tests:

```elisp
;; BAD — test passes, real call returns a cons and downstream
;; expand-file-name / file-exists-p / equality check on path errors.
(cl-letf (((symbol-function 'org-roam-id-find)
           (lambda (id) (and (equal id "real-uuid") "/abs/path/foo.org"))))
  ...)

;; GOOD — match the real shape.
(cl-letf (((symbol-function 'org-roam-id-find)
           (lambda (id) (and (equal id "real-uuid")
                             (cons "/abs/path/foo.org" 42)))))
  ...)
```

When writing a wrapper that needs a file path, unwrap the cons:

```elisp
(let ((result (org-roam-id-find id)))
  (cond
   ((null result) nil)
   ((consp result) (car result))
   ((stringp result) result)            ; defensive: alt versions
   (t (error "Unexpected return shape: %S" result))))
```

**Where this surfaced:** Phase 3 A.1.b sub-project. The `a3madkour-pub--id-to-file` wrapper in `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el` initially just `(when (stringp id) (org-roam-id-find id))` — passed cl-letf tests, then Task 19 spot-check ran it against the real installed org-roam and threw `wrong-type-argument stringp ("...path..." . 1)` in `expand-file-name`. Fixed + 2 regression tests added.

**Cost of the lesson:** ~5 minutes of debugging once the spot-check error was clear, but the bug would have shipped silently and broken every id-link rewrite in production publish runs. Pattern lesson: when stubbing org-roam (or any external library) in elisp tests, verify the stub matches the real return shape at least once via a "smoke run" — either an explicit unit test that drops the stub and exercises real org-roam, OR a `make-mock` helper that's authored against the documented return shape.

Applies generally: any cl-letf/mock-based test against an external library should be paired with one integration smoke that exercises the real API surface.
