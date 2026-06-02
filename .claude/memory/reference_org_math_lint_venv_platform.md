---
name: reference-org-math-lint-venv-platform
description: "org-math-lint venv at ~/org/notes/tools/org-math-lint/.venv/ can break silently when site-packages contains binaries from a different platform (e.g., Linux x86_64 mypyc .so files vs macOS arm64). The venv's python symlink resolves to system /usr/bin/python3 but the editable install + dependency wheels don't load → `ModuleNotFoundError: No module named 'org_math_lint'`. a3-pub.sh's math-check helper treats this as a validation failure (exit 1) rather than 'not installed' (exit 2)."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 29127c6c-92db-4a63-8841-a53b487a6d52
---

## Symptom

```
$ ~/org/notes/tools/org-math-lint/.venv/bin/python -m org_math_lint.cli check --root ~/org/essays
/opt/homebrew/Caskroom/miniconda/base/bin/python: Error while finding module specification for 'org_math_lint.cli' (ModuleNotFoundError: No module named 'org_math_lint')
```

Note `/opt/homebrew/Caskroom/miniconda/base/bin/python` in the error: that's where the venv's `python` symlink resolved to (it chain-links `python → python3 → /usr/bin/python3` which on this machine routes to conda's base Python or system Python — not the venv interpreter). `sys.prefix` reports the system path, not the venv, so the venv's `lib/python*/site-packages` is never on `sys.path`.

## Why

`org-math-lint` was installed editable into a venv that was later relocated or whose interpreter symlink was broken. Specifically observed:

- `.venv/bin/python` → `python3`
- `.venv/bin/python3` → `/usr/bin/python3` (system Python)
- `.venv/lib/python3.14/site-packages/` contains an `.so` named `*mypyc.cpython-314-x86_64-linux-gnu.so` — the wheels were installed on Linux x86_64.

Two diagnostic indicators:
1. The venv expects Python 3.14 but the symlinks point at whatever `/usr/bin/python3` is (macOS system Python is typically 3.9, broken match).
2. The C-extension is built for `x86_64-linux-gnu`; running on macOS arm64 means the binary can't load even if the import path were correct.

## Fix (host-config, not slice-code)

Recreate the venv on the current host:

```bash
cd ~/org/notes/tools/org-math-lint
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -e .
```

(Choose a `python3` that matches the platform; on macOS arm64 use Homebrew Python or the system 3.11+. The `pyproject.toml` requires `>=3.11`.)

Verify:

```bash
.venv/bin/python -m org_math_lint.cli check --root /tmp
# expected: prints OK if empty dir, or a usage banner if cli requires arg
```

## How `a3-pub.sh`'s helper handles it (today)

`a3_pub_check_math` checks `[ -x "$ml_venv" ]` to detect "not installed" → exit 2 with install instructions. But `~/org/notes/tools/org-math-lint/.venv/bin/python` IS an executable symlink even when broken, so the check passes and the helper proceeds to invoke it. The invocation fails with `ModuleNotFoundError`, which exits 1 — and `a3-pub.sh` treats that as "math validation failed; publish aborted" (the message points at the wrong cause).

**Workaround until the venv is fixed:** pass `--skip-math-check` to a3-pub.sh.

**Possible improvement** (deferred follow-up): the helper could probe `"$ml_venv" -c "import org_math_lint"` first; non-zero from that → exit 2 with the recreate-venv instructions; zero → proceed with the actual `cli check` call. Cleaner exit-code discipline; out of slice C scope.

## How to detect the broken state quickly

```bash
~/org/notes/tools/org-math-lint/.venv/bin/python -c "import sys; print(sys.prefix)"
```

If the printed prefix is anything other than `/Users/<you>/org/notes/tools/org-math-lint/.venv`, the venv is broken — Python is loading from outside the venv.

Or check the binary platform:

```bash
file ~/org/notes/tools/org-math-lint/.venv/lib/python*/site-packages/*mypyc*.so 2>/dev/null
```

If output contains `ELF` (Linux) or a different architecture, the `.so` won't load and the package import will fail.
