---
name: Hugo js.Build can't code-split a single entry
description: Setting splitting:true + format:esm on a single js.Build entry silently inlines dynamic imports — esbuild needs outdir mode, Hugo uses outfile. Use multi-entry instead.
type: reference
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**The trap:** Hugo's `js.Build` runs esbuild with `outfile` (set by `targetPath` or default). esbuild's code splitting requires `outdir` mode. So passing `splitting: true` + `format: "esm"` produces no warning, no error, and no chunks — `import('./foo.js')` is just inlined into the entry bundle. The bundle size doesn't change.

**Verified:** minimal Hugo site (one entry, one dynamic import, splitting:true, format:esm) emits a single file with `Promise.resolve().then(() => init_big())` and the inlined body. Hugo v0.161.1+extended.

**The workaround (used in this site):** multi-entry. Call `js.Build` once per section in `scripts.html` with conditional `<script>` tags by `.Section`. Each call is independent — no shared chunks, no code splitting per se, but you get per-section payloads. `filter-chips.js` gets duplicated across entry-essay + entry-garden (~8 KB cost), which is far cheaper than the alternative (d3 on every page).

**See:** `layouts/partials/scripts.html` for the pattern; CLAUDE.md "JS pipeline" section for the documented rationale.

**When to revisit:** if Hugo gains true `outdir`-mode build support, or if `js.Build` exposes a way to capture multiple output Resources, single-entry splitting becomes possible. Until then, multi-entry is the only working path.
