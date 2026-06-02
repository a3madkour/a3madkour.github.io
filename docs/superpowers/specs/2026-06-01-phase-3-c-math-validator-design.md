# Phase 3 sub-project C — math validator

**Status:** design (brainstormed 2026-06-01)
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` (sub-project A — access control + link semantics)
**Sequence:** A → B.0 → B.1 → B.1.1 → B.2 → B.3 → B.4 → F → **C** → D → E (per [[phase-3-decomposition]])
**Prior slice memories:** [[f-complete]] (F citation pipeline shipped 2026-06-01), [[next-slice]] (queued pointer), [[deferred-features-stay-visible]] (math stub policy).

---

## 1 — Goals & non-goals

### Goals

Ship pre-publish math-syntax validation for org-authored content **by integrating an existing tool** rather than authoring a parallel one. The author already maintains `org-math-lint` at `~/org/notes/tools/org-math-lint/` — a 1.2k-LoC Python package that tokenizes org files, applies a 10-rule registry (delimiters, fragmented math, unicode → LaTeX, unknown commands), and verifies each math fragment by running real KaTeX in-process via `py-mini-racer`. The validator already exists, is more rigorous than anything that would land in a stdlib-only site-side linter, and is the right source-of-truth for math validation.

C wires it into the publish pipeline and tightens the surrounding site contract:

1. **Pre-publish gate (dotfiles):** `a3-pub.sh` invokes `org-math-lint check` against the source dir before launching Emacs. Non-zero exit aborts publish — same fail-fast discipline as F's cite-key resolver.
2. **`has_math` auto-derivation (dotfiles):** B.4's essays handler stops requiring a manual `#+HUGO_HAS_MATH:` keyword and instead scans the buffer for math markers; emitted frontmatter reflects reality.
3. **Site-side coupling check (site, 25th linter pair):** a small `tools/check_math.py` validates `has_math` ↔ body markers consistency in essays. Catches publish bugs the source-side validator can't see (Hugo markdown is the ground truth for the site).
4. **`{{< math >}}` stub retirement + example-one fixture conversion (site):** delete the placeholder shortcode; convert example-one's math block to real LaTeX (`\(\alpha + \beta = \gamma\)` + a display block) so the full chain has an end-to-end fixture.
5. **Documentation (site):** CLAUDE.md gains a "Math pipeline" subsection naming the chain `org source → org-math-lint → ox-hugo → has_math auto-derive (B.4) → site coupling check → KaTeX runtime (deferred)`.

### In scope

- `a3-pub.sh` calls `org-math-lint check` by default before invoking Emacs. New flag `--skip-math-check` opts out (in-progress drafts, repo bootstrap).
- Discovery of the `org-math-lint` venv at `~/org/notes/tools/org-math-lint/.venv/bin/python` with a clear "not installed" error if missing.
- B.4 essays handler buffer scan for `\(`, `\[`, `\begin{<env>}` outside code/example blocks; sets emitted `has_math:` accordingly. `#+HUGO_HAS_MATH:` becomes an optional manual override (true / false) that wins over auto-derivation when present.
- Site `tools/check_math.py` + `tools/test_check_math.py` — coupling-only validator, ~50 LoC + ~6 tests.
- Site CI integration: new linter pair in `.github/workflows/hugo.yaml` and `tools/ci-local.sh` (step count goes 61 → 63).
- Delete `layouts/shortcodes/math.html`.
- Convert `content/essays/example-one/index.md` from `{{< math >}}…{{< /math >}}` HTML-entity placeholder to real LaTeX (one inline + one display block); keep `has_math: true`.
- Flip `content/essays/example-three/index.md` to carry one inline `\(E = mc^2\)` so V1 has a second math-bearing essay and exercises the coupling check on a happy path.
- CLAUDE.md "Math pipeline" subsection (architecture-section addition).

### Non-goals

