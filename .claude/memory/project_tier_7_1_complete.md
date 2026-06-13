---
name: tier-7-1-complete
description: "Tier 7.1 (LHCI sitemap-derived URLs) shipped 2026-06-12; gen_lhci_urls.py + Hugo lhci-pages.json manifest; ~22 unit tests"
metadata:
  node_type: memory
  type: project
---

**Shipped 2026-06-12.** Tier 7.1 — LHCI sitemap-derived URLs (originally 4.2 in [[project-lhci-representative-pages-queued]]). 4.1 (`check_lhci_urls.py`, [[project-lhci-url-validator-complete]]) stays as defense-in-depth.

Site commits: `9bd5aac..827a209` (15 commits: spec + plan + 13 implementation).

What landed:

- New Hugo output format `LHCI-PAGES` (`hugo.yaml` + `layouts/index.lhci-pages.json`) emits `public/lhci-pages.json` — array of `{url, kind, section, type}` per regular page + section + home.
- New `tools/gen_lhci_urls.py` — stdlib-only generator. Functions: `group_pages` (tuple-key), `pick_representative_urls` (alphabetical-first per group), `render_assert_matrix` (group-keyed overrides → URL patterns; Python 3.13 re.escape workaround for `\-` → `-`), `rewrite_lighthouserc` (preserves preset, numberOfRuns, base assertions, upload). `run(repo_root, dry_run)` entry + `main()` with `--dry-run` flag.
- New `tools/test_gen_lhci_urls.py` — 22 unit tests covering grouping, picking, override application, idempotency, failure modes, dry-run.
- New `tools/lhci-overrides.json` — group-keyed assertion thresholds. Replaces the inline `assertMatrix` entry that hand-targeted `/essays/example-one/`.
- CI workflow + `tools/ci-local.sh` insert the regen + sibling test between `hugo --minify` and the LHCI steps.
- CLAUDE.md note added.
- First-CI-after-merge: URL count 12 → 26 (one representative per Hugo (sub-)section); essay representative shifted from `example-one` to `example-blocks-crossref` (alphabetical first); assertMatrix override (`page:essays:essays` → mobile perf 0.85) auto-migrated to the new pick.

Spec: `docs/superpowers/specs/2026-06-12-lhci-sitemap-derived-urls-design.md`.
Plan: `docs/superpowers/plans/2026-06-12-lhci-sitemap-derived-urls.md`.

**Side effects worth noting:**
- LHCI CI runtime roughly doubles (12 → 26 URLs).
- Now auditing chrome pages (`/about/`, `/blog/`, `/credits/`) and library leaves (`/library/listening/` etc.) and works sub-sections that weren't audited before. More layout coverage; harmless.
- Base assertions block in lighthouserc files now multi-line JSON (Python json.dumps indent=2 expands arrays). Functionally identical to the previous one-line form.

**Follow-ups (queued in spec §6):**
1. Tier 7.2 — visual-feature autodetect. ~150 LOC. Trigger: after 7.1 fingerprint corpus is observable across 2-3 LHCI runs.
2. Per-essay JS bundle auditing. Trigger: first explorable essay where bundle exceeds page-weight gates.
