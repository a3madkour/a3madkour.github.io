---
name: project-phase-8-slice-3-final-qa
description: Phase 8 third slice (final QA pass) shipped 2026-05-13 (merge 1aa1a2e); mobile strip bug RESOLVED 2026-05-13 (commit bab359d); 2 deferrals + remaining QA items still queued
metadata: 
  node_type: memory
  type: project
  originSessionId: 24cd0623-f93e-4288-bac7-27d7f97abfbc
---

Phase 8 Slice 3 — Final QA pass — merged (partial).

Shipped to master 2026-05-13 (merge `1aa1a2e`, pushed to origin). 6 commits, 4 files, +280 lines (documentation only, no code changes).

**Why:** Spec `docs/superpowers/specs/2026-05-13-phase-8-design.md` §4 calls for a fix-on-find QA walkthrough as the Phase 8 close. The first session walked a small portion of the checklist and surfaced one true blocker bug plus two deferrable polish items. Rather than burn more context on the one bug we couldn't crack, Phase 8 ships with documented deferrals and the rest is queued for a fresh session.

**How to apply:**
- **Phase 8 is closed.** Pagefind runtime (Slice 1) + CI gates trio (Slice 2) + QA checklist (Slice 3) all shipped. The mobile strip bug is now resolved too (commit `bab359d`, 2026-05-13). Remaining QA checklist items + the two non-blocking deferrals (RSS UX, garden path-log retrieval) are still queued.
- **Next session priority:** resume the QA checklist (§1.1-1.5, 1.7-1.9 keyboard nav, §2 SR walkthrough, §3 CB sim, §4 mobile audit, §5 perf). Mobile strip bug no longer needs investigation.
- **Mobile strip bug resolution (for future similar issues):** root cause was horizontal document overflow at narrow viewports caused by `.site-nav` lacking `flex-wrap`. Firefox's `position: sticky` paint math fails when `html.scrollWidth > clientWidth` — DOM API reports correct `y=0` but paint is drawn against the wider scroll context. The fix is `flex-wrap: wrap` on the nav + `html { overflow-x: clip }` as defense-in-depth (`clip` does NOT create a scroll container, so sticky descendants keep working — `hidden` would break them).

**What this slice landed:**
- `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` — the canonical QA checklist (45 items across 5 categories), with §6 capturing the session's state (3 walked, 3 deferred, rest queued)
- `docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md` — spec stub for the garden visited-notes retrieval gap (consent banner has no UI consumer)
- `docs/superpowers/specs/2026-05-13-mobile-page-sidebar-strip-bug-design.md` — spec stub for the unresolved mobile strip pinning bug, including diagnostic outputs + failed-attempts list + a "Resume points" section for the next session
- CLAUDE.md updated: "Final QA — partial pass" added to Shipped; Phase 8 line replaced with "Phase 8 follow-up: mobile page-sidebar strip bug + finish QA walkthrough"

**Resolution of the originally-unresolved bug (commit `bab359d`, 2026-05-13):**
Not a compositor or `display: contents` bug as the original spec hypothesized. The first session's diagnostic was misleading because it was taken at a viewport width where the bug didn't reproduce — at the narrow widths where users actually see it, `<html>` had horizontal overflow (because `.site-nav` had no `flex-wrap`), which is what broke Firefox's sticky paint. The fix was a four-line CSS change + one HTML change (`<main class="home">` → `<div>`, an HTML-validation cleanup found during bisect). Full write-up in the spec stub's "Resolution" section. Diagnostic pattern: when DOM API says sticky is pinned but the user sees it scroll away, check `documentElement.scrollWidth > clientWidth` BEFORE pursuing compositor hypotheses.

**Related memory:**
- [[project-phase-8-slice-1-pagefind-runtime]]
- [[project-phase-8-slice-2-ci-gates]]
- [[project-page-sidebar-slice]] — original Phase 7 polish that shipped the strip code
