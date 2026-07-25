---
name: reference_css_refs_leading_interpolation
description: "check_css_refs.py resolves interpolation PREFIXES, not leading `${x}-suffix` — allowlist dynamically-built class bases"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a4b4e454-fc0d-4ae8-8172-2c36574d9f94
---

`tools/check_css_refs.py` resolves template-interpolation **prefixes** (Hugo `{{ }}`, printf, JS `${}` where the literal part comes first, e.g. `garden-${x}`). It does **not** resolve a **leading** interpolation like `` `${classPrefix}-graph-node` `` — the static-resolvable part is a suffix (`-graph-node`), and the scanner keys on prefixes, so the class reads as orphaned.

When a class base is constructed with the variable first (common after a "parameterize by prefix" refactor), the linter false-flags it. Fix = add the concrete class name(s) to `tools/css-refs-allowlist.txt` with a comment pointing at where it's emitted. Confirm the class is genuinely rendered first (an E2E/DOM assertion), since allowlisting removes the guard.

Seen in R5.2 graph-core (`assets/js/graph-core.js` emits `` `${adapter.classPrefix}-graph-node` ``): allowlisted `research-graph-node` + `works-graph-node`; `garden-graph-node` didn't need it because `garden-graph.js` still queries `.garden-graph-node` literally. See [[audit-r5-2-complete]].
