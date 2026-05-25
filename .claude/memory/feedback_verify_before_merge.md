---
name: Always offer dev server spot-check before merging a slice
description: User consistently wants to visually verify a slice in the browser before authorizing merge + push. Pattern observed across all 4 slices in the 2026-05-11 session.
type: feedback
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
After implementing a slice and before merging to master, **offer the dev server first and wait for visual sign-off** — don't proceed straight from "implementation complete" to "merge and push" unless the user explicitly says to.

**Why:** Observed across all 4 slices on 2026-05-11 (Phase 4 follow-ups, Phase 4 stylistic cleanup M1–M10, About bio half, Research surface Slice 1). The user said "run the server let me verify then merge and push" or equivalent in three of the four; the one time I went straight to merge was after they pre-authorized it ("merge and push"). Build-clean + CI-green isn't a substitute — runtime visual issues (e.g. the `hugo --minify` + dev-server interaction that broke CSS MIME on the research-surface slice, or the consent banner's wrong button colour from Phase 4) only surface in the browser.

**How to apply:**
- After completing all tasks + final CI sweep, present the finishing-a-development-branch options but **also** include the dev-server URL and a 4–6 line "what to eyeball" checklist (the specific behaviours / variants this slice introduced). Mention dark mode if there's anything theme-sensitive.
- Don't restart the dev server if it's already serving correctly — just point the user at the relevant URLs.
- If the user pre-authorizes with a single message that includes both "verify" and "merge" wording, treat that as serial: verify first, then merge once they signal satisfaction (typically a second message saying "merge and push" or "looks good").
- If you ran `hugo --minify` during the CI sweep, the dev server is now serving stale minified+fingerprinted output from public/. Clean + restart before pointing the user at it — see `reference_hugo_dev_server_gotcha.md`.
