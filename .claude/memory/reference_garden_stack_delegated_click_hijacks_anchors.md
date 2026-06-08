---
name: garden-stack-delegated-click-hijacks-anchors
description: "`garden-stack.js` has a delegated click handler on `<main data-stack-root>` that hijacks any internal `/garden/<slug>/` `<a>` click (including fragment-bearing same-page links) for column-append navigation. Any new interactive affordance with an `<a href=…>` inside a garden column must defend against this — either by being excluded by `isInternalGardenLink` (the 2026-06-07 fix adds a `u.hash + same-pathname` skip) or by calling `e.stopPropagation()` in its own handler before the click bubbles to `<main>`."
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc32fd0c-3d65-4233-88cb-6c9b4bf8e30a
---

## The hijack

`assets/js/garden-stack.js` attaches a delegated click handler at `init()` time:

```js
root.addEventListener('click', (e) => {
  const a = e.target.closest('a');
  const slug = isInternalGardenLink(a);
  if (!slug) return;
  e.preventDefault();
  appendColumn(slug);
});
```

`isInternalGardenLink` matches any `<a>` whose resolved URL has pathname `/garden/<slug>/`. **Crucially: it resolves the `href` attribute against `window.location.href` first** — so `<a href="#foo">` inside a garden note resolves to the current note's URL and gets classified as "internal garden navigation". The handler then calls `appendColumn(slug)` → `focusColumn(slug)` → `scrollIntoView` + title focus, scrolling the column.

This affected the Tier 2.1 anchor-link affordance (the §-glyph next to garden body headings): the §'s `<a href="#first-listen">` was matched, click bubbled to `<main>`, garden-stack scrolled, anchor-link's own handler then ran and copied to clipboard. Result: clipboard worked AND page scrolled to top.

## The fix (2026-06-07, commit `5e27a86`)

`isInternalGardenLink` now skips fragment-bearing same-page URLs:

```js
if (u.hash && u.pathname === window.location.pathname) return null;
```

So any `<a>` with a `#fragment` whose target is the current page is treated as an intra-note jump, not navigation. Cross-note links (with or without fragments) are unchanged.

## How to apply

- **Adding a new interactive `<a>` to garden columns:** if the `<a>`'s `href` is a same-page fragment (`#…`), no defense needed — the 2026-06-07 fix handles it. If the `<a>` points cross-note, your click handler runs AFTER `appendColumn` already did its work; if that's wrong, call `e.stopPropagation()` in your handler to prevent garden-stack from seeing the click.
- **Adding a new delegated handler to garden columns:** attach it INSIDE the stack root (so it fires during bubbling BEFORE the root's handler) and call `e.stopPropagation()` if you handled the click. Or attach it to `<main>` (which is the stack root's parent) and rely on the root's handler running first.
- **Discovering similar bugs:** if a click inside a garden column produces unexpected scrolling or column behavior, check `garden-stack.js`'s click handler first — it's the most aggressive delegated handler in the codebase.

## Related

- [[anchor-affordance-complete]] — the Tier 2.1 slice that surfaced this interaction.
- `assets/js/anchor-link.js` — the affordance whose click handler runs alongside garden-stack.
- `layouts/_default/baseof.html` — emits the `<main data-pagefind-body>` wrapper that the garden-stack root lives inside.
