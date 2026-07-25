---
name: reference_org_element_file_property_drawer_position
description: "org-element only tags a file-level :PROPERTIES: drawer as property-drawer when it's the buffer's literal first element"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 97b081c2-f09d-4384-bd76-a05215511347
---

**`org-element` only parses a file-level `:PROPERTIES:...:END:` block as element type `property-drawer` when it is the buffer's LITERAL first element.** If any keyword (`#+TITLE:`, `#+HUGO_SUMMARY:`, …) precedes it — the normal, natural authoring order — the same block parses as a generic `drawer` (name "PROPERTIES") whose contents are paragraph/plain-text, and `(org-element-map ast 'property-drawer …)` / `node-property` extraction returns **nil**, silently dropping every property.

Verified empirically (Emacs 30.2): `#+TITLE:`-then-drawer → no `property-drawer`; drawer-first or drawer-under-a-headline → `property-drawer` found.

**Robust extraction that ignores position** (used by the recipe handler's `--drawer-alist`): interpret the whole AST back to text and regex-scan the block —
```elisp
(let ((text (substring-no-properties (org-element-interpret-data ast))))
  (when (string-match ":PROPERTIES:\\(\\(?:.\\|\n\\)*?\\):END:" text)
    ;; then parse each `:KEY: value' line
    ))
```
`substring-no-properties` is required: without it `match-string` returns propertized values carrying a large `:parent` backreference graph (memory hygiene; note `equal` on strings already ignores text properties and `format "%s"` strips them, so it's not load-bearing for correctness, just hygiene).

Bit the recipe Slice 2 pipeline ([[project_recipe_slice_2_complete]]) — the spec's own keywords-first authoring example silently lost servings/times/etc. until this fix.
