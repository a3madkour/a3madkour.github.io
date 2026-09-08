---
name: feedback-mutation-test-every-guard
description: Break the thing and watch the test fail — a guard observed passing proves nothing
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ad301310-23dc-4009-b3e1-3375f3d4be7c
  modified: 2026-09-08T03:55:37.957Z
---

When I add a test, linter, or assertion that is meant to *prevent* a defect,
I verify it by reintroducing the defect and watching the guard fail. Then revert.
Observing a new guard pass proves only that the code is currently correct — it
says nothing about whether the guard would notice if it stopped being correct.

**Why:** in the 2026-09-07 recipe remediation, **six** tests passed while
testing nothing, and every one was written by someone trying to do the right
thing:

- An E2E for "the scaler doesn't rewrite quantities at rest" passed against the
  unfixed scaler, because every fixture quantity happened to round-trip through
  the formatter unchanged.
- An assertion that a search group "is visible" passed with its label deleted —
  `<h3>undefined</h3>` is still visible.
- `toHaveCount(0)` on children of a parent locator passed when the parent matched
  nothing (a bogus href).
- A heading-order loop passed on `[h1]` alone, because the loop body never ran.
- A pill-injection assertion would have passed with the pill's CSS deleted.
- A `role="status"` announcement "worked" while the region was absent from the
  accessibility tree at load — the DOM, text, role and toggling were all correct.

Each asserted something *adjacent* to the property it was meant to protect. That
is what happens when a test is written to describe a fix rather than to detect
its absence.

**How to apply:** after GREEN, mutate — delete the CSS rule, remove the array
entry, revert the template guard, restore the `hidden` attribute — rebuild, and
confirm the guard reports the specific failure. Paste that failure as evidence.
If the guard still passes, it is not a guard. Related: [[feedback_tone]] on
reporting findings measuredly.
