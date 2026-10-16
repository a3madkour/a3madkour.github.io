---
name: reference_stale_elc_shadows_publish_elisp
description: run-tests.sh and a3-pub.sh load an older .elc over an edited .el — edits silently untested and unpublished until recompiled
metadata:
  node_type: memory
  type: reference
  originSessionId: 5c2a5d02-07e8-4ea9-b946-2d0cb3a41302
  modified: 2026-10-16T05:12:17.909Z
---

`~/emacs-configs/custom/lisp/` holds untracked `*.elc` files. Neither `run-tests.sh` nor `a3-pub.sh` sets `load-prefer-newer`, so after editing a publish module `require` loads the OLD byte-code: tests pass/fail against stale code and a real publish runs stale code. The only tell is the line `Source file ‘…’ newer than byte-compiled file; using older file` in the output.

**How to apply:** after editing any publish `.el`, grep the test output for `newer than`, or batch byte-compile the edited files first (`emacs --batch … -L . --eval "(setq load-prefer-newer t)" -f batch-byte-compile <files>`, with the straight bootstrap + build-dir load-path from `run-tests.sh`). No Emacs server may be running, so `emacsclient` can't do it. Logged as S1 friction row 4; the real fix (`load-prefer-newer t` in both scripts) is S2 work. See [[project_authoring_infra_roadmap]].