- **No new Python math grammar in this repo.** `tools/check_math.py` does no delimiter balance, no macro vocab, no environment validation. That's `org-math-lint`'s job.
- **No vendored KaTeX support tables** (no `tools/data/katex_macros.txt` or `tools/data/katex_envs.txt`).
- **No site-side KaTeX runtime.** Math is still deferred per the CLAUDE.md deferred-features table; KaTeX bundling is a separate, future slice gated on author appetite.
- **No site-side validation of math syntax inside dollar forms.** `org-math-lint`'s canonicalization pass (E6 / E7 rules) coerces all math to `\(...\)` / `\[...\]` at the source, so post-export markdown will only contain those forms in practice. The site coupling check does recognize `$$...$$` and inline `$...$` as presence markers (defense in depth against `org-math-lint` config drift) but performs no balance, macro, or environment validation on them — `org-math-lint` is the authority on syntactic correctness regardless of which delimiter form arrives.
- **No autofix on the site side.** `org-math-lint` has a `fix` subcommand; site CI only ever runs `check`-style readonly validation.
- **No CI-side `org-math-lint` invocation.** The org sources aren't checked in; GitHub Actions has no way to run the pre-export validator. Site CI relies on the coupling check only.
- **No extension of `org-math-lint` itself** in this slice. If essay-specific rules become necessary later, that's an `org-math-lint` patch, not a site change.
- **No changes to the citation, garden, library, research, or works handlers.** B.4 (essays) is the only one touched, because `has_math` is essay-only frontmatter.
- **No KaTeX `\newcommand` / project-macros support.** Already an `org-math-lint` non-goal; out of scope here.
- **Unified def/thm/figure markup, multi-target export** — sub-project D.
- **Explorables / per-page widgets** — sub-project E.

---

## 2 — Module structure

```
~/dotfiles/
└── emacs-configs/custom/
    ├── lisp/a3madkour-publish-essays.el         [MOD]  auto-derive has_math from buffer
    ├── lisp/a3madkour-publish-essays-test.el    [MOD]  +2 tests (auto-derive + override)
    └── (a3-pub.sh)                              [MOD]  --check-math / --skip-math-check + org-math-lint subprocess

~/Sync/Workspace/a3madkour.github.io/
├── tools/check_math.py                           [NEW]  coupling-only validator (~50 LoC)
├── tools/test_check_math.py                      [NEW]  sibling unittest (~6 tests)
├── content/essays/example-one/index.md           [MOD]  swap {{< math >}} for real LaTeX
├── content/essays/example-three/index.md         [MOD]  add inline \(E = mc^2\); has_math: true
├── layouts/shortcodes/math.html                  [DEL]  retire stub
├── .github/workflows/hugo.yaml                   [MOD]  new linter-pair step (61 → 63)
├── tools/ci-local.sh                             [MOD]  mirror CI step
├── CLAUDE.md                                     [MOD]  "Math pipeline" architecture subsection; 24 → 25 linter pairs
└── docs/superpowers/specs/2026-06-01-phase-3-c-math-validator-design.md [NEW]
```

**Why no new module on the dotfiles side.** `org-math-lint` is the validator; the dotfiles edits are a shell-level subprocess call and a buffer-scan inside an existing module. No new elisp file makes sense — this isn't an orchestrator on par with F's `a3madkour-publish-citations.el`. The integration is intentionally thin.

**Why not split `check_math.py` further.** At ~50 LoC there's nothing to split. Mirrors `check_smoke.py` / sibling-less linters in size, but C ships its sibling test file because the coupling logic has meaningful branches.

---

## 3 — Pre-publish gate (dotfiles)

### 3.1 `a3-pub.sh` integration

One new flag: `--skip-math-check` opts out. Default behavior runs the check. Useful for repository bootstrap or known-broken in-progress drafts where the author wants to publish anyway.

Pseudocode in the living / deliberate / sync exec blocks, **before** the Emacs invocation:

```sh
if [ "$skip_math_check" != "1" ]; then
  ml_venv="$HOME/org/notes/tools/org-math-lint/.venv/bin/python"
  if [ ! -x "$ml_venv" ]; then
    echo "ERROR: org-math-lint not installed at ~/org/notes/tools/org-math-lint/.venv" >&2
    echo "       Install: cd ~/org/notes/tools/org-math-lint && python3 -m venv .venv && .venv/bin/pip install -e ." >&2
    echo "       Or rerun with --skip-math-check." >&2
    exit 2
  fi
  "$ml_venv" -m org_math_lint.cli check --root "$source_dir" || exit $?
fi
```

`$source_dir` resolution:

