---
name: design-batch-no-plan-until-implement
description: "When brainstorming multiple features in one session, write specs for all but only draft implementation plans when the user is ready to implement a specific slice"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2586b61b-7278-423f-b331-1090fe330889
---

When the user brings a batch of features to design in one session, design and commit specs for each one, but **draft an implementation plan only when explicitly asked**. Plans are per-slice, drafted right before implementation begins. Specs accumulate; plans don't.

**Why:** 2026-05-13 session designed 4 features (citation export, time-synced poetry, streams section, multi-target export). After Feature 1's spec, I offered to invoke writing-plans (per the brainstorming skill's terminal-state contract). User said yes for Feature 1. After Feature 1's plan, user explicitly said: "this was just the design phase for this feature, let's continue with the design of the other three then commit that to the spec and project context then we [will] go and implement them at each slice." So for Features 2/3/4 I wrote specs only — no plans. Specs end with a note: "Implementation plan drafted only when the slice is actually scheduled."

**How to apply:** When the user signals a multi-feature batch (3+ features queued in one session, or "let's design X, Y, Z first"), default to spec-only. Surface the plan-drafting decision per slice as a separate question when implementation time comes. The brainstorming skill's "invoke writing-plans" terminal step is right for single-feature flows; multi-feature batches deviate from it intentionally.

After the batch: update CLAUDE.md with a "Designed but not yet implemented" table linking the specs (and any plans that exist). Then push.

Related: [[remaining-work-phase-order]] — within the batch, feature phase fits should be surfaced in each spec's §phase-placement so sequencing is obvious when the user picks the next slice.
