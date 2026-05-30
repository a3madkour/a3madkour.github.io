---
name: lhci-google-fonts-flakiness
description: "Render-blocking third-party CSS (fonts.googleapis.com) makes LHCI desktop perf flake: identical HTML/CSS/JS bundles, but Google Fonts TTFB swings from ~200ms to ~3000ms across CI runs, dropping perf scores from 1.00 to ~0.60. Fix: self-host woff2 files in static/fonts/, add @font-face to main.css §3, remove the <link> + preconnect lines from head.html. With font-display: swap and same-origin fetches, perf is deterministic ≥0.95 across all pages."
metadata:
  node_type: memory
  type: reference
---

## Symptom

3 deploy runs in a row at different commits, all failing the LHCI desktop assertion `categories.performance >= 0.9` — but each on a **different URL** (`/research/` 0.60, `/garden/` 0.87, `/garden/graph/` 0.64). Different page each time, same root cause.

## Diagnosis

HTML / CSS / JS bundle sizes were byte-identical between the last passing run and the failing runs. The only delta: render-blocking time on `https://fonts.googleapis.com/css2?...` jumped from ~227ms (passing run) to ~2946ms (failing run). FCP went from 0.7s to 3.4s. With `font-display: swap`, the font woff2 files themselves don't block paint — but the *CSS request that declares the @font-face* does, because it's served with `<link rel="stylesheet">`.

Smaller pages (like `/garden/graph/`, mostly chrome + a JS-rendered SVG) magnify the impact because there's not much else competing for the FCP timeline.

## Fix (shipped 2026-05-30)

1. Download 16 woff2 files from Google Fonts' CDN (latin + latin-ext subsets, all weights we use) into `static/fonts/`.
2. Add 16 `@font-face` declarations to `assets/css/main.css` §3 Typography, each pointing at `/fonts/<filename>.woff2` and declaring `font-display: swap` + the same `unicode-range` Google Fonts uses (so per-subset gated downloads still work).
3. Remove the `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?...">` + 2 `<link rel="preconnect">` lines from `layouts/partials/head.html`.

Result: same-origin font CSS (inside the already-fingerprinted main.min.css), zero third-party network dependency at render time, deterministic FCP.

## Don't reintroduce

The `fonts.googleapis.com` `<link>` was historical convenience. The cost was:
- LHCI perf flakiness (this memo).
- Privacy: every page load round-trips visitor info to Google.
- Subject to third-party-cookies LHCI audit (a sibling Best Practices score regression).

If you ever need a new weight or face, download the woff2 file into `static/fonts/`, add an `@font-face` block to `assets/css/main.css` §3, and run `tools/ci-local.sh` to confirm.

## Tradeoffs

- **Repo size**: +595 KB for 16 woff2 files. Reviewed and accepted.
- **Subset coverage**: latin + latin-ext only. Author content is English-primary; if you ever publish Cyrillic / Greek / Vietnamese content, the browser will fall through the font stack rather than render a tofu — which is what we want.
- **Cache hits**: Google Fonts CDN had warm cross-site caching (mostly mythical post-Chrome 86, but a few hits). Self-hosted means every visitor cold-loads the fonts on first visit. For a low-traffic personal site, this is a non-issue.

## Cross-references

- The Hugo bump (0.148.0 → 0.162.1) that *coincided* with the failure was a red herring — bundle sizes were byte-identical. The flakiness was already latent; the bump just put three consecutive runs through a slow-network window.
- Originally surfaced by [[b2-complete]]'s post-ship deploy failures (`4fe4870`, `6e5a746`, `e4cb4d0` — three runs in a row).
