---
name: project-tier-6-deferred
description: Tier 6 (About Now widget) closed-by-deferral 2026-06-08; demoted back to deferred-features registry; homepage Currently widget already covers the auto part
metadata: 
  node_type: memory
  type: project
  originSessionId: df0f8dca-53dd-4978-ad74-36f105a7b286
---

**Closed-by-deferral 2026-06-08.** Tier 6.1 was the only row in Tier 6 of `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`. Brainstorm opened per the standard cycle, surfaced the actual overlap, user opted to skip rather than ship.

**Why deferred (the decision rationale):**
- The Phase 3 §4.2 Now widget spec was written *before* the homepage v3 Currently widget (`partials/home/currently.html`, shipped 2026-05-13) and *before* the four library YAMLs (`data/{reading,listening,playing,watching}.yaml`, B.2).
- Those two pieces together already auto-derive and surface Reading / Listening / Playing / Watching on the homepage.
- The only *new* value the About Now widget would add on top is hand-authored **Working on** + **Wondering** prose (the two sections of the original Phase 3 spec that have no YAML source).
- That part requires the author to commit to maintaining recurring "what I'm working on / wondering about" copy.
- The bio-half spec's own argument (2026-05-11) was that a stale Now widget signals "this site doesn't update" and reads worse than no Now at all — same argument now applied to "Working on / Wondering" without a maintenance commitment.

**Trigger to re-open:** Author actually wants a place to write recurring "Working on / Wondering" prose. Not "we could add this someday" — "I have copy I want to publish on a recurring basis."

**Where it lives now:**
- Roadmap row 6.1 marked `⊘` with a CLOSED-BY-DEFERRAL block summarizing this.
- Deferred-features registry "Authoring / metadata extensions" row updated with the new trigger and the factual correction that `layouts/about/single.html` has *no* placeholder slot (the previous wording was wrong — Tier 6 would have added the section from scratch).
- CLAUDE.md project status updated.

**What did NOT ship:** no spec, no plan, no code. The session that opened this brainstorm produced three documentation edits + this memory + one commit. See [[reference-d2-pdf-qa-followup]] tradition — when a brainstorm concludes "skip," that's the deliverable.

**Pre-scout pre-existing factual error corrected (in registry):** the roadmap row claimed "About page has a placeholder slot." It doesn't — `layouts/about/single.html` renders Bio / Where / Connect / Colophon and nothing else. Future re-openers should NOT spend time looking for the slot.

**Related:** [[project-next-slice]] · [[project-tier-1-10-complete]] · [[feedback-deferred-features-stay-visible]]
