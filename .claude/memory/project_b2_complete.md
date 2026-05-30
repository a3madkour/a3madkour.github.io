---
name: b2-complete
description: "B.2 library handler — shipped 2026-05-29/30. 309 ert tests (+38 from B.1.1's 271) + 19 Python integration fixtures (was 14) all green. Per-medium YAML row publisher: 4 source org files (~/org/notes/library-{reading,listening,playing,watching}.org) → data/{reading,listening,playing,watching}.yaml rows via `a3-pub.sh --publish-living`. Two retroactive helpers shipped alongside (--git-mtime-of-file, --filter-editorial-tags) close B.1.x follow-ups #2 and #6. Slash-form section paths are now canonical; handler dispatch refactored from symbol-keyed → string-keyed alist. Task 17 (real-corpus spot-check) still pending — no real library-*.org annotations seeded yet."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-05-29/30):** B.2 — library per-content-type publisher per `docs/superpowers/plans/2026-05-29-phase-3-b-2-library-handler.md` and `docs/superpowers/specs/2026-05-29-phase-3-b-2-library-handler-design.md`. Subagent-driven across 17 tasks.

## What ships in B.2

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

**New module:**
- `a3madkour-publish-library.el` + `a3madkour-publish-library-test.el` — `publish-library-file` end-to-end. Walks top-level org headings via `org-element-parse-buffer`, normalizes each to a YAML-row plist, renders deterministically, writes-if-different. No ox-hugo invocation (drawer-only metadata), no link rewriter (no body to rewrite), no asset copier (covers manually committed to `static/library/covers/`). Per-medium config table inside the module captures the four-way variance: `data/<medium>.yaml` filename, default media_type, allowed media_types, allowed statuses.

