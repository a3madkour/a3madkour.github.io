---
name: publish-living-fixture-sweep
description: "publish-living's orphan sweep is MANIFEST-based, not disk-vs-source. It removes URLs that are in the manifest but not in the new publish run. Hand-authored Hugo fixtures (not in the manifest) are never touched. Also: failed delete-bundle silently logs and doesn't retry."
metadata:
  node_type: reference
  type: reference
---

**Rule:** `a3-pub.sh --publish-living`'s orphan-removal step (Step A of `a3madkour-pub/finish-publish` in `a3madkour-publish-unpublish.el`) operates on the URL-history MANIFEST, not on the on-disk `content/` tree.

**Mechanic:** `diff-published-set` compares the manifest's `state ∈ {live, draft}` entries against the new publish run's accumulator (id → url). Entries in manifest but missing from the new run → `:removed`. For each, finish-publish calls `unpublish-delete-bundle` then `record-publish` with `'removed`.

**Why:** This means orphan-removal is bounded by what the publisher has ever published before. Hand-authored Hugo content (the fixtures the site started with at `content/garden/emergence-vs-design/`, `content/garden/invisible-cities/`, etc.) was never recorded by the publisher and therefore is never in the manifest. publish-living leaves it alone.

**How to apply:**
- When starting real-corpus publishing for the first time in a section, the existing fixture bundles will STAY on disk until you manually `rm -rf` them. The publisher will not sync them away. Document this for the author before they expect "publish-living sweeps fixtures."
- If the spec or design doc says "publish-living does a sync," interpret that as "syncs the publisher's known set" — not "diffs source vs. disk and removes anything unaccounted for." The disk-vs-source model would be more invasive and was deliberately not adopted (would risk blowing away unrelated content).

## Secondary finding (worth filing as A.1.d follow-up)

**`unpublish-delete-bundle` has no retry on failure.** If the path computation is wrong (e.g., `a3madkour-pub-site-content-dir` defaults to the wrong machine — see [[b1-complete]] round 2), the helper logs `"already absent (stale manifest?)"` via `message`, returns nil, and finish-publish continues. `record-publish` then marks the manifest entry as `state: removed` — so on the next publish-living, `diff-published-set` no longer sees this id as live, hence no re-attempt. The orphan bundle persists on disk forever.

The site-content-dir defcustom that caused this is now fixed (dotfiles `0825853`, derives from site-data-dir). But the no-retry behavior is a latent gap: ANY failure mode in delete-bundle (permissions, lock, etc.) will silently leave orphans. Worth a small follow-up that at least WARNs loudly + ideally resets the manifest entry so a retry can succeed.
