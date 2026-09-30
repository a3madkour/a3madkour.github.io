---
name: reference_pipeline_masks_exit_status
description: "A shell pipeline returns the exit status of its LAST command, so `git pull | tail -1 && git merge` runs the merge even when the pull failed. Cost a false 'verified against upstream' claim."
metadata:
  node_type: memory
  type: reference
---

**The bug.** A pipeline's exit status is that of its **last** command. So:

```bash
git pull --ff-only 2>&1 | tail -1 && git merge --no-ff feature -F msg.txt
```

runs the merge **even when the pull fails**, because `tail` exits 0 regardless. The pull's
own output scrolls past in the same stream, so `Updating <old>..<new>` can be read as
success when it is actually the prelude to an abort.

**How it bit (2026-09-30, [[project_works_handlers_slice]]).** The pull refused because the
incoming commit edited `config.org`, which had ~103 uncommitted lines. The merge then ran on
the un-updated `main`. The result: `main` diverged from `origin/main` (29 ahead, 1 behind),
and the session reported "the merge combined my branch with the upstream commit and the
merged result is green" — **which was false**. The suite was green, but on a tree without
that commit.

**This project already had the same class of bug and fixed it.** P5.5 of the publish-pipeline
audit split an assignment from its `export` because the `export` builtin masks the exit
status of the command whose output it assigns, silently swallowing a `|| exit 1`. Same
lesson, different builtin.

**How to avoid it.**
- Do not pipe a command whose exit status you are about to branch on. Run it bare, then
  inspect its output separately.
- `set -o pipefail` in scripts.
- When verifying a merge, **assert the ancestry** rather than trusting the command chain:
  `git merge-base --is-ancestor <expected-upstream> HEAD`. That single check would have
  caught this immediately, and `git log --first-parent` shows the same thing at a glance.
