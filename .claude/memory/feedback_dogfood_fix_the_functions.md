---
name: feedback-dogfood-fix-the-functions
description: "In dogfood runs, every defect is fixed in the code that ran (mark/export/handlers/templates), never by hand-editing the content it produced"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 92b7d69f-8d8f-4829-9fe2-eb800703172b
  modified: 2026-10-22T02:55:55.720Z
---

When a dogfood publish produces wrong output, fix the function that produced it — `a3-publish-mark`, the export, the handler, the capture template — and have the user re-run it. Do not propose one-off content fixes ("add filetags to this note", "edit the :theme line") as the fix, and do not offer them as an option beside the code fix.

**Why:** 2026-10-21, S1 research: I offered "content fix" vs "mark fix" for a missing `tags` field and asked the user to hand-edit a wrong `:theme`. User: "fix the mark always it is on the code that ran not these one off fixes. This is a dogfood using the functions we built we fix the fucking functions." The point of the dogfood is to harden the pipeline; a hand-patched note hides the bug from the next author.

**How to apply:** For each friction row, name the function that produced the wrong output, fix it with a failing test first, then have the user re-run the real command. Fix all the layers that contributed (e.g. both the export and the capture template), and the minor issues too — don't queue cheap ones. See [[feedback_dont_defer_cheap_things]], [[project_authoring_infra_roadmap]].
