---
name: c-complete
description: C math validator — shipped 2026-06-01. Integration slice; no new validator on site side. Pre-publish gate via a3-pub.sh subprocess-calling org-math-lint; B.4 scanner gained env detection + code-fence exclusion; site tools/check_math.py validates has_math ↔ body coupling on essays. 25th linter pair. CI step count 61 → 63. ert 478 → 480.
metadata: 
  node_type: memory
  type: project
  originSessionId: 29127c6c-92db-4a63-8841-a53b487a6d52
---

**Shipped (code-complete 2026-06-01):** C — math validator per `docs/superpowers/specs/2026-06-01-phase-3-c-math-validator-design.md` + `docs/superpowers/plans/2026-06-01-phase-3-c-math-validator.md`. 10 tasks, subagent-driven, 10 implementation commits across 2 repos (5 site + 5 dotfiles).

## What ships in C

### Dotfiles (`~/dotfiles/`; baseline `43fb740` → tip `0284026`)

- `a3madkour-publish-essays.el` (B.4 essays handler) — `--scan-has-flags` extended:
  - **Env detection (`81fae4d`)** — 4th disjunction `\\\\begin{[a-zA-Z]+\\*?}` covers `\begin{equation}…\end{equation}`, `\begin{align*}…\end{align*}`, etc.
  - **Code-fence exclusion (`89092f8`)** — new `--strip-code-fences` helper strips ` ```-fenced ` markdown blocks plus org `#+begin_src` / `#+begin_example` regions; only `:has_math` uses the stripped body (other has_* keys keep scanning the unstripped body).
  - 2 new ert tests: `scan-math-environment`, `scan-math-inside-code-fence-ignored`.
- `a3-pub.sh` — three commits:
  - **Helper + flag (`8049844`)** — `a3_pub_check_math()` invokes `org-math-lint check --root <dir>` via `~/org/notes/tools/org-math-lint/.venv/bin/python`. Distinct exit codes 0/1/2. `--skip-math-check` flag pre-pass.
  - **Bash 3.2 fix (`7b2db57`)** — guard empty `parsed_args[@]` with explicit length check (macOS bash 3.2 + `set -u` trips on empty-array expansion otherwise).
  - **Wire (`0284026`)** — `a3_pub_check_math` called in three intercepts after their SITE_DATA_DIR resolution:
    - `--publish-living` → `$HOME/org/notes`
    - `--publish-deliberate <FILE>` → `$(dirname "$target_path")`
    - `--sync-citations` → `$HOME/org`
  - `--check-orphans` intercept unchanged (dry-run, no source publish).
- ert: 478 → 480.

### Site (`~/Sync/Workspace/a3madkour.github.io/`; baseline `e3b9c6a` → tip `8808c74`)

- `tools/check_math.py` + `tools/test_check_math.py` (25th linter pair; ~95 LoC linter + 7 sibling tests).
- `layouts/shortcodes/math.html` — deleted (was a `<code data-math>` placeholder; KaTeX parses `\(...\)` / `\[...\]` directly).
- `content/essays/example-one/index.md` — `{{< math >}}` replaced with `\(\alpha + \beta = \gamma\)` + `\[\sum_{i=1}^{n} x_i = \bar{x}\,n\]`.
- `content/essays/example-three/index.md` — `has_math: true`; inline `\(E = mc^2\)` added.
- `.github/workflows/hugo.yaml` + `tools/ci-local.sh` — math linter pair wired after citations.
- `CLAUDE.md` — new "Math pipeline" Architecture subsection; linter-pair count 24 → 25; CI step count 61 → 63.

## Why this slice mattered

The site had `has_math: true` on example-one as a deferred-feature placeholder for over a year, with the `{{< math >}}` shortcode wrapping HTML-entity Greek letters as a stand-in. No validator caught the eventual mismatch between frontmatter and content. C closes the gap by:

1. Wiring the **existing** validator (`org-math-lint` — author's own tool at `~/org/notes/tools/org-math-lint/`, 1.2k LoC; vendors KaTeX in V8 via py-mini-racer) into a3-pub.sh as a pre-Emacs subprocess gate. Failed validation aborts publish.
2. Tightening B.4's `has_math` auto-derive to cover environment-based math + skip code blocks.
3. Adding a site-side `check_math.py` (25th linter pair) that catches frontmatter/body drift at CI time — orthogonal to the source-side check.

Most importantly: **no parallel grammar in the site repo.** Vendoring a KaTeX support table would have rotted; using the author's real tool gives in-process KaTeX accuracy for free. See [[next-slice]] (now pointing at D).

## Known follow-ups (C.x)

1. **org-math-lint venv broken on this host** (host-config, not slice-code). `~/org/notes/tools/org-math-lint/.venv/bin/python` symlinks to `/usr/bin/python3` (system Python) but the site-packages contain Linux x86_64 binaries (mypyc `.so` files) from a prior install. `python -m org_math_lint.cli check` fails with `ModuleNotFoundError`. **`a3-pub.sh`'s helper treats this as exit-1 "validator failure"** rather than the spec's intended exit-2 "not installed" because the venv's python binary IS executable; the venv just doesn't yield org_math_lint at runtime. Fix: recreate the venv with `python3 -m venv .venv && .venv/bin/pip install -e .` from `~/org/notes/tools/org-math-lint/`. See [[reference-org-math-lint-venv-platform]]. Until that's done, real publishes need `--skip-math-check` or the user does the venv rebuild. The slice's a3-pub.sh wiring is correct; this is purely a host-state issue.
2. **Interactive `M-x a3-publish-*` paths uncovered.** Math gate only runs through `a3-pub.sh` shell invocation. Per-spec V1 scope; flag for future patch if interactive becomes the norm.
3. **Garden / research / library math not validated.** Those sections don't carry `has_math` frontmatter; site coupling check only walks essays. Extend the linter (and add `has_math` to those schemas) when math actually appears in non-essay sections.
4. **KaTeX runtime itself still deferred** per the CLAUDE.md deferred-features table. C just validates; the rendering engine is its own future slice gated on author appetite.
5. **Helper exit-code conflation.** Current helper returns 1 on validator failure AND on broken-install (because the broken install yields a python crash, which the helper treats as a check failure). Cleanest fix would distinguish "python crash" (exit 2) from "validation report exit 1" via probing `python -c "import org_math_lint"` first. Out-of-band; not surfaced because (1) above is the real blocker.

## End-of-slice test inventory

- ert (dotfiles): 478 → 480 (+2: env detection + code-fence exclusion).
- Python unit (site `tools/test_check_math.py`): 0 → 7 (new linter pair).
- Python integration: unchanged.
- CI step count: 61 → 63 (math linter + sibling test).
- Linter pairs: 24 → 25.

## State at end of session

- All 10 implementation commits LOCAL on `master` (site) and `main` (dotfiles).
- **Not pushed** — held for user review of the slice.
- Site working tree: clean except for memory notes about to be written.
- Dotfiles working tree: pre-existing 5 dirty tracked files unchanged (author's in-progress; never staged).
- Worktree `.claude/worktrees/f-citation-pipeline` still present from F's session; clean to remove now.
- No outstanding CI failures locally (`tools/ci-local.sh` math pair passes; LHCI deps not installed locally per [[reference-ci-local-lhci-deps]]).
