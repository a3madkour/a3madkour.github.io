---
name: reference-duplicate-id-anchor-race
description: "An `<a href=\"#foo\">` with `preventDefault` can still race-process focus to the first id=foo element in the DOM. Use `<button>` for actions, not anchored links"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6cf4b615-49d6-4ba4-93a9-5aac82ce1434
---

When the DOM has multiple elements with the same `id`, an `<a href="#that-id">` click can race-process URL-hash + focus to the FIRST match, even if a JS handler calls `preventDefault()`. The fix is to use `<button type="button">` for click-driven actions instead.

**Concrete example (2026-05-14 citation-export slice):** Stacked garden columns each had a `<section id="cite-this">` static-fallback. Clicking "Cite this note" in column 2 — an `<a class="cite-cta" href="#cite-this">` — should have opened the modal scoped to column 2. JS preventDefault was called immediately on click. But the page focus jumped back to the first column anyway (`getElementById('cite-this')` semantics: first match wins). The browser race-processed the URL fragment update + focus before preventDefault could land.

**Fix:** swap the `<a>` for `<button type="button">`. Buttons have no anchor-navigation default action, so there's nothing for the browser to race-process. The JS handler (delegated `closest('.cite-cta')` on document) doesn't care about tag.

```hugo
<!-- Wrong (raced with preventDefault) -->
<a class="cite-cta" href="#cite-this">Cite this note</a>

<!-- Correct -->
<button class="cite-cta" type="button" data-action="open-cite-modal">Cite this note</button>
```

When to apply: any click-driven UI action where preventDefault is the only thing preventing the browser's default link behavior — especially if the DOM might contain multiple elements with the same id (stacked / repeated sections, syndicated partials, JS-loaded fragments). If the action isn't actual navigation, use `<button>`.

When NOT to apply: actual navigation (links to other pages, in-page anchors used as fallback for no-JS users) — use `<a>` with a unique target.

Related: [[project_citation_export_slice]] · [[feedback_no_arrow_prefix_on_links]].
