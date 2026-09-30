---
name: reference_emacs31_subr_trampoline_breakage
description: "Emacs 31.1 on this macOS cannot native-compile subr trampolines, so every ert test that mocks call-process/make-process dies before its own assertions. Was 54 of 55 dotfiles ert failures."
metadata:
  node_type: memory
  type: reference
---

**Symptom.** A large, scattered set of dotfiles ert failures across unrelated modules —
async, assets, unpublish, author, essays, history, multi-pdf, multi-word — that looks like
broad rot. Every failing test's condition is the same:

```
(native-compiler-error "Compiling …/subr--trampoline-…call_process_0.eln…
 clang: error: invalid version number in '-mmacosx-version-min=18.0'
 libgccjit.so: error: error invoking gcc driver")
```

**Cause.** Emacs 31.1 (dev build) on this macOS cannot native-compile subr trampolines: the
SDK reports a version clang rejects, so libgccjit fails. Emacs needs a trampoline whenever a
primitive like `call-process` or `make-process` is advised or mocked — which is exactly what
these tests do — so the test dies during compilation, before its own assertions ever run.

**Scale when found (2026-09-29).** 54 of 55 failures in the dotfiles ert suite. The single
genuine failure underneath was
`a3madkour-pub-multi-pdf/compile-chain-runs-four-passes`.

**Fix for the test harness.** One line in `emacs-configs/custom/lisp/run-tests.sh`
(dotfiles `9a6f12e`):

```bash
--eval "(setq native-comp-enable-subr-trampolines nil)"
```

Suite went 55 unexpected → 1, and 21s → 4.9s. Trampolines buy nothing in a batch run.

**Still open, and the trap.** `a3-pub.sh` does **not** disable them. Combined with
`tools/test_publish_integration.py` overriding `HOME` — which gives the subprocess an empty
`eln-cache`, so every trampoline compiles fresh — **all 15 publish-subprocess tests in that
file are red on this machine.** Verified pre-existing by checking the dotfiles lisp dir out
at an earlier commit and diffing the failure sets: identical.

So: **a red `test_publish_integration.py` on this machine is not evidence of a regression.**
Diff the failure sets before believing one. Whether a real `a3-pub.sh` publish is affected
depends on the user's `eln-cache` being warm; untested either way.

Surfaced during [[project_works_handlers_slice]], whose plan had asserted a "751 passing"
baseline that did not exist.
