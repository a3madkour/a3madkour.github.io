---
name: project-recipe-remediation-shipped
description: Recipe section + 29-row post-review remediation shipped and deployed 2026-09-07; 10 of 13 follow-ups also closed; what remains
metadata: 
  node_type: memory
  type: project
  originSessionId: ad301310-23dc-4009-b3e1-3375f3d4be7c
  modified: 2026-09-08T03:55:19.677Z
---

**SHIPPED AND DEPLOYED 2026-09-07.** `recipes` rebased onto `main`, max-effort
reviewed, remediated as a 19-node DAG, merged (`171a19d`), and deployed across
three green runs. `main` at `2d01fa1`. This closes the recipe work that had sat
unmerged since 2026-07-10.

**Sequence:** rebase (§50 collision — KaTeX kept §50, recipes moved to §51) →
`/code-review max` → 15 confirmed findings + ~15 runners-up → spec
`docs/superpowers/specs/2026-09-07-recipe-audit-remediation-design.md` (29 rows,
RC1.1–RC5.3) → plan → 19-node DAG, one reviewer per node, 4 nodes failed first
review and were fixed → merged → deployed → 10 of the 13 rows in
`docs/superpowers/specs/2026-09-07-recipe-followups.md` also closed.

**Guards added:** 35 → 38 linter pairs. `check_search_sections.py` (every
`section:` value the build emits must be registered in `search.js`),
`check_image_ladder.py` (template's `image` branch keys pinned to the linter's),
`check_meta_description.py` (descriptions must be flattened prose). 103 CI steps.

**RF3.3 closed 2026-09-08** — and the earlier note here was wrong on two
counts. Paper-on-burgundy *does* render (`.search-modal-chip.is-active`,
`.download-link:hover`), as does burgundy-on-paper (`.reenable-tracking`,
`.recipe-stp button`), so the fix was four real contrast pairings, not a
value-identity assertion. An identity assertion would have been actively wrong:
the two tokens are documented as semantically distinct and are allowed to
diverge — gating paper directly is what makes divergence safe. 17 → 21 pairings.

**RF3.4 closed 2026-09-08, both halves — and it too was understated.** A full
sweep put the thinnest pair at `warn`/`stone` **4.55:1**, tighter than either
pairing the row named and unmentioned by it. Reporting half: the gate now prints
each pairing's margin and closes with the sub-`TIGHT_MARGIN` set, so the sweep
is recomputed every run instead of living in a document that was wrong about it.
Palette half: three hue-preserving nudges (light `--color-warn` `#9c5719`, light
`--color-ink-fade` `#6c6862`, dark `--color-burgundy` `#df7481` in *both* dark
blocks) lift the floor from +0.05 to +0.25/+0.26. `TIGHT_MARGIN` is then set
*below* the palette's target (0.20 vs 0.25) so an empty report means clear-of-
the-line rather than on-it.

**The follow-ups document is now fully closed.** Remaining recipe work: Slice 3
(meal-prep planner, deferred by design) and the org pipeline, which has still
never run against the real org-roam corpus — see
[[project_recipe_slice_2_complete]]. That is the last unproven link.

**Corrections worth keeping:** RF2.5 (duplicate ids) was a **false positive** —
`grep -o 'id=[a-zA-Z0-9_-]*'` matches a bare `id=` with an empty capture, and
those empties collide. A real `html.parser` pass over 129 pages finds zero.
Chasing it found a genuine bug though: `.Summary` is rendered HTML, so 18 pages
shipped markup inside `<meta name=description>` / `og:description` — invisible
locally because the description is never rendered, public everywhere else.

See [[feedback_mutation_test_every_guard]] and
[[reference_playwright_reuse_existing_server]] for the two lessons that
generalize beyond this project.
