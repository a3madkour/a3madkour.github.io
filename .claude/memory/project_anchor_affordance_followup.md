---
name: anchor-affordance-followup
description: "Queued brainstorm — deep-link affordance for anchored content (semantic blocks, headings, garden notes, etc.). D.1 shipped a `[id]:hover::after { content: \" #\"; }` rule but it looks bad and doesn't actually solve the underlying UX problem (visual hint only; not clickable; invisible on touch). Future slice brainstorms a real solution."
metadata:
  node_type: memory
  type: project
---

**Status:** queued for brainstorming. No spec, no plan yet.

## The problem

When a page element has a stable anchor URL — a theorem block with `id="thm-ivt"`, an essay heading with a custom-id, a garden note section — a reader has no obvious way to:

1. **Know that this element is deep-linkable.** Without a visual cue, the URL fragment is invisible.
2. **Easily grab the deep-link URL.** Today, getting `/essays/example-five/#thm-ivt` requires right-clicking a same-page cross-ref (if one exists) and using "copy link address", OR scrolling to the element and copying from the browser address bar after it updates with the hash. Both are friction.

Both halves of the problem matter independently: the discoverability half (a reader who doesn't know the convention won't try), and the action half (even a reader who does know has to do extra work).

## What D.1 shipped (not the answer)

D.1's CSS §47 has:

```css
.block-strong[id]:hover::after,
.block-soft[id]:hover::after,
.block-proof[id]:hover::after {
  content: " #";
  color: var(--color-ink-soft);
  font-weight: 400;
  margin-left: 0.4em;
}
```

Issues with this approach:

1. **`::after` content can't be clicked.** Browsers don't dispatch click events on pseudo-element generated content. So the `#` is a *hint* with no action attached — readers who hover and reach for it can't actually grab the URL.
2. **Hover-only is invisible on touch devices.** Mobile readers (a non-trivial fraction of essay traffic per LHCI mobile gates) get no affordance at all.
3. **Visually awkward.** The `#` floats outside the block on the right edge with no enclosing styling; reads as decorative noise rather than functional UI.
4. **Selector scope is narrow.** Only matches the three new D.1 block-tier classes. Headings (H2/H3), garden note sections, research surfaces — none of these get the affordance, but they have exactly the same problem.

The pattern was added optimistically during D.1's brainstorm as a "we'll generalize it later" placeholder. Code-review caught the misleading "§11 heading anchor" comment but didn't push back on the core mechanism. Visual review pushed back.

## Existing conventions to consider (not yet decided)

- **GitHub READMEs / MDN / Docusaurus / dev.to**: hover surfaces a real `<a class="anchor" href="#id">#</a>` inside the heading. Click copies-to-clipboard or scrolls into view. JS-light variants exist (pure CSS + native anchor) and JS-heavy variants (clipboard API + tooltip).
- **Tufte CSS sidenote pattern (this site already uses it)**: marker + aside, but for asides, not deep-link UI.
- **Some academic theme conventions**: a leading `§` glyph next to the block-header, clickable.
- **Address-bar-update-on-scroll**: scroll-spy that rewrites `location.hash` as the reader passes anchored elements; pure browser-side, no UI clutter. Smart but invisible.

## Scope when this slice opens

Single source of truth across:

- Semantic blocks (D.1's 12 kinds where `:id` is set).
- Essay headings (H2/H3 — most essays don't set custom-ids, but the slice could include opt-in via `:CUSTOM_ID:` per the existing org convention).
- Garden note section headers.
- Possibly research themes/questions, library shelves, works tiles where they have stable IDs.

Single CSS rule + matching template logic + one shared partial. Replace `[id]:hover::after` in §47.

## Pre-brainstorm reads

1. CLAUDE.md "Tokens" + the existing CSS palette to keep the affordance on-brand.
2. [[d1-complete]] §47 — the current (not-the-answer) implementation.
3. The existing heading-anchor handling in any layout that touches `:CUSTOM_ID:` (the B.1.1 id-link rewriter is the closest piece of infrastructure).
4. LHCI mobile + half-screen-1080p constraints (per [[feedback-test-at-half-screen-1080p]]) — touch + narrow-viewport affordance matters.

## When to schedule

After D.2 (multi-target export). D.2 is the next big slice; this affordance is small surface, slot it in when there's appetite — could be its own polish slice or fold into a "site UX polish" batch alongside other deferrals.
