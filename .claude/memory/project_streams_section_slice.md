---
name: project-streams-section-slice
description: "Streams section slice — shipped: merged + pushed to master 2026-05-20"
metadata: 
  node_type: memory
  type: project
  originSessionId: fab84d67-9908-43ee-a27e-dcf7540dea4f
---

**Shipped 2026-05-20.** Merge `f155d82` (`--no-ff` `Merge branch 'feature/streams-section'`), pushed `2bdf093..f155d82`. Branch `feature/streams-section` deleted; master 0/0 with origin.

New 7th top-level `/streams/`: per-stream archive pages (click-to-load privacy-preserving YouTube embed → `youtube-nocookie.com/embed/<id>?autoplay=1`), bidirectional `related_* ↔ source_stream` cross-refs to essays/garden/research/works, header live-pill driven by cron-polled `data/streams-live.yaml`, homepage upcoming-streams strip merging `data/streams-schedule.yaml` (user-authored) + `data/streams-twitch-cache.yaml` (Action). Cite integration per spec §10 — `archived`/`removed` only via triplicated predicate (`baseof.html` + `head.html` + `scripts.html`).

Infrastructure: 22nd + 23rd linter pairs (`check_streams_fixtures` + `check_streams_links` bidirectional symmetry), 11th JS bundle entry (`entry-streams.js` — click-to-load + `setupFilterChips` on `/streams/` section), CSS §46. Cron workflow `.github/workflows/streams-poll.yaml` (`*/5 *` cron) runs `tools/poll_streams.py` (stdlib-only urllib transport, 19 mocked-HTTP unit tests). Live→not-live transition auto-creates `content/streams/<YYYY-MM-DD>-<slug>/index.md` stub.

Spec `docs/superpowers/specs/2026-05-13-streams-section-design.md` (§0 reconciliation at scheduling: nav 6→7 / no RSS / verification-split). Plan `docs/superpowers/plans/2026-05-19-streams-section.md` (4681 lines, 38 tasks / 12 phases). Executed via `superpowers:subagent-driven-development` (fresh subagent per task + two-stage spec/quality review).

Hard-won lessons baked into shipped code (don't regress):
- **Hugo template gotchas caught only by `hugo` invocation**, after both reviewers approved verbatim — see [[reference-hugo-template-gotchas]]: `hasKey` → `isset`; `(printf "%v" $d) | substr 0 10` → `substr (printf "%v" $d) 0 10` (Hugo's `substr` is `STRING START LENGTH`; pipe puts string as LAST arg). Memory `feedback_verify_before_merge` correctly flagged this risk class. Hugo build verification is now part of the executable checklist; don't trust subagent + reviewer alone for template syntax.
- **Essay 3-col grid (.essay-layout: TOC | body | sidenote)** is unique to essays — cross-section partials placed between header + grid land OUTSIDE the reading column at full article width. Place inside `<div class="essay-body reading-column">` BEFORE `{{ .Content }}` for natural reading-column flow. Other 6 section single layouts wrap in `reading-column`/vertical flow, no equivalent fix needed.
- **`assets/js/search.js` SECTION_ORDER + SECTION_LABEL must both grow** when a new section is added — `SECTION_LABEL` alone gives `undefined` group headers; `SECTION_ORDER` filter at search.js:80 also drops the section entirely if absent. Both at top of search.js.
- **Filter-chip JS on section index** requires broadening the `scripts.html` predicate from `eq .Section "streams" AND eq .Kind "page"` to just `eq .Section "streams"` — otherwise chips render but don't filter. `streams.js` self-guards on `.streams-index .filter-chips` selector so it no-ops on per-stream pages.
- **Hyphenated data filenames** (`data/streams-live.yaml` etc.): use `index site.Data "streams-live"`, never `site.Data.streams-live` (silently breaks per [[reference-filter-chips-data-tags-space-delimited]] family of CLAUDE.md gotchas).
- **Plan amendments shipped vs verbatim** (record per spec §0 pattern): JS bundle predicate broadened (filter-chip wiring); essay from-stream insertion site moved inside `.essay-body`; SECTION_ORDER addition (one-line follow-up beyond the SECTION_LABEL the plan called for).

**Agent-environment update (CONTRARY to prior memory):** Hugo IS runnable in this sandbox — `hugo version`, `hugo --minify`, `hugo server` all worked. `pkill hugo` triggers exit 144 (likely sandbox kill on `hugo server` cleanup); a long-running `hugo server` started fine and served content for the spot-check. Updates [[project-next-slice]]'s "SIGKILLs every hugo invocation" caveat — partially false; short builds + dev-server-startup work.

User-side post-merge bootstrap (still required — flag at session-start when needed): Twitch dev-app (https://dev.twitch.tv/console/apps) → `TWITCH_CLIENT_ID` + `TWITCH_CLIENT_SECRET` repo secrets; YouTube Data API v3 key → `YOUTUBE_API_KEY` repo secret; `TWITCH_USER_LOGIN` + `YOUTUBE_CHANNEL_ID` repo vars. Then `workflow_dispatch` once before relying on cron. Until that lands, `data/streams-live.yaml` stays in the seeded not-live state and the live-pill emits nothing.

See also: [[reference-hugo-template-gotchas]] (the slice's loudest lesson), [[project-time-synced-poetry-slice]] (prior subagent-driven slice), [[project-next-slice]].
