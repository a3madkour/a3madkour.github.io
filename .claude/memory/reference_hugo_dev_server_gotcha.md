---
name: Don't run `hugo --minify` alongside an active `hugo server`
description: A production build populates public/ + resources/ that the running dev server then serves, with broken behaviour (MIME mismatch on fingerprinted CSS that the dev-mode HTML doesn't reference).
type: reference
originSessionId: cfd5e26b-590f-4577-aed6-8c8b9f757692
---
**The trap:** if `hugo server` is running and you also run `hugo --minify` for a CI sweep, the production build writes minified + fingerprinted output to `public/` and seeds `resources/`. The dev server then mixes states: it serves HTML from memory (referencing un-fingerprinted `/css/main.css`) but the production-mode `head.html` branch (`if hugo.IsProduction`) emits the fingerprinted URL anyway. Browser requests `/css/main.css` (or a stale fingerprinted hash that no longer exists), gets a 404 served as `text/plain`, and rejects it as CSS due to MIME mismatch. The page renders unstyled.

**Verified 2026-05-11** during the Research surface (Slice 1) verification cycle: user reported "main.css is blocked due to MIME type 'text/plain' mismatch". Reproduced by curling `/css/main.css` → 404 + `text/plain`. Root cause was an earlier `rm -rf public resources && hugo --minify` for the CI sweep with the dev server still running.

**Fix:**
```
pkill -f "hugo server"
rm -rf public resources
hugo server --buildDrafts --port 1313 &
```
Returns to in-memory serving with `Content-Type: text/css` on `/css/main.css`.

**Avoiding the trap:**
- Don't run `hugo --minify` while the dev server is up — use the dev server's own build output for CI-equivalent checks (`grep -oE 'src=[^ >]+\.js' public/...` etc.).
- If you must run a production build for verification (e.g. checking bundle isolation or production-only fingerprinting behaviour), kill the dev server first, run the build, then restart the dev server after `rm -rf public resources`.
- In plans, schedule production-build verification *after* visual verification, not before, so the dev server isn't tainted when the user goes to spot-check.

**See:** the Research surface (Slice 1) memo (`project_research_surface_slice_1.md`) which captures the specific incident.
