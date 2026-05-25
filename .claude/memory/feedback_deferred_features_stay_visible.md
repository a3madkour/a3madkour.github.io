---
name: Deferred features must stay visible in plans and exercised by fixtures
description: When triaging features out of a slice, document the deferral explicitly in the spec/plan and have fixtures exercise the deferred capability where possible
type: feedback
originSessionId: 624875d4-e750-49c5-9e96-c5bab4010528
---
When a brainstorm or plan defers a feature out of the current slice, two things must happen:

1. **Document the deferral explicitly** in the spec/design doc and the implementation plan. Not just "we picked these four" — also "we deliberately did not pick these four, here's the reason, here's the slice they belong to." A reader six months later should be able to see: this was considered, it was punted to phase X, here's why.

2. **Have fixtures exercise the deferred feature when feasible.** If we're writing fixture markdown for an essay and we deferred KaTeX, still drop a math expression into one fixture so when KaTeX gets wired up later, the fixture is already there to verify. Same for spoiler blocks, video shortcodes, widget mounts, etc. The current page might render them as raw text or harmless placeholder, but the *content* is future-proofed.

**Why:** Deferred features fall off the radar when they vanish from the working doc. Fixtures that exercise deferred capability turn "this works" into a contract, not a hope — when the feature lands, you flip a renderer on and immediately know whether it worked. The user explicitly asked for both behaviors: "DO DOCUMENT THE FACT THAT WE DIDN'T IMPLEMENT THIS. And if possible create filler fixtures that test those features even if the page doesn't show it yet."

**How to apply:** Whenever a brainstorm or plan triages a feature list, produce two artifacts in parallel: the in-scope list AND an explicit deferred list with rationale and target phase. When designing fixtures/test data for a slice, deliberately include syntax/markup for deferred features so they round-trip the moment the renderer arrives. Treat fixture coverage of deferred features as part of the slice's deliverable, not a nice-to-have.
