---
name: reference-hugo-css-var-zgotmplz
description: Go html/template sanitizes an interpolated CSS custom-property name to var(ZgotmplZ) — colorless
metadata: 
  node_type: memory
  type: reference
  originSessionId: a7a980ab-0626-4eae-ab5f-45cfb26e61b9
---

In a Hugo template, `style="background:var({{ .var }})"` where `.var` is a CSS
custom-property name (e.g. `--color-burgundy`) renders as `var(ZgotmplZ)` —
Go's `html/template` contextual autoescaper does not treat an interpolated token
inside a `style` CSS context as a safe identifier, so the swatch/element ends up
**colorless**. The build does NOT error; it silently produces `ZgotmplZ`.

**Detection:** `grep -ro ZgotmplZ public | wc -l` on the built site (a grep-only
linter check like `check_smoke.py` can gate this).

**Fixes (prefer the data-attr one — it's this repo's established precedent):**
- `data-swatch="0|1|2"` (or `data-theme-color`) attribute + static CSS rules
  `.x[data-swatch="0"] { background: var(--color-burgundy) }`. No interpolation
  into a CSS context at all. Matches §31's existing `data-theme-color` pattern.
- Or `{{ printf "var(%s)" .var | safeCSS }}` (verified to render correctly).

**Not affected:** JS-set styles (`el.style.background = …` / `.innerHTML` written
by browser JS) — the Go sanitizer is server-template-only, so garden-graph.js's
runtime-injected swatches keep inline style legitimately.

Surfaced in the graph-view chrome-consistency slice — see
[[project_graph_view_chrome_consistency_slice]]; the bug was in plan-verbatim
markup and caught by code review, not the build.
