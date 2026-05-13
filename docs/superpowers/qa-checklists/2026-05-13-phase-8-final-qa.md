# Phase 8 — final QA checklist (2026-05-13)

**Slice:** Phase 8 Slice 3 — final QA pass.
**Spec:** `docs/superpowers/specs/2026-05-13-phase-8-design.md` §4.
**Live URL during walkthrough:** `python3 -m http.server 8080 --directory public` from a fresh `hugo --minify && pagefind --site public/` build.

Mark each item ☑ (pass), ☒ (fail — capture finding inline + fix), or ⚠ (acceptable deferral — note why). Empty checkbox = not yet walked.

---

## 1. Keyboard nav

- [ ] **1.1** Tab order through homepage: hero → Currently widget → Research strip → Garden strip → Works strip → footer. No traps, no skipped interactive elements.
- [ ] **1.2** Filter chip strips on `/essays/`, `/garden/`, `/works/games/`, `/works/music/`, `/works/poetry/`, and all four `/library/<leaf>/` pages are arrow-key navigable per spec.
- [ ] **1.3** Filter-chip disclosure (the `<details>` containing secondary tag chips): arrow keys flow input → first chip → between visible chips (no wrap) → input again; Esc clears the search input.
- [ ] **1.4** Garden stacked-columns: Tab moves through column headers and tile links predictably; no traps inside a column.
- [ ] **1.5** Graph pages (`/garden/graph/`, `/research/graph/`, `/works/graph/`): keyboard users have a working sidebar/links fallback; the SVG graph itself doesn't trap or steal focus.
- [ ] **1.6** Theme toggle button + RSS link + search icon-button all reachable in tab order; each activates via Space or Enter.
- [ ] **1.7** Search modal: `/` opens (when focus is not in an `<input>` / `<textarea>` / `[contenteditable]`); modal traps focus; Tab cycles input → filter chips → results → kbd-hints footer → back to input; Esc closes; ↑/↓ navigate result rows; Enter opens; ⌘/Ctrl+Enter opens new tab.
- [ ] **1.8** Page-sidebar rail (≥1220 px) + mobile dots strip (<1220 px): anchor links activate with Enter; scrollspy correctly highlights the current section.
- [ ] **1.9** Essay post page: TOC links activate with Enter; sidenote markers reachable + activate; citation hover-card has a keyboard equivalent (focus the cite, the card shows).

## 2. Screen-reader walkthrough

SR of choice: **Orca** (Linux GTK SR), with NVDA-on-Windows as fallback. iOS VoiceOver covers the mobile audit.

Targets — read each page top to bottom, narrating along:

- [ ] **2.1** Homepage `/`
- [ ] **2.2** An essay post `/essays/example-essay-one/`
- [ ] **2.3** A garden note `/garden/emergence-vs-design/`
- [ ] **2.4** A research theme `/research/themes/memory-and-play/`
- [ ] **2.5** A research question `/research/questions/what-is-a-narrative-atom/`
- [ ] **2.6** A library leaf `/library/reading/`
- [ ] **2.7** A game page `/works/games/example-playable-full-release/`
- [ ] **2.8** Search modal (open via `/`, type a query, navigate results)

For each target verify:

- [ ] **2.9** Landmark structure: header / nav / main / footer announced.
- [ ] **2.10** Heading hierarchy: H1/H2/H3 read in document order.
- [ ] **2.11** Icon buttons (RSS, theme toggle, search) speak meaningful labels.
- [ ] **2.12** Status pills + growth-stage glyphs read text content (not colour-only).
- [ ] **2.13** Citation hover-cards have a keyboard-accessible alternative.
- [ ] **2.14** Sidenote markers announce as superscript references.
- [ ] **2.15** Graph pages announce as decorative (or have proper labels).

## 3. Colour-blindness simulation

Tool: Chrome / Edge DevTools → Rendering → Emulate vision deficiencies. Cycle through {protanopia, deuteranopia, tritanopia, achromatopsia}.

Pages checked:

