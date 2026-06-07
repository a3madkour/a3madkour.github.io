---
name: tier-1-7-complete
description: "Tier 1.7 (D.1 attr_shortcode multi-word titles double-escape) — shipped 2026-06-07 in dotfiles 31f9570. Post-export markdown sanitizer in export-file strips `key=\"&quot;V&quot;\"` → `key=\"V\"` at the ox-hugo emit boundary. Suite 611 → 615 (+4 named tests). Author-side workaround in [[feedback-d1-attr-shortcode-unquoted-titles]] is no longer needed; multi-word `:title \"Multi word\"` now round-trips correctly."
metadata: 
  node_type: memory
  type: project
  originSessionId: 5b5bbb90-9abc-47bc-b613-67a9ddf91b2a
---

**Shipped 2026-06-07.** Bug 1.7 from `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`. The longstanding "unquoted single-word title" workaround captured in [[feedback-d1-attr-shortcode-unquoted-titles]] is no longer needed.

## Root cause

ox-hugo's special-block emit reads `#+attr_shortcode: :title "Multi word"` via `org-export-read-attribute :attr_shortcode`. The org attr parser preserves surrounding quote characters in the value verbatim — `:title "X"` parses to `(:title "\"X\"")`. ox-hugo then emits the paired shortcode as `{{< theorem title="&quot;X&quot;" id="..." >}}`. Hugo HTML-escapes the `&quot;` entities again at render time, so the rendered page lands with `&amp;quot;X&amp;quot;` inside `<span class="block-title">`.

Pre-fix, authors worked around it by keeping `:title` to unquoted single-word values only. No multi-word title was authored in real content; the bug was theoretical until a future essay needed one.

## Fix

Post-export markdown sanitizer in `a3madkour-pub-export--strip-stray-attr-quotes` — runs in `export-file` between raw-output capture and the frontmatter/body split, scoped to the body. Regex `\\([a-zA-Z_-]+\\)="&quot;\\(.*?\\)&quot;"` → `\\1="\\2"` collapses any attribute whose value is itself wrapped in `&quot;...&quot;`.

The pattern is bounded by construction: `&quot;` doesn't appear in YAML frontmatter and prose-level mentions don't sit inside `key="..."` shortcode-attribute syntax. So the regex is safe even buffer-wide (test `strip-stray-attr-quotes-leaves-prose-quot` pins this).

## Alternative considered

Pre-export buffer rewrite in `multi-filter.el` (matching the existing `--translate-vocab` pattern that runs for `latex`/`pandoc` backends). Rejected: the org attr parser needs the quotes to group multi-word values — stripping them upstream would break value parsing on multi-word titles before ox-hugo even sees them. Post-export at the emit boundary is the cleanest hook.

## Tests

4 new ert in `a3madkour-publish-export-test.el` — all unit-test the helper directly (no need to invoke ox-hugo):
- `strip-stray-attr-quotes-basic` — canonical bug pattern.
- `strip-stray-attr-quotes-noop-on-clean` — already-clean shortcodes pass through.
- `strip-stray-attr-quotes-multiple` — multiple shortcodes in one body all get sanitized.
- `strip-stray-attr-quotes-leaves-prose-quot` — prose-level `&quot;` mentions are untouched.

Suite 611 → 615, 0 unexpected.

## Author-side workaround status

[[feedback-d1-attr-shortcode-unquoted-titles]] is now historical. Multi-word `:title "Multi word"` works correctly post-fix. The memory entry stays in place as a record of the bug's prior behavior; future-me can ignore the "use single unquoted words" guidance.

## Commits

Dotfiles only:
- `31f9570` fix(export): strip stray &quot; from shortcode attrs — closes bug 1.7

Site repo: roadmap row marked ✓ + this memory file + MEMORY.md index entry.

## Tier 1 status after this

9 of 10 closed: 1.1 ✓, 1.2 ✓, 1.3 ✓, 1.4 ✓, 1.5 ✓, 1.6 ✓, 1.7 ✓, 1.8 ✓, 1.9 ✓. Remaining: 1.10 (Step B failed-delete variant, filed this session). After 1.10, Tier 1 is fully closed and Tier 2 (UX polish — anchor affordance + D.1 cross-ref auto-formatting) becomes the next session's queue head.

## Cross-references

- Roadmap: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` Tier 1
- Source memory: [[feedback-d1-attr-shortcode-unquoted-titles]]
- Companion ert location: `a3madkour-publish-export-test.el` (B.1 module)
