# Phase 3 sub-project A.1.c: asset handling — design

**Date:** 2026-05-23
**Status:** brainstormed; plan pending
**Phase fit:** Phase 3, sub-project **A**, slice **A.1.c** (third of five in A.1 sequence: A.1.0 bootstrap → A.1.a foundations → A.1.b link rewriter → **A.1.c asset handling** → A.1.d unpublish + integration).
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §6 (link rewriting + HTML escape contract) + §7 (asset handling) + §10 (A → B interface) + §12 (A.1 vs A.2 scope split, item #6).
**Session policy:** no commits between sessions — author reviews + commits manually.

## 1 — Goals

Replace A.1.b's `:pending-asset` rewriter stub with real handling for asset-shaped org links. Specifically, for any `[[./assets/...]]` (relative), `[[~/org/notes/assets/...]]` (absolute home), or `[[/abs/path/...]]` form pointing at a non-`.org` file, the elisp library must:

1. **Resolve** the link to a canonical-root position under `~/org/notes/assets/` (either `page/<source-slug>/` per-page or `shared/` site-wide).
2. **Validate** that per-page references stay within the source note's own slug namespace (cross-namespace use → inert + WARN).
3. **Auto-remediate** out-of-root assets by moving them into canonical position (`git mv` if tracked, `mv` otherwise) + rewriting the `.org` source link.
4. **Copy** referenced assets into the published bundle (`content/<section>/<slug>/` per-page; `static/notes-shared/` shared).
5. **Clean up** stale per-page assets — bundle files not in the current ref set + not matching `index.md` patterns get removed each publish.
6. **Emit HTML** for the link — `<img>` for image extensions, `<a href>` for everything else — applying the new `--html-escape` helper that this session's spec amendments introduced.
7. **Validate** the committed bundle tree via a new Python linter pair (`tools/check_org_assets.py` + sibling), the 24th in CI.

This slice closes spec §12 A.1 item #6 ("Asset canonical folder + pre-publish validation + auto-remediation + per-page bundle copy + 24th linter pair") and lands the HTML-escape helper retrofit decided in this session as a parent-spec amendment in commit `62636ef`.

## 2 — Non-goals (deferred or out of scope)

- **Unpublish flow + integration tests.** Belongs to A.1.d.
- **Slug-shift asset directory rename.** When a note's slug shifts (`foo` → `foo-v2` via `#+HUGO_SLUG:` or title change), its `assets/page/foo/` directory does NOT auto-rename to `assets/page/foo-v2/`. Author handles manually. A.1.d may tie this to URL-history slug-change events.
- **Shared-asset conflict resolution when out-of-root same file linked from multiple notes.** First note's publish wins; subsequent notes get `(missing asset: …)` + WARN (because the source file was moved during the first remediation). Author resolves by relocating to `assets/shared/`.
- **`--strict` flag plumbing.** Deferred to A.2 per parent spec §6. A.1.c hard-codes WARN-vs-INFO; the `--strict` flag (which would promote WARN to ERROR) is not wired yet.
- **Shared-asset garbage collection.** Spec §7 explicitly defers a `--gc-shared` flag — A.1.c never deletes from `static/notes-shared/`.
- **Asset cite metadata.** Asset captions / figure-cite integration belongs to sub-project D (unified semantic markup) or F (citations). A.1.c emits bare `<img>`/`<a>` with no cite hooks.

## 3 — Carry-forward context

- **A.1.b shipped 2026-05-23** with 109 ert tests and a `:pending-asset` placeholder for the asset link branch in `a3madkour-publish-rewrite.el` (~line 280). A.1.c replaces that branch.
- **HTML escape contract** added to parent spec §6 in commit `62636ef`. A.1.c implements `a3madkour-pub--html-escape` and retrofits A.1.b's three existing `:html` emit points alongside its own new emits.
- **Spot-check tooling** (`a3-pub.sh` wrapper from A.1.b) is functional and loads the publish-rewrite module via straight + `-l a3madkour-publish-rewrite`. A.1.c spot-check piggybacks on this.

## 4 — Rewriter return shape (hybrid HTML + path metadata)

A.1.b's asset branch returned `(:pending-asset ORIG-LINK :warnings (...))`. A.1.c upgrades to:

```elisp
(:html "<img src=\"x.png\" alt=\"My screenshot\" />"
 :resolved-path "x.png"                     ; bundle-rel for page; "/notes-shared/X" for shared
 :source-path "~/org/notes/assets/page/foo/x.png"
 :kind image                                ; image | other
 :warnings nil)
```

Rationale:

- `:html` matches A.1.b's id-link/file-link/external/typed-link shape — B's per-section publisher splices the string in unchanged.
- `:resolved-path` + `:source-path` give `a3madkour-pub/asset-validate-and-copy` everything it needs for the copy queue + stale-cleanup diff without re-parsing the HTML.
- `:kind` is exposed for downstream use (e.g., B's per-content-type publishers may want to wrap image vs link emits in `<figure>` or similar; A.1.c itself does NOT add figure wrappers — bare `<img>` / `<a>` only).

For inert outcomes (cross-namespace, missing file, out-of-root with auto-remediate off), the rewriter returns:

```elisp
(:inert "(missing asset: x.png)"
 :warnings ("out-of-canonical-root: x.png; run with --auto-remediate or move manually"))
```

The `(missing asset: NAME)` text is rendered verbatim into the bundle — a visible inert marker on the page so the author notices.

## 5 — Asset resolution algorithm

For a link `[[<path>][<text>]]` where `path` matches `a3madkour-pub--asset-shaped-link-p` (no URL scheme AND extension ≠ `org`):

**Step 1 — Normalize the path.**

- Relative (`./assets/...`) → resolve against the source `.org` file's directory.
- Absolute (`~/...`, `/abs/...`) → `expand-file-name`.
- Result: an absolute filesystem path.

**Step 2 — Classify against canonical root.**

```
canonical-root = (expand-file-name a3madkour-pub-canonical-asset-root)
              = ~/org/notes/assets/                  (defcustom; user-overridable)

:kind page          if path begins with <root>/page/<slug>/<filename>
:kind shared        if path begins with <root>/shared/<filename>
:kind out-of-root   otherwise (anywhere else on the filesystem)
:kind missing       if file doesn't exist (regardless of location)
```

**Step 3 — Dispatch by kind.**

| Kind | Action |
|---|---|
| `page` + own-slug matches | Resolve. Copy queued to `BUNDLE-DIR/<filename>`. Emit `<img>`/`<a>` with `src="<filename>"`. |
| `page` + own-slug differs | **Cross-namespace error.** Emit `(missing asset: <filename>)` inert marker + WARN ("link from bar.org to assets/page/foo/X; move to shared/ to share"). |
| `shared` | Resolve. Copy queued to `static/notes-shared/<filename>`. Emit with `src="/notes-shared/<filename>"`. |
| `out-of-root` + `auto-remediate t` | Auto-remediate (Step 4). Then re-dispatch as `page` (now matching own-slug). |
| `out-of-root` + `auto-remediate nil` | `(missing asset: <filename>)` + WARN ("out-of-canonical-root; run with --auto-remediate or move manually"). |
| `missing` | `(missing asset: <filename>)` + WARN ("source file does not exist"). |

**Step 4 — Auto-remediation flow.**

```
destination = ~/org/notes/assets/page/<source-slug>/<filename>

if destination exists with same content (byte-equal):
  no move needed; just resolve.

if destination exists with different content:
  hash = SHA-1 of source file content, first 6 hex chars
  destination = ~/org/notes/assets/page/<source-slug>/<basename>-<hash>.<ext>
  (recurse on collision check; loop terminates because content-hash is deterministic)

if DRY-RUN:
  log INFO ("would move: <src> → <dst>")
  return :remediated-dry-run

else:
  if source is git-tracked (vc-git-handler-p): git mv <src> <dst>
  else:                                          mv <src> <dst>
  rewrite the .org source link to the new canonical relative path
  log INFO ("moved: <src> → <dst>")
  return :remediated
```

The org-source rewrite is buffer-level — `(save-excursion (goto-char (point-min)) (while (search-forward OLD-LINK nil t) (replace-match NEW-LINK t t)))` inside the publish run, then `save-buffer`. Author sees both the file move and the link change in `git status` afterward — explicit side effect, no hidden state.

**Step 5 — HTML emission.**

```
kind = image  if (file-name-extension path) ∈ a3madkour-pub-asset-image-extensions
       other  otherwise

display = (if (and text (not (equal text path))) text (file-name-nondirectory path))
src     = bundle-rel-path                       ; page: just filename; shared: /notes-shared/<filename>

if kind == image:
  :html → (format "<img src=\"%s\" alt=\"%s\" />"
                  (a3madkour-pub--html-escape src)
                  (a3madkour-pub--html-escape display))
else:
  :html → (format "<a href=\"%s\">%s</a>"
                  (a3madkour-pub--html-escape src)
                  (a3madkour-pub--html-escape display))

(missing / cross-namespace / remediation-failed):
  :inert → (format "(missing asset: %s)" (a3madkour-pub--html-escape (file-name-nondirectory path)))
```

**Image extensions** (`a3madkour-pub-asset-image-extensions` defcustom):
`png jpg jpeg gif svg webp avif`. Everything else → `<a href>`. Unknown extensions fall through to link form (safest default).

## 6 — API surface (new + amended)

New file `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`:

```elisp
;; Defcustoms
a3madkour-pub-canonical-asset-root        ; default "~/org/notes/assets"
a3madkour-pub-asset-image-extensions      ; default '("png" "jpg" "jpeg" "gif" "svg" "webp" "avif")
a3madkour-pub-asset-auto-remediate        ; default t
a3madkour-pub-notes-shared-static-dir     ; default "<site-repo>/static/notes-shared"
                                            ; (resolved relative to publish driver's site-root)

;; Public
(a3madkour-pub/rewrite-asset-link PATH TEXT SOURCE-NOTE-ID &optional DRY-RUN)
  ;; → (:html ... :resolved-path ... :source-path ... :kind ... :warnings (...))
  ;;   or (:inert ... :warnings (...))
  ;; Drives the asset branch in a3madkour-publish-rewrite.el's dispatcher.

(a3madkour-pub/asset-validate-and-copy ORG-FILE BUNDLE-DEST-DIR &optional DRY-RUN)
  ;; → (:copied (FILE ...) :removed (FILE ...) :warnings (...) :errors (...))
  ;; Walks ORG-FILE for asset refs; copies referenced assets into BUNDLE-DEST-DIR or
  ;; the shared static dir; removes stale per-page assets per blacklist policy (§7).

;; Private helpers (a3madkour-pub--asset-*)
(a3madkour-pub--asset-resolve-path PATH SOURCE-NOTE-ID)
  ;; → (:kind page|shared|out-of-root|missing :abs-path ... :rel-path ...)

(a3madkour-pub--asset-cross-namespace-p RESOLVED SOURCE-SLUG)
  ;; → non-nil when :kind page and the path-slug != SOURCE-SLUG

(a3madkour-pub--asset-auto-remediate SOURCE-ABS DEST-SLUG DRY-RUN)
  ;; → (:moved-to ... :method git-mv|mv :info ...) or (:error ...)
  ;; collision: SHA-1 first 6 hex chars suffix

(a3madkour-pub--asset-bundle-dest RESOLVED BUNDLE-DIR)
  ;; page → BUNDLE-DIR/<filename>; shared → notes-shared-static-dir/<filename>

(a3madkour-pub--asset-cleanup-stale BUNDLE-DIR REFERENCED-FILES)
  ;; removes BUNDLE-DIR/* not in REFERENCED-FILES ∪ {index.md, _index.md, index.*.md}

(a3madkour-pub--extract-asset-refs ORG-FILE)
  ;; parses ORG-FILE, returns list of (PATH . TEXT) pairs for asset-shaped links
```

Modified file `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`:

```elisp
;; New helper added (lives in rewrite.el because 3 of 4 emit points are here):
(a3madkour-pub--html-escape S)
  ;; Escapes & < > " ' for HTML attribute + element-body context.
  ;; Called by every :html emit in rewrite.el AND in publish-assets.el.

;; Retrofit applied to existing emit points:
;;   line ~176: id-link emit       (escape href + display)
;;   line ~237: typed-link emit    (typed-link-type is whitelist; NOT escaped;
;;                                  rewrite still re-uses id-link's escaped output)
;;   line ~275: external link emit (escape href + text)

;; Dispatcher branch updated:
((a3madkour-pub--asset-shaped-link-p path)
 (a3madkour-pub/rewrite-asset-link path text source-note-id))     ; was: :pending-asset stub
```

## 7 — Stale cleanup policy (blacklist)

`(a3madkour-pub--asset-cleanup-stale BUNDLE-DIR REFERENCED-FILES)` removes any file `F` in `BUNDLE-DIR` where:

- `F` is a regular file (not a directory), AND
- `F` is not in `REFERENCED-FILES`, AND
- `F` is not one of `index.md`, `_index.md`, or matches `index.*.md` (language-variant pattern), AND
- `F` does not start with `.` (skip dotfiles like `.publish-state` if a future slice adds one).

**Author contract**: do not hand-place files in `content/<section>/<slug>/` bundles. The bundle is owned by the publisher. Assets live in `~/org/notes/assets/{page/<slug>/, shared/}` — that is the source of truth. Files placed directly in a bundle without going through the org-source pathway WILL be removed on the next publish.

This is the simplest deterministic policy. A whitelist-with-sidecar alternative (track copied files in a `.publish-state` per bundle) was considered + rejected for A.1.c — adds a state file we'd need to maintain across slices. Revisit in A.1.d if hand-curated bundle additions become a real workflow need.

## 8 — Python linter (24th pair)

`tools/check_org_assets.py` + sibling `tools/test_check_org_assets.py`. Stdlib-only. CI registers both after the existing 23 linter pairs, before `hugo --minify`.

**What it validates** (walking the committed `content/<section>/<slug>/` tree):

```python
for bundle in content/*/<slug>/ where index.md exists:
  body = strip_frontmatter(read(bundle / "index.md"))
  refs = extract_img_src(body) + extract_a_href(body) + extract_markdown_image(body)
  for ref in refs:
    if ref starts with (http://, https://, mailto:, tel:, #) or is internal route (/garden/, /essays/, ...):
      skip
    elif ref.startswith("/notes-shared/"):
      assert (repo / "static" / ref[1:]).exists()
    elif "../" in ref:
      error: "path traversal: <ref>"
    else:
      assert (bundle / ref).exists()
  for f in files-in-bundle except {index.md, _index.md, index.*.md, dotfiles}:
    if f not in refs:
      error: "orphan: <f> in <bundle> not referenced by index.md"
```

**Why match both `<img src>` AND markdown `![alt](src)`** — A.1.c's rewriter emits raw `<img>` HTML, but B's per-section publisher (a future slice) might emit markdown image syntax for some content types. Linter matches both forms from day one — future-proofing is cheap.

**Errors are fatal; warnings advisory.** Soft warnings only for editor-cruft patterns (`*.tmp`, `*.swp` in a bundle).

**Test sibling coverage** (`test_check_org_assets.py`):

- ✅ Healthy bundle (`<img>` + `<a href>` to real files + `/notes-shared/` ref).
- ✅ Multi-bundle (validate 3 bundles in one run).
- ✗ Broken local ref → error.
- ✗ Broken shared ref → error.
- ✗ Orphan file → error.
- ✗ Path traversal (`../foo.png`) → error.
- ✓ External skip (`https://`).
- ✓ Anchor skip (`#section`).
- ✓ Internal route skip (`/garden/other-note/`).
- ✓ Empty bundle (just `index.md`) → passes.
- ✓ Markdown image syntax `![alt](file.png)` validated same as `<img>`.

**Explicitly NOT validated by Python:**

- Cross-namespace use (elisp-side enforcement; Python doesn't see org source).
- Round-trip asset ↔ org-source matching (no manifest, no source visibility).
- Global shared-asset GC (orphans in `static/notes-shared/` are spec-deferred — §7 §Copy/cleanup).

## 9 — Testing strategy

Three layers, matching A.1.b's pattern.

**Layer 1 — Elisp unit tests.** New file `a3madkour-publish-assets-test.el` + extensions to `a3madkour-publish-rewrite-test.el`. Baseline 109 (end of A.1.b); target **~150** ert tests at end of A.1.c (final count locked at writing-plans time).

Breakdown:

| Coverage area | New tests |
|---|---|
| Path resolution (relative/absolute, classification, missing detection) | ~12 |
| Auto-remediation (move, collision, dry-run, org-source rewrite, git-mv-vs-mv, INFO log) | ~10 |
| HTML emission (`<img>` vs `<a>`, alt fallback, escape applied, shared-asset src form, inert "(missing asset: X)") | ~10 |
| `asset-validate-and-copy` (page + shared copies, stale removal, dry-run, returns shape) | ~8 |
| Escape helper retrofit (3 emit points + regressions for `<>&"`) | ~5 |
| `rewrite-link` integration (asset branch dispatches, `:pending-asset` removed) | ~3 |

**Layer 2 — Python linter pair.** Per Section 8 — roughly 11 cases in the sibling.

**Layer 3 — Integration test.** `tools/test_publish_integration.py` lands in A.1.c with 7 asset-handling fixtures:

```
fixtures/asset-handling/
├── note-with-canonical-asset.org      → bundle has the asset; no WARN
├── note-with-shared-asset.org         → static/notes-shared/ has the asset
├── note-with-out-of-root-asset.org    → asset moved into canonical root;
                                          .org source rewritten; INFO log present
├── note-with-cross-namespace.org      → (missing asset: X) + WARN
├── note-with-missing-asset.org        → (missing asset: X) + WARN
├── note-with-stale-bundle.org         → pre-existing junk removed on publish
└── dry-run-out-of-root.org            → no side effects; INFO "would move" logged
```

Each fixture asserts on resulting `content/`, `~/org/notes/assets/`, `static/notes-shared/`, captured stdout, and (for out-of-root cases) the diff on the source `.org` file.

**Per-stage manual-verification cadence** — same pattern as A.1.b. Implementation plan defines 5-7 stages with ert-tests-must-stay-green checkpoints, plus a final spot-check stage (mirrors A.1.b Task 19): point `a3-pub.sh` at a real org note with assets, confirm assets land, `.org` source rewrites if any, Hugo build succeeds, rendered HTML matches expectations.

## 10 — File inventory

**Created** (this slice):

```
~/dotfiles/emacs-configs/custom/lisp/
├── a3madkour-publish-assets.el          NEW
└── a3madkour-publish-assets-test.el     NEW

a3madkour.github.io/
├── tools/check_org_assets.py            NEW
├── tools/test_check_org_assets.py       NEW
├── tools/test_publish_integration.py    NEW   (spec §11 placeholder until now)
└── docs/superpowers/specs/
    └── 2026-05-23-phase-3-a1-c-asset-handling-design.md  (this file)
```

**Modified** (this slice):

```
~/dotfiles/emacs-configs/custom/lisp/
├── a3madkour-publish-rewrite.el         add --html-escape; retrofit 3 emits;
│                                         replace :pending-asset branch dispatch
└── a3madkour-publish-rewrite-test.el    +5 escape-retrofit + +3 asset-branch integration tests

a3madkour.github.io/
├── .github/workflows/hugo.yaml          register check_org_assets.py + sibling
├── tools/ci-local.sh                    register same locally
├── CLAUDE.md                            linter count 23→24; note A.1.c shipped;
                                         update next-slice pointer
└── docs/superpowers/plans/
    └── 2026-05-23-phase-3-a1-c-asset-handling.md   NEW (lands after writing-plans)
```

## 11 — Commit layout (suggested; refined at writing-plans time)

Site repo:

```
docs(phase-3): A.1.c design — asset handling + 24th linter pair    (this brainstorm)
docs(phase-3): A.1.c implementation plan                            (writing-plans output)
ci(linters): register check_org_assets.py + sibling (24th pair)     (after dotfiles ship)
test(integration): asset-handling fixtures                          (after dotfiles ship)
docs(CLAUDE.md): A.1.c shipped + linter count 24                    (after dotfiles ship)
```

Dotfiles repo (3-4 commits across stages):

```
publish(html-escape): add --html-escape helper + retrofit rewrite emits
publish(assets): canonical-root resolution + classification (no I/O yet)
publish(assets): auto-remediation + copy + cleanup
publish(assets): rewrite-link integration + missing-asset rendering
```

Exact split refined at writing-plans time based on stage boundaries.

## 12 — Open carry-forwards for A.1.d

- **Slug-shift asset directory rename.** When a note's slug changes, `assets/page/<old-slug>/` does not auto-rename. Possible A.1.d hook into URL-history slug-change events to trigger a directory rename + bulk link rewrite.
- **Shared-asset conflict resolution.** When an out-of-root same file is linked from multiple notes, first publish remediates it under one note's `page/<slug>/`; subsequent notes get `(missing asset: …)` + WARN because the source is gone. Author resolves by relocating to `shared/`. A.1.d could detect this pattern + suggest `shared/` placement automatically.
- **`--strict` flag plumbing.** Deferred to A.2 per parent spec §6. A.1.c hard-codes WARN; the flag (which would promote WARN to ERROR) is not wired.
- **`.publish-state` sidecar / whitelist cleanup.** A.1.c uses a blacklist cleanup policy (bundle-dir minus `index.md` patterns and current refs). A.1.d may revisit if hand-curated bundle additions become a real workflow need.

## 13 — Cross-references

- Parent spec: `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §6 (link rewriting + HTML escape contract) + §7 (asset handling) + §10 (A → B interface) + §11 (testing strategy) + §12 (A.1 vs A.2 scope split).
- Prior slice: `docs/superpowers/plans/2026-05-20-phase-3-a1-b-link-rewriter.md` (A.1.b ships the `:pending-asset` stub this slice replaces).
- Memory: `memory/project_a1b_complete.md` (A.1.b ship detail) + `memory/project_next_slice.md` (A.1.c entry pointer + carry-forward status).

## Spec self-review checklist (per superpowers:brainstorming)

- [x] **Placeholder scan** — no TBD, TODO, or vague items. Test counts marked "roughly N" with "locked at plan time" caveat where appropriate.
- [x] **Internal consistency** — Section 4 return shape matches Section 5 emit logic matches Section 6 API surface matches Section 8 linter expectations.
- [x] **Scope check** — single implementation plan. Three open carry-forwards explicitly punted to A.1.d (Section 12), each with a one-line trigger condition.
- [x] **Ambiguity check** — "image extension" list is explicit (Section 5); "cleanup policy" is explicit (Section 7); "what the linter does NOT do" is explicit (Section 8). Hand-placed-files-get-nuked contract stated explicitly in Section 7 ("Author contract").
