---
name: project-time-synced-poetry-slice
description: "Time-synced poetry runtime slice — shipped: merged + pushed to master 2026-05-19"
metadata: 
  node_type: memory
  type: project
  originSessionId: f5bcea34-8124-4ba8-a918-fcf90b93b5af
---

**Shipped 2026-05-19.** Merge `23e997b` (`--no-ff` `Merge branch 'feature/time-synced-poetry'`), pushed `2bb9220..23e997b`; follow-up stub commit `2bdf093`. Worktree + `feature/time-synced-poetry` branch removed; master 0/0 with origin.

Poetry pages with `[mm:ss]` body markers switch to a synced-reveal runtime: Hugo-side parser (`synced-marker-seconds.html` + `synced-text-parser.html` + `poem-synced.html`), routing in `works-poetry/single.html`; JS player `poem-synced.js` (entry `entry-poetry.js` → 10th bundle `poetry.<hash>.js`, page-narrow); CSS §45; §9 BibTeX "With audio reading." note; 21st linter pair `check_poetry_synced` + `example-poem-synced` fixture. Spec `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md`, plan `docs/superpowers/plans/2026-05-18-time-synced-poetry.md` (heavily amended in-flight — read its amendment notes before reusing).

Executed via `superpowers:subagent-driven-development` (10 tasks, fresh subagent + two-stage review each). Hard-won lessons baked into the shipped code (don't regress):
- **C1/C2 (final holistic review caught these; per-task reviews structurally couldn't):** word/uniform-mode wrapper line must NOT carry `data-t` (only words + markdown line-mode lines do) or §45's `.poem-line[data-t]` opacity:.06 multiplicatively crushes revealed words; JS tracks the **union** of `.poem-word[data-t]` ∪ `.poem-line[data-t]` (not an all-or-nothing ternary) so mixed word/markdown poems reveal.
- **Hugo `int` octal gotcha:** `int "08"`/`"09"` → "invalid syntax"; marker parts cast `int (float $s)`. See [[reference-hugo-int-octal-gotcha]]. Fixture deliberately keeps `[00:08]`/`[00:09]` as the CI regression guard.
- Spec §4's "markers never in rendered HTML" also covers `<meta>`/`og:description` — `head.html` strips `[mm:ss]` from the description fallback + fixtures carry explicit `summary:`.
- Fixture is strictly in-order, fixed 1s step (`Lorem`@0:01 → `veniam`@0:21, markdown line @0:17, escaped `\[00:99]` literal @0:19) per user spot-check request for legibility; untimed-inheritance behaviour is unit-test-covered, not in the live fixture.

**Environment caveat (recurred all session):** this agent sandbox SIGKILLs every `hugo` invocation (exit 144) — Hugo build/dev-server cannot be run by the agent here; rely on the user's dev server + CI-on-push. Stdlib linters DO run. Also: never run `hugo --minify`/`rm -rf public` against a worktree while the user has a dev server on it (poisons their server — happened, recovered via kill + rm public/resources + restart). LHCI never ran locally (env-blocked); CI runs it on push.

Follow-on queued: [[project-phase-3-org-synced-poetry-export]]. See also [[project-toc-collapsible-subsections-slice]].
