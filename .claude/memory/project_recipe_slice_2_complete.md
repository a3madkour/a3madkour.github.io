---
name: project_recipe_slice_2_complete
description: Recipe Slice 2 (org authoring + lint + export) — implemented & harness-verified via SDD; awaits real-publish acceptance + push
metadata: 
  node_type: memory
  type: project
  originSessionId: 97b081c2-f09d-4384-bd76-a05215511347
---

**Recipe Slice 2 — org authoring → lint → export — IMPLEMENTED + harness-verified (2026-07-09/10), NOT pushed.** The follow-up to Slice 1 ([[project_recipe_section]]): author a recipe in org-mode and publish it to the shipped Slice 1 frontmatter contract.

**Design:** `docs/superpowers/specs/2026-07-09-recipe-slice-2-org-authoring-design.md` (spec `a679b81`, refined). **Plan:** `docs/superpowers/plans/2026-07-09-recipe-slice-2.md` (`2bf7460`). Prior-art research: org-chef (PROPERTIES-drawer idiom, key spellings) + emacs-otdb (org-table ingredients) + Cooklang (data model only). Executed via subagent-driven-development (14-task plan, fresh implementer+reviewer per task).

**Authoring shape (all keywords-first, natural `#+TITLE:` at top):** one `.org` per recipe — `#+HUGO_SECTION: recipes` + `#+TITLE:`/`#+DATE:`/`#+FILETAGS:`/`#+HUGO_SUMMARY:`, a `:PROPERTIES:` drawer (`:servings:` req; `:yield-unit:`/`:prep-time:`/`:cook-time:`/`:cuisine:`/`:category:`/`:video:`/`:image:` opt), a headnote, and three subheadings: `** Ingredients` (`#+NAME: ingredients` org table, cols `qty|unit|item|group|note|alt`), `** Steps` (ordered list, leading `[mm:ss]` kept verbatim), `** Sources` (link list `- [[url][name]] — note`).

**Code (dotfiles `~/dotfiles/emacs-configs/custom/lisp/`, branch `main`, 17 commits `7161d59..2d6ac4a`, 780/780 ert):**
- `a3madkour-publish-recipes.el` — garden/research-peer per-file handler, registered as the `recipes` living-publish section. Pipeline: lint → parse drawer+3 subtrees → strip subtrees → ox-hugo body export → `normalize 'recipes` → inject recipe keys → render flow-style YAML (key-hook, like research `outputs`) → copy `:image:` → write `content/recipes/<slug>/index.md` → record-publish. Whole body in one `condition-case` (failures → `on-done 'err`).
- `a3madkour-recipe-lint.el` — pre-publish linter, 6 rules, org `file:line` errors; `a3-pub.sh`-invoked, default-on, `--skip-recipe-check` (env `A3_PUB_SKIP_RECIPE_CHECK`, exported).
- `a3madkour-publish-frontmatter.el` — new `recipes` normalize branch (standard fields only; handler injects the rest).
- `a3-pub.sh` — recipe modules wired into all 3 `-l` blocks + the flag.

**Site docs (`master`):** CLAUDE.md "Recipe authoring (org → export)" para + Slice 2 marked shipped in the section spec (`5f21a18`). No site *code* change — Slice 1 already renders the contract.

**5 bugs caught DURING execution (not shipped):** (1) org-element only tags a file-leading `:PROPERTIES:` drawer as `property-drawer` when it's the LITERAL first buffer element — keywords-first authoring made it a generic `drawer`, silently dropping all metadata → position-robust extraction (`substring-no-properties` + `org-element-interpret-data` + regex scan), see [[reference_org_element_file_property_drawer_position]]; (2) source parser split on the note em-dash before parsing the link, mangling links whose description contains an em-dash (the spec's own example) → parse link first; (3, CRITICAL, final review) `"recipes"` missing from `a3madkour-pub/sections` #+HUGO_SECTION allow-list → `note-section` user-errors on any recipe file OUTSIDE `collect-triples`' condition-case → would abort the ENTIRE living publish; (4, final review) bare `:image:` drawer filename never copied to the bundle → broken JSON-LD image URL; (5, ox-hugo E2E) the file-level `:PROPERTIES:` drawer (generic, keywords-first) LEAKED INTO THE BODY — ox-hugo renders a generic drawer's contents as body text; `--strip-data-subtrees` removed the 3 heading subtrees but not the drawer → also strip the leading `:PROPERTIES:…:END:` block before export. All 5 have regression tests. **Lesson: each verification layer caught a different class — ert (unit logic), the export harness (data shape), the whole-branch review (integration/allow-list), and ONLY the real ox-hugo E2E caught the body leak. Bugs 3/5 were invisible to 780 green tests because tests bypass `note-section` + ox-hugo.**

**Verification done (FULL E2E):** drove the REAL `publish-recipe-file` through ox-hugo (org-roam identity stubbed via `cl-letf` — only `note-metadata`/`note-slug`/`note-url`/`site-root`/manifest), emitting into the site repo. Result: clean body (headnote only, `/italic/`→`_italic_`), both site linters clean, `hero.svg` copied, `image` key emitted → and `hugo` BUILT the page: renders title/ingredients/steps/sources, mounts the scaler (`recipe-rail`/`recipe-scale`), emits schema.org/Recipe JSON-LD (`@type:Recipe`, cookTime PT25M, recipeYield "4 servings", recipeIngredient/Instructions, isBasedOn=sources, image→bundle hero.svg) + the `index.json` download. Harness/fixtures in scratchpad (throwaway; site fixtures stay Slice-1 hand-authored).

**REMAINING (user-gated, NOT done):** publish through the author's REAL org-roam (so id/slug/url resolve for real, not stubbed). Both repos are pushed as of 2026-09-08 — site deployed, dotfiles `main` in sync at `e5e4c4e` — so the corpus run is all that is left. Slice 3 (meal-prep planner) still a separate deferred project.
