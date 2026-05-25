---
name: reference-dialog-close-inert-state
description: "`<dialog>.showModal()` makes the rest of the page inert; only `.close()` unwinds it. `removeAttribute('open')` first breaks teardown and leaves the page silently unclickable"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6cf4b615-49d6-4ba4-93a9-5aac82ce1434
---

When closing a `<dialog>` that was opened via `.showModal()`, **call `.close()` first**. Removing the `open` attribute first leaves the page in a stuck inert state where every click is silently swallowed.

```js
// Correct
function closeModal() {
  if (typeof modal.close === 'function' && modal.open) {
    modal.close();
  } else if (modal.hasAttribute('open')) {
    modal.removeAttribute('open');
  }
}

// Wrong (what I shipped, then had to fix)
function closeModal() {
  if (modal.hasAttribute('open')) modal.removeAttribute('open');
  if (typeof modal.close === 'function') modal.close();
}
```

**Why:** `.showModal()` adds the dialog to the browser's top layer AND marks the rest of the document inert (every element outside the dialog ignores clicks). Only `.close()` unwinds the inert state. If you call `removeAttribute('open')` first, the dialog visually closes, but `.close()` then early-returns because it thinks the dialog is already closed — and the inert flag never gets cleared. Every page click after that becomes a no-op.

**Symptom (what the user reported during citation-export walkthrough, 2026-05-14):** "When you click out of the modal, no other links work anymore." Modal closes, page looks normal, but every click below is dead.

When to apply: any `<dialog>` closed programmatically. Backdrop click, Esc key, close button — all paths through `closeModal()` need to call `.close()` first.

Related: [[project_citation_export_slice]].
