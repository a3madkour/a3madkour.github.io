---
name: tier-1-5-1-8-1-9-complete
description: "Tier 1.5/1.8/1.9 chunk — shipped 2026-06-07. 1.5: library handler swapped to last-modified-cascade helper (dotfiles 0cb4414). 1.8: verified org-roam-db-sync gate was already added retroactively (no code). 1.9: fixed alt=\"file:NAME\" by stripping the prefix from synthesized link text in rewrite-link (dotfiles 350a711). Suite 609 → 611 ert green."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Three Tier 1 rows closed: 1.5 + 1.9 fixed in dotfiles, 1.8 verified already closed.

## 1.5 — library handler upgraded to cascade

Library was the last per-section handler still using a 2-step `or` (drawer → git-mtime) for `last_modified`. When a row had no `:LAST_MODIFIED:` drawer AND the source file wasn't git-tracked, the `or` chain returned nil and the `(when lm …)` guard skipped emit → row landed without `:last_modified:` → site linter (which requires the field) rejected the YAML.

Swap calls `a3madkour-pub-frontmatter/last-modified-cascade` (the helper B.3 shipped + wired into garden/essays/research). Library rows have no per-heading `#+HUGO_LASTMOD:` equivalent so `:keyword` stays unset; the cascade still always returns a YYYY-MM-DD string, so `:last_modified` is now unconditionally emitted.

**Test:** `normalize-last-modified-cascade-fallthrough` — stubs `git-mtime-of-file` → nil + `filesystem-mtime-of-file` → sentinel; asserts row carries the fs-mtime value (proves the cascade walks past the empty git-mtime instead of stopping). Existing drawer-wins + git-mtime-fallback tests still green.

**Commit:** dotfiles `0cb4414`.

## 1.8 — already closed (verified)

`a3-pub.sh --check-orphans` (and other publish flows) chains through `(begin-publish)` which calls `(org-roam-db-sync)`. The roadmap row said this raised on machines without `~/org-roam/`.

`a3madkour-publish.el:317-319` already has the gate:
```elisp
(when (and (boundp 'org-roam-directory)
           (file-directory-p org-roam-directory))
  (org-roam-db-sync))
```

Comment marks it "A.1.d known limitation" — the gate was added retroactively, but the memory + roadmap weren't updated. Verified by reading current code; no test gap (no straightforward way to stub `boundp` without a fragile test). Marked ✓ in roadmap with the file:line citation.

## 1.9 — alt text retains `file:` prefix

`[[file:diagram.svg]]` (no display text) produced `<img alt="file:diagram.svg" />`.

**Root cause:** `--parse-org-link's` `[[path]]` branch synthesizes text from path verbatim → text comes back with `file:` prefix intact, even though `--strip-file-prefix-if-asset` strips it from path. Downstream in `rewrite-asset-link`, the `(equal text path)` "no display text" guard then fails (text has prefix, path doesn't) → display defaults to the prefixed text → alt lands with `file:` baked in.

**Fix location: `rewrite-link` (rewrite.el), NOT rewrite-asset-link (assets.el).** Roadmap suggested fixing in assets.el; correct site is one layer up at the path/text computation boundary. When parsed text equals raw-path (the parse-time "no display text" signal), substitute text with the file:-stripped path so the downstream `(equal text path)` check fires correctly. Equality-guarded — won't clobber an author-given literal display string of `file:foo`.

**Test:** `rewrite-link-file-prefix-no-display-strips-from-alt` — exercises the full `rewrite-link` chain with `[[file:diagram.svg]]`, asserts emitted HTML contains `alt="diagram.svg"` and NOT `alt="file:`.

**Commit:** dotfiles `350a711`.

## Suite

ert 609 → 611 (one new test each for 1.5 and 1.9, 0 unexpected). Three commits across two dotfiles modules (library + rewrite). No site code changed.

## Cross-references

- Roadmap: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 1
- Closure ancestor for 1.5: B.3 cascade work (no separate memory)
- Closure ancestor for 1.8: A.1.d (retro-gate added post-ship)
- Discovery context for 1.9: [[d2-figref-bundled-fix-complete]] (the figref fix that surfaced the residual alt-text issue on example-multi)
- Remaining Tier 1: 1.7 (D.1 multi-word quote workaround — deferred), 1.10 (Step B failed-delete variant — just filed)