- [ ] **3.1** Homepage `/` (Currently widget colour cues)
- [ ] **3.2** Research index `/research/` (status pills)
- [ ] **3.3** Library leaves — all four — status badges
- [ ] **3.4** Garden index `/garden/` — growth-stage glyphs + tag chips
- [ ] **3.5** One essay post — citation links + body type contrast

Under each deficiency mode, verify:

- [ ] **3.6** Status pills distinguishable via shape + label, not colour alone.
- [ ] **3.7** Growth stages still legible (the glyphs differ in shape, not just colour).
- [ ] **3.8** Filter-chip active state visibly different from inactive.
- [ ] **3.9** Search-modal `<mark>` highlights visible against snippet background.

## 4. Mobile audit

DevTools mobile mode for desktop browser checks; one or two pages on the user's actual phone for VoiceOver coverage.

Breakpoints to spot-check:

- [ ] **4.1** 360 px — small phone (iPhone SE / Galaxy A)
- [ ] **4.2** 414 px — large phone (iPhone Pro Max)
- [ ] **4.3** 768 px — tablet portrait
- [ ] **4.4** 960 px — half-screen 1080 p workspace (per memory feedback)
- [ ] **4.5** 1220 px — page sidebar rail → dots strip flip point

Items at each breakpoint:

- [ ] **4.6** Homepage hero stacks cleanly (image + lede + mark).
- [ ] **4.7** Currently widget rows wrap without overflow.
- [ ] **4.8** Research strip readable; cards don't truncate.
- [ ] **4.9** Garden strip readable; tiles don't overflow.
- [ ] **4.10** Page sidebar collapses to mobile dots strip below 1220 px.
- [ ] **4.11** Filter chip strips wrap without overflow; disclosure usable.
- [ ] **4.12** Search modal sized correctly on phone (~95 vw, fits within viewport).
- [ ] **4.13** Graph pages downgrade to standalone full-screen view; SVG canvas fills viewport.
- [ ] **4.14** Real device (user's phone): one essay + one garden note; check actual touch target sizes + scroll behaviour.

## 5. Performance — manual cross-check

The page-weight gate (Slice 2) is the primary automated check. This section adds a manual cross-check.

- [ ] **5.1** DevTools Network panel on cold-load of homepage: total transfer matches `check_page_weights.py` reported number ± a few KB (Google Fonts CDN adds external bytes not in our budget).
- [ ] **5.2** DevTools Network panel on cold-load of `/library/reading/` (heaviest non-graph page): total transfer within ~500 KB budget.
- [ ] **5.3** Cover images on `/library/*/` use `loading="lazy"` OR are small enough that eager-load is fine (current state — confirm or open follow-up).
- [ ] **5.4** Spot any low-hanging perf wins: font preload, `<link rel="preconnect">` for fonts.googleapis.com, etc. Document each as a separate item to fix in-slice or defer.

## 6. Summary

Filled in at end of walkthrough:

- Total items walked: __ / __
- ☑ pass: __
- ☒ fixed in-slice: __
- ⚠ deferred (with reason): __
- Follow-up specs opened: __

### Follow-ups

- ⚠ **RSS link UX** — clicking the header RSS icon navigates to the raw `.xml` feed file. Standard behavior; RSS-literate visitors are fine, but pretty-rendering via an XSL stylesheet is a future polish. Deferred (no spec opened yet); revisit if the audience grows.
- ⚠ **Garden path-log retrieval** — the consent banner asks users to persist a visited-notes list, but no UI surface reads it back. Spec stub filed at `docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md`. Pick up as a standalone post-Phase-8 polish slice (not Phase 3, not Phase 8).
- ⚠ **Mobile page-sidebar strip doesn't pin** (items 4.10 + 4.12 family) — at viewport widths < 1220 px the dots strip scrolls away with content instead of staying at viewport top. Reproduces on real phone too. Multiple in-session fixes failed; DOM/paint API confirms the element is at viewport top but it's not visible on screen — points to a compositing/render-tree divergence we couldn't isolate in this session. Spec stub filed at `docs/superpowers/specs/2026-05-13-mobile-page-sidebar-strip-bug-design.md`. Pick up with a fresh context.

---

*End of checklist.*
