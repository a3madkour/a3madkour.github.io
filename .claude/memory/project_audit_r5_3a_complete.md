---
name: audit-r5-3a-complete
description: "R5.3a AMS-block consolidation SHIPPED 2026-07-05 (da48e80..b651784); 11 numbered shortcodes → thin wrappers over ams-block.html partial, proof bespoke; R5.3b next"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

# Audit R5.3a — AMS block consolidation (shipped)

**2026-07-05.** R5.3 was split (user decision): **R5.3a = AMS blocks (this)**; R5.3b = graph-panel single-partial, a separate later cycle. Executed **subagent-driven** (2 tasks, fresh implementer + reviewer each, Opus final review = READY). Design `da48e80`, plan `06004cb`, impl `3925b6c`, docs `54d8208`, + CLAUDE.md E2E-count fix `b651784`. Design/plan under `docs/superpowers/{specs,plans}/2026-07-05-r5.3a-*`. **Not yet pushed** at time of writing (local on master).

**What shipped:** the 11 numbered AMS block shortcodes (theorem/lemma/corollary/proposition/definition/remark/example/note/claim/conjecture/axiom) — identical modulo (kind label, `block-<kind>` class, `block-strong|block-soft` tier, counter key) — collapsed to one-line wrappers over a new shared `layouts/partials/ams-block.html`. **`proof.html` stays bespoke** (the outlier: unnumbered, `<em>` header, `:of` arg, ∎ tombstone; not duplicated, so nothing lost). 214 LOC → 11 wrappers + `proof.html` + ~20-line partial.

**Verification was a byte-identical rendered-HTML diff** (pure Hugo templates → deterministic): snapshot `public/essays` (non-minified) before, refactor, rebuild, `diff -r` must be empty. It was, across all 11 essay pages — proving the four invariants held (ref-block `Scratch "block-label-<id>"`, counter identity theorem-family-shared-vs-per-kind, `.block-header` markup for `block-renumber.js`, byte-identity). No new tests — the diff + `check_anchor_link` + `ci-local` guard it.

**Hugo gotcha (important, reusable):** a paired shortcode (`{{< theorem >}}…{{< /theorem >}}`) whose render logic moved into a partial FAILS to build — Hugo's static parser scans the *shortcode template source* for a literal `.Inner`/`.InnerDeindent` to decide the closing tag is valid, and a wrapper that only passes `"ctx" .` never mentions `.Inner`. Fix: pass `"inner" .Inner` as an extra dict key (a parser hint the partial ignores; it reads `$ctx.Inner`). See [[reference_hugo_paired_shortcode_partial_inner]]. Also: `$.kind` (not `.kind`) inside the partial's `with $id`/`with $title` blocks, since `.` is rebound.

**Next: R5.3b** — graph-panel single-partial. R5.2 already normalized works, so the 3 `graph-panel.html` partials now differ only by id/title/aria-label/legend-section → extract one shared partial + 3 thin includes. Then R5.4 (Python tooling dedup — duplicated linter test scaffolds). See [[audit-remediation-roadmap]].
