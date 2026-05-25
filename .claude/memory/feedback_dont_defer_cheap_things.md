---
name: Don't defer cheap things — include them when implementation cost is low
description: User prefers shipping the full feature set when each item is cheap; only defer when an item carries real implementation cost or unresolved design questions
type: feedback
originSessionId: 624875d4-e750-49c5-9e96-c5bab4010528
---
When triaging a feature list, I should NOT default to "defer the marginal one for cleanliness" if implementing it is cheap. The user prefers including everything that's cheap to add, even if it isn't immediately useful, over leaving items off for tidiness.

The bar for deferring is **real implementation cost or an unresolved design question** — not "this isn't useful yet" or "the data set is too small to show its value right now."

**Why:** The user explicitly said: "do all of them, I don't see why we need to be cautious with what we leave out here if it is simple to implement." Leaving cheap items out creates churn — they come back as a question later, get re-litigated, get added in a follow-up that could have been part of the original. Better to land the complete shape once.

**How to apply:**
- For low-cost items in a feature triage, the default is "include." Do not propose deferring on grounds like "single-value chip looks cosmetically odd today" or "no fixture exercises this yet" — those are not real costs.
- Reserve "defer" recommendations for items that involve: nontrivial JS (KaTeX, d3-force, custom widgets), unresolved design conventions (per-page bundle JS conventions in spec §15), large dependencies, or implementation work that genuinely belongs to a different slice.
- When unsure whether something is cheap, ask — don't unilaterally defer.
- Pair this with the prior memory about documenting deferrals: when something IS deferred, it must still be documented and exercised by fixtures where possible.