**Modified modules:**
- `a3madkour-publish-history.el` — new `--git-mtime-of-file` helper (closes B.1 follow-up #2). Shells `git log -1 --format=%cI`; returns `YYYY-MM-DD` for tracked files, `nil` otherwise.
- `a3madkour-publish-frontmatter.el` — new `--filter-editorial-tags` helper (closes B.1.1 follow-up #6). Strips `TODO`/`NOEXPORT` from tag lists. Wired into the garden normalizer so the next garden publish-living run produces clean tags (see B.2 commit `82c3d2f` in site repo: 4 garden notes republished).
- `a3madkour-publish-living.el` — registers 4 library handlers via `with-eval-after-load`, all pointing at the same `publish-library-file`. Dispatch alist refactored from symbol-keyed → **string-keyed** (see "Architectural decisions" below).
- `a3-pub.sh` — `-l a3madkour-publish-library` added to the three publish-side intercepts (publish-living, publish-deliberate, default-exec). NOT `--check-orphans`.

### Site repo

- `tools/test_publish_integration.py` — 5 new fixtures under `TestLibraryPublishLiving`: `_publish_living_library` / source-yaml helpers; `test_library_publish_once` / `test_library_publish_idempotent` / `test_library_slug_shift` / `test_library_removed_item_unpublish` / `test_library_yaml_passes_site_linters`. The linter-parity fixture imports `check_library_fixtures.run()` + `check_library_links.run()` + `check_library_covers.run()` in-process. (Last one currently calls a wrapper because the existing linter doesn't expose `run(root)` — see follow-ups.)
- `hugo.yaml` — bumped pin to 0.162.1; `_index.html` → `_index.md` for the homepage (Hugo 0.162's tighter `security.allowContent` denies `text/html` source files).
- `CLAUDE.md` — Hugo version pin + the new Hugo-0.162 policy note.
- `docs/superpowers/plans/2026-05-29-phase-3-b-2-library-handler.md` — 17-task implementation plan.
- `docs/superpowers/specs/2026-05-29-phase-3-b-2-library-handler-design.md` — design spec.

## Test counts at slice end

- **ert: 309 total** (B.1.1 baseline 271 + 38 new across library, history, frontmatter, living). All passing.
- **Python integration fixtures: 19 total** (B.1.1 baseline 14 + 5 new B.2 fixtures). All passing.
- **`tools/ci-local.sh`**: passed end-to-end on Hugo 0.162.1.
- **Site linters** (library fixtures + links + covers): green against current site (still fixture rows) and against B-emitted YAML in tmp dirs (via the linter-parity integration fixture).

## Commits

In dotfiles repo (13 commits, `4b3bb8b..23fc5d7`):
- `00a47a8` git-mtime-of-file helper in publish-history
- `8e21499` filter-editorial-tags helper + retroactive garden fix
- `9c1b1c4` scaffold a3madkour-publish-library module + wrapper -l line
- `4b3bb8b` --title-to-slug helper per spec §5
- `d5d2a43` library --normalize-item required fields
- `05a1d09` library --normalize-item optional pass-throughs + last_modified
- `d10f44b` library --normalize-item tags filter
- `0067485` library --normalize-item extras + cover-file check
- `52709b3` library --render-library-yaml deterministic output
- `e445e2d` library --render-scalar single-quotes YAML-sensitive strings
- `cc0561b` library --render-scalar broader yaml indicator coverage
- `9747cd2` publish-library-file end-to-end
- `23fc5d7` string-keyed handler alist; register 4 library handlers

In site repo (6 B.2 commits + 2 housekeeping):
- `aad124f` integration fixture — library publish-once
- `0364bab` integration fixture — library publish idempotent
- `61e800f` integration fixture — library slug shift
- `daf9a84` integration fixture — library removed item unpublish
- `8131abc` integration fixture — library yaml passes 3 site linters
- `4fe4870` Hugo bump 0.162.1 + `_index.md` rename + spec deferrals
- `82c3d2f` republish 4 garden notes with TODO tag filtered (filter-editorial-tags side-effect)
- `6e5a746` memory snapshot for B.1.1 + goldmark unsafe reference

All pushed to origin/master (last push: `4fe4870..6e5a746`). Dotfiles at `23fc5d7` — pushed.

## Architectural decisions worth recording

1. **Slash-form section paths are canonical** (`library/reading`, `library/listening`, ...). `a3madkour-pub/sections` is the authoritative list. New handlers register string keys directly: `(cons "library/reading" 'a3madkour-pub-library/publish-library-file)`. Garden remains `"garden"` (no slash). This was the Task 11 refactor — B.1's symbol-keyed dispatch (`(cons 'garden 'fn)` then `symbol-name` bridge) didn't compose with multi-level paths like `library/<medium>` without round-tripping through interned symbols, and the slash form ends up cleaner across the codebase.

2. **YAML scalar quoting is best-effort, not bulletproof.** `--render-scalar` evolved twice during the slice (commits `e445e2d` + `cc0561b`) to single-quote YAML-sensitive strings (containing `:`, `#`, `-` at start, `[`, `{`, multi-line, etc.). Coverage is broader than B.1's date-only special-case but the fallback path still uses `%S` and can error on unknown types. Logged as a follow-up.

3. **Two retroactive helpers shipped in B.2** rather than as B.1.x patches, so the upgrades land together: `--git-mtime-of-file` (B.1 follow-up #2 — fall back to git mtime instead of file mtime when `#+HUGO_LASTMOD:` is absent) and `--filter-editorial-tags` (B.1.1 follow-up #6 — strip `TODO`/`NOEXPORT` from emitted tags). The garden normalizer now uses both; the next garden publish-living run will pick up the change (already observed in site commit `82c3d2f`).

4. **No relref / no anchor rewriter for library.** Library items have no body — only drawer metadata + optional `summary` line. So neither `rewrite-buffer-links` nor `goldmark.renderer.unsafe` are exercised by B.2. They stay site-wide-configured (from B.1.1) and ready for the next handler that needs them (research, essays, works).

5. **Library is the structural outlier.** B.2 emits per-medium YAML rows by replacing the entire file each publish — not by appending. The handler reads the full source file, normalizes every heading, sorts deterministically (by slug), and writes. Idempotency is automatic. No `unpublish-delete-bundle` analogue is needed because removed items just disappear from the regenerated YAML.

## Spot-check status (Task 17)

**Not yet performed.** No real `~/org/notes/library-*.org` annotations exist; in-batch integration fixtures cover the publisher behavior, but the round-3 equivalent of B.1's real-corpus seeding is still pending. To execute:

1. Author one or more entries per medium in `~/org/notes/library-reading.org` / `library-listening.org` / `library-playing.org` / `library-watching.org`, each with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: library/<medium>` (slash form per Architectural Decision 1).
2. Each top-level heading = one library row. Drawer properties drive the YAML fields (see spec §5 property mapping).
3. Run `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living`.
4. Inspect emitted `data/<medium>.yaml` for shape correctness; run `tools/check_library_fixtures.py` + `_links.py` + `_covers.py`.
5. Commit B-emitted YAML, push.

## Known issues / B.2.x follow-ups (logged, not blocking)

1. **`check_library_covers.py` should expose `run(root)`** like other linters do. The B.2 linter-parity fixture works around this with a wrapper but the API gap will bite the next handler that wants to assert against covers.
2. **`--render-scalar` fallback `%S`** can error on unknown types (custom structs, hashtables). Add a typed-default + WARN.
3. **`:group 'a3madkour-publish`** in defcustoms should be `'a3madkour-pub` to match the package prefix. Small cleanup, no functional impact.
4. **Works page sidebar labels overflow at desktop** (spec §13). Pre-existing; unrelated to B.2 but logged in this slice's spec for visibility.
5. **LHCI local failure** — local `tools/ci-local.sh` can't run Lighthouse CI without `chromium` on PATH; CI has it. Documented as non-blocking.
6. **`.Site.Data` deprecated in Hugo 0.156+** → migrate to `hugo.Data` site-wide eventually. Not B.2 work but flagged by the 0.162 bump.

## Lessons logged

- [[next-slice]] now points at B.3 (research handler) — see that memo for the next-session start.
- The slash-form / string-keyed dispatch lesson applies forward: B.3 will register `"research/themes"` + `"research/questions"` as two separate keys pointing at the same handler, in the same shape B.2 used for library.

## Next slice: B.3 (research handler)

Per design spec §12 slice ordering: B.1 → B.1.1 → B.2 → **B.3 (research)** → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F → C → D → E. Research splits into two cascade types (themes + questions) sharing one section path tree — first multi-type handler. See [[next-slice]].

## How to start the next session

Read site CLAUDE.md + this file + [[next-slice]] + parent B spec §9 (research pipeline shape). Then `superpowers:brainstorming` for B.3 — the themes/questions split + cross-linking (theme ↔ question, supporting_notes, related_essays) warrants a design pass even though the per-content-type infrastructure is now well-trodden.

## Cross-references

- Parent spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`
- B.2 spec: `docs/superpowers/specs/2026-05-29-phase-3-b-2-library-handler-design.md`
- B.2 plan: `docs/superpowers/plans/2026-05-29-phase-3-b-2-library-handler.md`
- Prior slice: [[b1-complete]] (carries B.1 + B.1.1)
- Decomposition: [[phase-3-decomposition]]
- Lessons referenced: [[goldmark-unsafe-for-ox-hugo-html]] (site-wide; not exercised by B.2), [[phase-3-library-tag-shelves]] (round-trip rule satisfied), [[phase-3-two-publish-commands]] (library is in the frequent+idempotent set)
