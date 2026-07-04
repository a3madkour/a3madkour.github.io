---
name: project-lhci-url-validator-complete
description: LHCI 4.1 — pre-LHCI URL validator shipped 2026-06-04; new 26th linter pair check_lhci_urls + 2 CI steps; kills the 5-min push→404 round-trip
metadata: 
  node_type: memory
  type: project
  originSessionId: 0420f74c-d40e-4e4d-87f6-3b505a6587c3
---

# LHCI URL validator (4.1) — shipped 2026-06-04

**8 commits on master, push range `c043c0e..41c7a37`:**

1. `1bfef6d` spec — design approved (replaces 2026-06-01 stub).
2. `1ad4bcc` plan — 8 tasks across 5 commits.
3. `79ca137` feat — scaffold + `file_for_url` + `check_existence` (5 tests).
4. `4a67db0` feat — `check_equality` (4 tests, ordered list comparison).
5. `e22d316` feat — `check_assert_matrix` (4 tests, regex coverage + syntax validation).
6. `744fb7b` feat — `run()` orchestrator + `main()` + 5 bootstrap tests (18 total).
7. `a2f5a57` ci — wire into `.github/workflows/hugo.yaml` after smoke.
8. `4066874` docs — CLAUDE.md (25→26 pairs, 63→65 CI steps).
9. `41c7a37` ci — `tools/ci-local.sh` mirror (plan gap caught in execution).

## What ships

`tools/check_lhci_urls.py` (~165 LOC) + `tools/test_check_lhci_urls.py` (18 tests, ~248 LOC). Three checks: existence (each `collect.url` URL → `public/<path>/index.html`), desktop/mobile equality (ordered list parity), assertMatrix regex coverage (every `matchingUrlPattern` matches ≥1 URL). Exit 0/1/2 (clean/validation-failure/bootstrap-failure).

CI step pair inserted between `check_smoke.py` and `check_page_weights.py`. Local smoke confirmed: clean run = `"check_lhci_urls: OK (12 URLs, 1 assertMatrix overrides)"`; URL drift caught (2 errors); regex drift caught (1 error). LHCI local-run blocked by no-chromium-on-PATH per [[reference_ci_local_lhci_deps]]; CI runs it.

## Why

B.4 push triggered two consecutive LHCI 404 round-trips (5 min each) from fixture-slug retirements: `example-essay-one` → `example-one`, and `memory-and-play`/`what-is-a-narrative-atom` → `example-theme-one`/`example-question-one`. Validator fast-fails in seconds.

## What's still deferred

- **4.2 sitemap-derived URLs** — auto-generate `collect.url` from `public/sitemap.xml` grouped by Hugo (Kind, Section, Type). ~80 LOC + Hugo template emitting `representative-pages.json`. Pick up when next fixture retirement makes manual URL editing painful.
- **4.3 visual-feature fingerprint** — auto-extend on novel CSS classes / shortcodes. ~150 LOC + manifest snapshot. Pick up after 4.2 is in place.

## How to apply

When a future B.5/B.6/B.7 slice retires a fixture slug that's pinned in `lighthouserc.{json,mobile.json}`, the local pre-push `tools/ci-local.sh` run now catches it before push. Author still hand-edits the configs — that automation is 4.2's job.

## Process notes

- Subagent-driven execution: 4 implementer dispatches + 4 spec/quality reviewer dispatches + 1 final reviewer. All TDD (failing test → minimal impl → passing test → commit).
- Plan-gap caught in flight: `tools/ci-local.sh` mirrors `hugo.yaml` step-for-step; plan only mentioned the GHA workflow. Auto-mode call: added the mirror commit (`41c7a37`) before push so local CI matches remote CI.
- Working-tree hygiene preserved across all 8 commits: prior session's uncommitted memory files + `content/essays/example-multi/*` D.2 fixture changes never bundled into LHCI commits.

## Context

- Spec: `docs/superpowers/specs/2026-06-01-lhci-representative-page-set-design.md`
- Plan: `docs/superpowers/plans/2026-06-04-lhci-url-validator.md`
- Queued-slice memory now superseded: [[project_lhci_representative_pages_queued]] — 4.1 closed, 4.2/4.3 still queued.
- LHCI variance reference: [[reference_lhci_kitchen_sink_essay_variance]]
