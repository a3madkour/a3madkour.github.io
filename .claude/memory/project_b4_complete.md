---
name: project-b4-complete
description: B.4 essays handler shipped 2026-05-31; first publish-deliberate slice; 398 ert + 33 integration; 4 B-emitted bundles replace 7 hand-authored fixtures; key insights on ox-hugo keyword handling
metadata: 
  node_type: memory
  type: project
  originSessionId: 5145878a-a130-45b0-84d6-28c736593219
---

# B.4 essays handler — shipped

**Shipped 2026-05-31** via `superpowers:subagent-driven-development` over a 17-task plan, local master (site + dotfiles both unpushed).

**Why:** First per-content-type publisher in publish-deliberate mode (vs. living mode for garden/library/research). Folds in the B.0 contract amend (`finish-publish :scope`) that would otherwise unpublish other bundles on first deliberate run.

**How to apply:** When picking up Sub-project F (citations) or any later per-type handler (works/about/streams), the established pattern is:
- Dispatch arm in `a3madkour-publish-frontmatter.el` via `'<section>` symbol
- New module `a3madkour-publish-<section>.el` with `--scan-*`, `--copy-asset-dir`, `--write-if-different`, `--render-frontmatter`, `--render-yaml-value`, `publish-<section>-file` pipeline
- Register in `a3madkour-pub-deliberate--handlers` alist (Task 9-style)
- Add `-l a3madkour-publish-<section>` to `a3-pub.sh` `--publish-deliberate` + default exec blocks

## Final state

- ert: **398 tests** (+42 over baseline 356)
- integration: **33 tests** (+7 over baseline 26)
- 7 hand-authored essay fixtures retired → 4 B-emitted bundles (example-{one,two,three,four})
- 10 site commits + ~10 dotfiles commits, all unpushed
- `tools/ci-local.sh` passes pre-LHCI (LHCI environmental locally; no chromium on PATH)
- Linter: all 50 linter pairs green; pagefind + cite-meta + smoke + page-weight green; Hugo build clean

## Key insights surfaced during spot-check (Task 16) → all closed in-slice

1. **ox-hugo HTML-encodes raw `{{< X >}}` in body** → use `@@hugo:{{< X >}}@@` org export-snippet syntax in source. Spec §6.3 template was wrong; corrected during Task 16. Scanner now scans org-source + post-export body together — see [[reference_ox_hugo_html_encodes_shortcodes]].
2. **Most `#+HUGO_<X>:` custom keywords are NOT surfaced in ox-hugo's frontmatter alist** — must read directly via `read-org-keyword`. Affects: `HUGO_SUMMARY`, `HUGO_SERIES_ORDER`, `HUGO_HERO`, `HUGO_TILE_SIZE`, `HUGO_FEATURED`, `HUGO_SOURCE_STREAM`. ox-hugo DOES surface: `HUGO_SECTION`, `HUGO_PUBLISH`, `HUGO_SERIES` (as list), `HUGO_TOC`. See [[reference_ox_hugo_keyword_passthrough]].
3. **`asset-validate-and-copy` only walks `[[org-link]]` references** — shortcode `src=` attrs + `#+HUGO_HERO:` keyword values are NOT picked up. Added `--copy-asset-dir` helper that recursively copies `~/org/essays/assets/<id>/` into the bundle. See [[reference_asset_validate_walks_org_links_only]].
4. **dispatch alist uses symbol keys; `note-section` returns string** — `assq` is `eq`-based so string-vs-symbol silently never matches. Fixed in `publish-deliberate` via `(intern ...)`. Latent B.0 bug; observable only after Task 9 registered the first handler.
5. **finish-publish `:scope 'deliberate`** correctly skips Step A + C and narrows Step B to touched id; integration test 14 confirms unrelated section bundles survive untouched.
6. **`tags: false` YAML emission** when `tags` is nil — renderer's `null → "false"` rule was correct for booleans but wrong for tags (which semantically = empty list). Fixed via key-aware special case in `--render-frontmatter`: nil tags → `tags: []`.
7. **`series` from `#+HUGO_SERIES:` arrives as single-element list** — normalizer coerces to string for essays.

## Architecture

- `~/org/essays/<slug>.org` → `M-x a3-publish-deliberate` → `content/essays/<slug>/index.md`
- Essays NOT roam-indexed; NOT under `org-notes-dir`; `publish-living` does not touch them
- Asymmetric cross-ref: essay→note via `[[id:UUID]]`; note→essay via a ref-note in `notes/ref-notes/`
- has_* body scanner runs on source + post-export body concatenated; 6 flags (sidenotes/citations/footnotes/math/widgets/video-sync); per-flag `#+HUGO_HAS_<X>:` keyword override wins absolutely
- Hero / per-essay assets live at `~/org/essays/assets/<id>/`; copied wholesale into bundle by `--copy-asset-dir`

## Fix-up commits during Task 16 spot-check

| Commit | Issue |
|---|---|
| `ae0a644` | Scan org source for shortcodes; inject summary key (Task 15) |
| `d04c6e7` | Intern section string before assq (latent B.0 dispatch bug) |
| `f3085d8` | tags=[] + series list→string + series_order from keyword |
| `e8bc32a` | --copy-asset-dir helper for per-essay asset directory |
| `735d05a` | Read HUGO_HERO/TILE_SIZE/FEATURED/SOURCE_STREAM directly |

## Known follow-ups (post-slice)

- Visual QA still owed: TOC scrollspy collapse on example-one (level-4 nesting), series-nav prev/next styling on /essays/example-one + example-two (curl confirmed series pill renders "example-series (Part 1)"; full visual = author task)
- B.4 follow-up #3 (shared `--render-frontmatter` extraction): B.5 triggers it
- B.4 follow-up #1 (`a3-unpublish-deliberate` command): author hits a stale deliberate publish
- Spec §6.3 template needs amendment to use `@@hugo:{{< X >}}@@` syntax (logged here, not yet edited)
- The 4 `~/org/essays/example-*.org` stubs + `~/org/essays/assets/essay-one-uuid-placeholder/` (hero.svg + example-widget + example.mp4 stubs) are NOT in version control — they live in the author's `~/org/` (not under any tracked repo). If the author wants reproducibility, they need to copy them into a tracked location.