- `--publish-living`: org-roam-published notes — root is `~/org/notes/` (org-math-lint's default).
- `--publish-deliberate <FILE>`: root is the file's parent directory.
- `--sync-citations`: root is `~/org/` (covers notes + essays).
- `--sync-living`: same as `--publish-living`.

`org-math-lint check` already exits 0 on clean, 1 on issues; the existing error output is human-readable. No wrapping/translation needed.

### 3.2 Subprocess vs. elisp choice

a3-pub.sh, not begin-publish in elisp. Rationale captured during brainstorm: the shell hook fast-fails before spinning up Emacs (faster + cheaper), and elisp → venv-python is awkward. Interactive `M-x a3-publish-*` paths are uncovered by this hook — that's accepted V1 scope, on the assumption that interactive publishing is rare relative to shell-driven runs. If interactive becomes the norm, a parallel hook in `begin-publish` is the obvious follow-up (logged below).

### 3.3 Error model

- Exit 0: math validates; publish proceeds.
- Exit 1 (org-math-lint check failed): a3-pub.sh re-emits the org-math-lint stderr (already detailed: file + line + rule ID + message) and exits 1. No further publish work.
- Exit 2 (org-math-lint not installed): a3-pub.sh emits the install instruction and exits 2 with a distinct code so CI / scripts can distinguish missing-tool from real-failure.

### 3.4 What this doesn't catch

- Math added at the file level after pre-publish check but before ox-hugo (unlikely; checks run on the same buffer ox-hugo will see).
- Math broken by ox-hugo's translation (e.g., a regression where org math is mis-emitted as markdown). The site coupling check (§5) catches the most common form of this (`has_math` flag set but no markers survived in the output).

---

## 4 — `has_math` auto-derivation (B.4 essays handler)

### 4.1 Current state

B.4 essays handler (shipped 2026-05-31, see [[b4-complete]]) reads `has_math` from `#+HUGO_HAS_MATH: t` / `nil` in the org buffer and emits it into the markdown frontmatter. Authors who add math without flipping the keyword get a frontmatter / body mismatch — invisible until a runtime feature uses the flag (the future KaTeX loader will silently no-op).

### 4.2 New behaviour

When the essays handler builds the emitted frontmatter dict, it adds an auto-derivation pass for `has_math`:

```
1. Scan the buffer for math markers.
2. If a manual `#+HUGO_HAS_MATH:` exists, it wins (lets authors silence false positives).
3. Otherwise emit `has_math: true` iff any math marker was found outside code/example/quote blocks.
```

Marker regex (in scan order, dotall-aware where relevant):

- `\\(.+?\\\)` (inline)
- `\\\[.+?\\\]` (display)
- `\\begin\{(\w+\*?)\}.+?\\end\{\1\}` (environments — same-name pairing)

Code blocks excluded: `#+begin_src` / `#+end_src`, `#+begin_example` / `#+end_example`, `#+begin_quote` / `#+end_quote`, plus inline `~...~` / `=...=` spans. This mirrors `org-math-lint`'s parser token exclusions.

### 4.3 Why the keyword stays as override

Two cases the keyword still earns its keep:

- **False-positive silencing:** an author quotes raw `\alpha` in prose without intending KaTeX rendering (rare, but possible in a meta-essay about LaTeX). `#+HUGO_HAS_MATH: nil` forces `false`.
- **Forward-declared math:** an essay placeholder reserves `has_math: true` before the math is written, so the runtime loader is in place from the start. `#+HUGO_HAS_MATH: t` forces `true`.

The override semantics: if `#+HUGO_HAS_MATH:` is `t` / `true` → emit `true`; if `nil` / `false` → emit `false`; absent → auto-derive.

### 4.4 Sibling test coverage

`a3madkour-publish-essays-test.el` adds two ert tests:

- `essays--has-math-auto-derive-detects-math` — buffer contains `\(x\)`; no `#+HUGO_HAS_MATH:`; emitted frontmatter has `has_math: true`.
- `essays--has-math-manual-override-wins` — buffer contains `\(x\)`; has `#+HUGO_HAS_MATH: nil`; emitted frontmatter has `has_math: false`.

Existing tests that hard-code `#+HUGO_HAS_MATH: t` in fixtures keep passing because the manual value still wins; no fixture rewrites needed.

---

## 5 — Site-side coupling check

### 5.1 What it validates

`tools/check_math.py` walks `content/essays/**/index.md` (essays only — other sections don't carry `has_math`). For each file:

1. Parse frontmatter (reuse `parse_frontmatter()` from `check_fixtures.py`).
2. Read `has_math` (default `false` if absent).
3. Detect math markers in the body, excluding fenced code blocks (```` ``` ````).
4. Compare:

| `has_math` | Markers present? | Result |
|---|---|---|
| true | yes | OK |
| true | no | ERROR: `has_math: true` but no math markers found |
| false | yes | ERROR: math markers found but `has_math: false` (or missing) |
| false | no | OK |

Error messages name the file and the first marker location (for the math-found case) or just the file (for the math-missing case).

### 5.2 Marker recognition

Five forms recognized, robust to whichever ones survive ox-hugo emission and any future `org-math-lint` config-drift:

- `\(` (inline LaTeX, canonical)
- `\[` (display LaTeX, canonical)
- `\begin{` (any environment; the org-math-lint env allowlist handles validity upstream)
- `$$` (display dollar; only present if `org-math-lint` E7 canonicalization is opted out)
- `$<token>$` on a single line where `<token>` is non-trivial (inline dollar; only present if E6 canonicalization opted out)

The regex for inline dollar requires a non-space non-digit boundary on at least one side to avoid false-positives on prose with money amounts (`$5`, `$10/mo`). Edge cases for the dollar forms are not relied on — they exist only as a defense-in-depth; `org-math-lint` canonicalization gets us 99% to canonical `\(` / `\[`.

Fenced-code exclusion: split the body on lines beginning with ```` ``` ```` (3+ backticks); only scan even-indexed segments after the split (the ones outside fences). Inline backtick spans within a single line are scrubbed first with `re.sub(r"\`[^\`]*\`", "", line)`. Math inside Hugo shortcodes (`{{< spoiler >}}\(x\){{< /spoiler >}}` etc.) is **not** excluded — that's intentional: shortcode content is part of the page and the `has_math` flag should reflect it.

### 5.3 Linter shape

```
def lint_math(essays_dir: Path) -> list[str]:
    """Walk content/essays/**/index.md; return list of error strings."""
    ...

def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    essays_dir = repo_root / "content" / "essays"
    errors = lint_math(essays_dir)
    if errors:
        for e in errors: print(f"error: {e}", file=sys.stderr)
        return 1
    print("OK — math frontmatter coupling validates.")
    return 0
```

Same shape as `check_citations.py`. Stdlib only.

### 5.4 Test coverage

`tools/test_check_math.py` — 6 tests in one `MathCouplingTests` class:

1. `test_has_math_true_with_markers_passes` — essay with `has_math: true` and `\(x\)` in body → no errors.
2. `test_has_math_true_without_markers_fails` — essay with `has_math: true`, no math markers → 1 error mentioning `no math markers found`.
3. `test_has_math_false_with_markers_fails` — essay with `has_math: false`, body contains `\(x\)` → 1 error mentioning `math markers found`.
4. `test_has_math_missing_with_markers_fails` — frontmatter omits `has_math` entirely, body contains math → 1 error (treat missing as false).
5. `test_math_in_code_fence_ignored` — body contains `\(x\)` inside a fenced ```` ```python ```` block; `has_math: false` → no errors.
6. `test_dollar_signs_in_prose_dont_trip_inline_dollar` — body contains `$5` and `$10/month`; `has_math: false` → no errors (false-positive guard).

---

## 6 — Stub retirement + fixture conversion

### 6.1 Delete `layouts/shortcodes/math.html`

The shortcode currently wraps content in `<code data-math>` — a pure placeholder. Future KaTeX runtime parses raw `\(...\)` / `\[...\]` directly out of the HTML, so the shortcode adds no value. Delete it.

### 6.2 example-one conversion

Current:

```
{{< math >}}&alpha; + &beta; = &gamma;{{< /math >}}
```

Replacement:

```
\(\alpha + \beta = \gamma\)

\[\sum_{i=1}^{n} x_i = \bar{x}\,n\]
```

`has_math: true` stays. Auto-derivation would emit the same value (both markers detected), so the manual frontmatter and the auto-derived value agree — happy-path fixture for the site coupling check.

### 6.3 example-three flip

Currently `has_math: false`. Add one inline `\(E = mc^2\)` mid-body and flip to `has_math: true`. Gives the linter a second positive fixture and lets us assert it scans all essays not just example-one.

### 6.4 Why fixture changes are part of this slice

The deferred-features memory ([[deferred-features-stay-visible]]) calls for fixtures that exercise the shape of pending features. The current `{{< math >}}` stub did that for "math shortcode" — but the shortcode isn't the planned path. Replacing it with real LaTeX honors the same spirit: the shape exercised is the one KaTeX will actually consume.

---

## 7 — CLAUDE.md documentation

### 7.1 New "Math pipeline" subsection

Goes under "Architecture" alongside the existing CSS pipeline / JS pipeline / Theme toggle / Search modal subsections. Body:

> ### Math pipeline
>
> Math content is authored in org-mode and validated **before publish**, not after.
>
> 1. **`org-math-lint` (pre-publish, dotfiles)** — runs against org source files; tokenizes, applies the 10-rule registry (delimiters, fragmented math, unicode → LaTeX, unknown commands), verifies each fragment by parsing it with vendored KaTeX in V8 via py-mini-racer. Source: `~/org/notes/tools/org-math-lint/`. Invoked by `a3-pub.sh` (default on; opt out via `--skip-math-check`).
> 2. **B.4 essays handler `has_math` auto-derive (dotfiles)** — buffer scan for math markers; sets emitted `has_math` frontmatter. `#+HUGO_HAS_MATH:` keyword acts as manual override when present.
> 3. **`tools/check_math.py` (site CI, 25th linter pair)** — coupling-only: every essay's `has_math` value must match whether the body actually contains math markers. Catches publish bugs the source-side validator can't see.
> 4. **KaTeX runtime — deferred.** Currently no math engine ships on the site. When it lands, it will parse the canonical `\(...\)` / `\[...\]` forms `org-math-lint` produces.

### 7.2 Linter-pair count bump

In the "Commands" paragraph, "Twenty-four linter pairs" → "Twenty-five linter pairs". The list of linter pair names gains `cite math`. Same paragraph also clarifies that `check_math.py` validates only frontmatter / body coupling (the source-side validator is `org-math-lint`).

### 7.3 Deferred-features table

The "KaTeX math rendering" row stays — its trigger is still "Gated on author need". A new row OR a same-row note clarifies that math syntax is validated today even though rendering isn't shipped.

---

## 8 — Test plan

### 8.1 Dotfiles ert (essays handler)

Existing 478 ert tests (post-F baseline) stay green. New: 2 tests (per §4.4). Total: 480.

### 8.2 Site Python tests

New `tools/test_check_math.py`: 6 tests (per §5.4). Total Python integration tests delta: +0 (this is a unit-test sibling, not an integration test).

### 8.3 Integration (manual)

After implementation:

1. `cd ~/dotfiles && bash a3-pub.sh --publish-deliberate ~/org/essays/example-one.org --check-math` succeeds; example-one publishes; `data/citations.yaml` updates from F unchanged; `has_math: true` in emitted frontmatter.
2. Add a `\\unknown` macro to example-one.org; rerun → a3-pub.sh aborts with org-math-lint's `unknown macro` error. Publish does not run.
3. Site CI: `tools/check_math.py` runs against the published example-one — no errors.
4. Site CI: hand-edit a published essay to set `has_math: false` (without removing the math markers) — `check_math.py` fails with the expected error.

### 8.4 Failure modes the test plan doesn't cover

- `org-math-lint` venv install failure on a clean machine: caught by the install-instructions error message, not the test plan.
- ox-hugo emission regression that drops math markers: caught by the site coupling check; no dedicated test (would be hard to set up).
- KaTeX version drift in `org-math-lint`'s vendored bundle: out of scope; an `org-math-lint` concern.

---

## 9 — Open questions resolved by user

| Question | Choice | Notes |
|---|---|---|
| Validator scope | Reuse `org-math-lint` rather than write a parallel site-side validator | Discovered mid-brainstorm; reframed entire slice |
| Hook point | `a3-pub.sh` subprocess (not begin-publish elisp) | Interactive M-x paths uncovered V1; follow-up logged |
| Site-side validator | Tiny coupling-only check + `has_math` auto-derive in B.4 | Belt-and-suspenders; auto-derive removes the typo class, coupling check catches regressions |
| `{{< math >}}` stub | Retire; convert example-one to real LaTeX | The shortcode wasn't the planned path |
| Sections scanned by coupling check | Essays only | Other sections don't carry `has_math` |
| Section scope expansion to garden / library / research | Out of scope V1 | Add `has_math` to those frontmatter contracts if/when math appears there |

---

## 10 — Failure modes / follow-ups

### Logged for later

1. **Interactive `M-x a3-publish-*` paths uncovered.** Hook is in a3-pub.sh only; `M-x a3-publish-deliberate` doesn't fire the math check. Trigger for a future patch: parallel hook in `begin-publish` (elisp side) calling the same venv. Wait for the use case before committing to two implementations.
2. **`org-math-lint` venv portability.** If the author works on a new machine, the venv has to be reinstalled. The error message instructs how; if it bites repeatedly, a `tools/setup-org-math-lint.sh` helper is a small future patch.
3. **Garden / research / library math.** If math appears in those sections, the site coupling check is essay-only — they'd be uncovered. The fix is: add `has_math` to those frontmatter contracts (B.1 / B.2 / B.3 schema changes) and broaden `check_math.py` accordingly. Out of scope until a real garden / library / research math fixture lands.
4. **`#+HUGO_HAS_MATH:` keyword retirement.** Once auto-derive is shown to be reliable across the real corpus, the manual keyword can deprecate. Hold for one publishing cycle of real data before pulling.
5. **CI-side org-source validation.** Currently the CI workflow can't run `org-math-lint` (sources aren't checked in). If the source were ever made available to CI (e.g., via a private mirror), the workflow could run org-math-lint there too. Speculative; don't build for it now.
6. **`org-math-lint` itself depending on B.4's auto-derive.** Not a real coupling — they're independent. Just noting that this slice introduces validation in two places, both of which must be in agreement, and the test plan asserts that agreement explicitly.

### Not on the follow-up list

- A vendored KaTeX support table in this repo: explicitly not building; `org-math-lint`'s in-process KaTeX is more accurate.
- A regex-based delimiter balance check in `check_math.py`: explicitly out — coupling-only.
- A monitor / drift script that compares `org-math-lint`'s vendored KaTeX version against the site's runtime KaTeX: irrelevant until KaTeX is shipped at all.

---

## 11 — Commit shape

Expected commits (subagent-driven plan will lay these out in detail):

**Dotfiles:**
1. `feat(c): a3-pub.sh --check-math flag + org-math-lint subprocess gate`
2. `feat(c): B.4 essays handler auto-derives has_math from buffer markers`
3. `test(c): essays handler — has_math auto-derive + manual-override ert tests`

**Site:**
4. `feat(c): tools/check_math.py — has_math frontmatter coupling linter`
5. `test(c): tools/test_check_math.py — coupling-only sibling tests`
6. `chore(c): retire {{< math >}} shortcode + convert example-one to real LaTeX`
7. `chore(c): example-three carries \(E = mc^2\); has_math: true`
8. `ci(c): hugo.yaml + ci-local.sh — wire 25th linter pair`
9. `docs(c): CLAUDE.md — Math pipeline architecture subsection + linter-pair count`

Total: 9 commits (3 dotfiles + 6 site), distributed across two repos. ~150-200 LoC of new code, ~50 LoC of edits to existing modules, ~75 LoC of new tests.

---

## 12 — Sequencing context

Per parent decomposition [[phase-3-decomposition]]:

| Slice | Status |
|---|---|
| A — Access control + link semantics | shipped 2026-05-24 |
| B.0 — Shared publisher infra | shipped 2026-05-25 |
| B.1 — Garden handler | shipped 2026-05-25 |
| B.1.1 — Pre-export id-link rewriter | shipped 2026-05-26 |
| B.2 — Library handler | shipped 2026-05-30 |
| B.3 — Research handler | shipped 2026-05-31 |
| B.4 — Essays handler | shipped 2026-05-31 |
| F — Citation pipeline | shipped 2026-06-01 |
| **C — Math validator** | **this spec — designed 2026-06-01** |
| D — Unified semantic markup (def/thm/figure/multi-target) | queued |
| E — Explorables + per-page widgets | queued |

D / E remain ahead of C in dependency order only loosely — C's surface is so contained (a shell hook, a buffer scan, a 50-LoC linter, a stub deletion) that it has no architectural prerequisites beyond what's already shipped. D folds the existing multi-target export design (`2026-05-13-multi-target-export-design.md`); E is its own future spec.
