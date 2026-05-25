---
name: site-repo-staged-mess
description: "RESOLVED 2026-05-23. Site-repo had 505 staged-but-not-committed mutations from a prior session's wide `git rm --cached`; unstaging revealed only 3 files differed from HEAD (all legitimate work). Repo is now clean."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7ef3bb18-9acf-451e-8f17-f5a28329110c
---

**State (2026-05-23, resolved):** Site repo `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io` had a noisy staged state at session start; cleanup ran successfully and only 3 working-tree changes remained, all legitimate. **Not committed** (per session policy + user's explicit "DO NOT COMMIT" directive this session) — author commits separately.

## Resolution path

1. **Confirmed root cause**: prior session ran wide `git rm --cached` (didn't show in reflog because index-only mutations aren't HEAD events). The `MM .gitignore` shown at session start was misread or self-resolved during the unstage — working tree always matched HEAD.
2. **Ran `git restore --staged .`** — non-destructive global unstage.
3. **Result**: 505 mutations → **3 modified files**. The other 502 entries were all bystanders whose working-tree content was byte-identical to HEAD — innocent victims of the over-broad index purge.

## The 3 legitimate working-tree changes (all KEEP, all uncommitted)

| File | Diff | Why keep |
|---|---|---|
| `CLAUDE.md` | 2 lines | A.1.b completion language ("109 ert tests; A.1.c is next") from when A.1.b shipped — see [[a1b-complete]] |
| `docs/superpowers/plans/2026-05-20-phase-3-a1-b-link-rewriter.md` | 15 lines | Task 12 in-flight algorithm correction (Hugo `sanitizeAnchorNameWithHook` vs Goldmark `auto_heading_id`) from the A.1.b session |
| `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` | 13 lines | 2026-05-23 amendments resolving A.1.b carry-forwards #2 (HTML escaping contract) and #3 (Task 17 narrowing + Task 12 source-of-truth) — see [[next-slice]] |

## Lessons / cross-references

- "Session policy: no commits between sessions" + a session that DOES make index-only changes (like `git rm --cached`) = staged state accumulates silently across many sessions. Future analogous mess: try `git restore --staged .` first as a quick non-destructive test — most of the noise may evaporate.
- Reflog doesn't capture index mutations (`git add`, `git rm --cached`, etc.). For diagnosing staged-state weirdness, examine `git status` + `git diff --cached` directly, not the reflog.
- See [[next-slice]] for current A.1.c entry point + the 3 carry-forward statuses.
