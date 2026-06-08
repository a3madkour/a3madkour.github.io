---
name: feedback-trigger-gated-make-fixture
description: "When a roadmap row is \"trigger-gated\" pending real-content evidence, build a fixture that exercises the trigger so the design decision has evidence — don't just wait or ship blind"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: df0f8dca-53dd-4978-ad74-36f105a7b286
---

When a roadmap (or any queue) row is marked "trigger-gated — wait for real essay / real content / real X," do NOT default to "wait." Build a fixture that exercises the trigger condition.

**Why:** "Wait for real content" was conservative — meant "we'll get better answers with evidence." But evidence is producible. A fixture that intentionally hits the trigger (H4-dense essay, an essay with cross-references that would drift, a long multi-section essay) lets us trial the proposed default *now* against something that looks like the eventual real case, instead of either (a) shipping a guess against nothing, or (b) leaving the row open indefinitely.

**How to apply:**
- When picking up a "trigger-gated" row, ask: "what content state would the trigger look like, and can I author a dummy fixture that puts the site into that state?"
- If yes — build the fixture FIRST, then implement the proposed default against it, then have me review the visual result before committing.
- Run every available test (lint pairs, unit tests, dev-server visual eyeball at half-screen 1080p per [[feedback-test-at-half-screen-1080p]], `tools/ci-local.sh`) and pass the result back for review per [[feedback-verify-before-merge]].
- Don't pre-clear the trigger and ship together — let me see the fixture-driven result, then we can decide to ship together OR iterate the default OR confirm "actually we DO need to wait."
- This combines well with [[feedback-deferred-features-stay-visible]] — fixtures that exercise the deferred shape so the round-trip lands clean when implementation arrives.

**Anti-pattern:** Defaulting to "trigger hasn't fired, skip the row" without checking whether a fixture could produce the trigger.

**Anti-pattern:** Implementing the proposed default + shipping in one shot without showing me the fixture-driven visual result first.

**Origin:** 2026-06-08 conversation about Tier 2.2 / 2.3 / 2.4 of the polish-and-bugfix roadmap. I had defaulted to listing them as "trigger-gated, wait." User correction: build the fixture, test against it, surface for review.
