---
name: file-for-another-slice-means-stub
description: "When user says \"file for another slice\", they want a minimal stub queued for later brainstorming — NOT an interactive brainstorm now"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6cf4b615-49d6-4ba4-93a9-5aac82ce1434
---

When the user says "file [this] for another slice" or "file a slice for X", they want me to queue X as a future slice with a minimal stub, NOT brainstorm it interactively right now.

**Why:** Mid-session 2026-05-14 I had just finished a citation-export design iteration, and the user asked me to "file for another slice brainstorm a redesign of the library page". I read this as "start the brainstorming skill now" and dove into clarifying questions. They cancelled the tool use and corrected: they wanted the slice queued for a later session, not brainstormed now.

**How to apply:** "File a slice for X" → write a short stub spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (or similar) marked "Stub — needs brainstorming" at the top, capture whatever motivation/constraint the user has already mentioned, and add a row to the CLAUDE.md "Designed but not yet implemented" table (or a parallel "Queued for brainstorming" list). Do NOT invoke `superpowers:brainstorming` unless the user explicitly says "let's brainstorm X now" or similar. The verb "file" signals queueing; the verb "brainstorm" alone (without "file") signals to start the brainstorm immediately.

Related: [[feedback_design_batch_no_plan_until_implement]] — same family of "queue work, don't execute until the right time".
