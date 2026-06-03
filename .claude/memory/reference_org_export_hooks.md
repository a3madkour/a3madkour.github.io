---
name: reference-org-export-hooks
description: "Modern org exposes `org-export-before-processing-functions` and `org-export-before-parsing-functions` (note `-functions`, not `-hook`); the `-hook` variants don't exist"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d7fc28b7-3a2d-4df8-9f6f-fceb6b93385a
---

**Correct hook names** (modern org-mode, verified at `~/.emacs.d/straight/build/org/ox.el:2186` + `:3103`):

- `org-export-before-processing-functions` — runs before the export pipeline starts; handlers receive `(BACKEND)`.
- `org-export-before-parsing-functions` — runs before parsing; handlers receive `(BACKEND)`.

There is **no** `org-export-before-processing-hook` or `org-export-before-parsing-hook`. Adding a handler to a `-hook` variant is silently dead code — `add-hook` succeeds (it creates the variable), but org never runs it.

**Pattern:**

```elisp
(add-hook 'org-export-before-processing-functions
          (lambda (backend) …))
```

Handler signature is `(backend)` regardless of which of the two functions you hook.

**Where I lapsed:** D.2 Task 3 (`a3madkour-pub-multi-filter-install`) registered on `org-export-before-processing-hook`. Caught by code-quality review. Fixed in commit `25db8ee` in dotfiles.

**How to apply:** Any new dotfiles or site code that needs to run during org export must use the `-functions` variant. Grep `org-export-before-processing` before adding a hook to confirm you have the variable name right.
