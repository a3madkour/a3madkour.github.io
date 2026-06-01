---
name: reference-finish-publish-snapshot-lifecycle
description: "a3madkour-pub--manifest-snapshot is set at the top of begin-publish and CLEARED at the bottom of finish-publish. Any code that runs AFTER finish-publish (e.g. F's tail-called emit-yaml) sees nil and must fall back to a fresh manifest read off disk."
metadata:
  node_type: memory
  type: reference
---

`a3madkour-publish.el:172` declares `a3madkour-pub--manifest-snapshot` with a docstring stating the lifecycle: "Set at the top of `begin-publish` (next to the metadata-cache reset); cleared at the bottom of `finish-publish` (after Step C)."

The clear happens AFTER step C (write manifest to disk), so the on-disk yaml is fully updated by that point.

## When this bites

Any code that runs as a tail call from a top-level publish command (`a3-publish-living`, `a3-publish-deliberate`) AFTER `finish-publish` returns. The snapshot is gone; reading the defvar yields nil.

**Confirmed bite:** F Task 13 calls `emit-yaml` after finish-publish; `lookup-notes-ref` read the snapshot, got nil, silently returned no `notes_ref`. Spot-checked broken before fix.

## Why the clear exists

Per the docstring: "`a3madkour-pub/diff-published-set` reads from this snapshot instead of re-reading `data/url-history.yaml` off disk, so that `record-publish` calls made mid-publish (by B's per-note publishers) do not poison the slug-shift detection in `diff-published-set`."

So the snapshot is a session-start snapshot used for slug-shift detection during the publish. Once finish-publish completes, the snapshot has served its purpose and gets cleared so any *later* code doesn't accidentally read stale pre-publish state.

## How to read manifest after finish-publish

Use `a3madkour-pub-history/read-manifest-snapshot-or-disk` (B.0 helper) — it returns the snapshot when non-nil, else reads from disk. After finish-publish's clear, this transparently falls back to disk.

Alternative inline pattern:
```elisp
(or (and (boundp 'a3madkour-pub--manifest-snapshot)
         a3madkour-pub--manifest-snapshot)
    (a3madkour-pub-history/read-manifest))
```

F uses this pattern in `lookup-notes-ref`.

## Design hint

If you're adding a new tail-call after finish-publish that needs the manifest, prefer reading via the snapshot-or-disk helper. Don't assume the defvar will be live.
