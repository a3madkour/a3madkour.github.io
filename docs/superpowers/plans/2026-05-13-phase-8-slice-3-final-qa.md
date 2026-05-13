# Phase 8 — Slice 3: Final QA pass implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Walk the assembled site through keyboard, screen reader, colour-blindness, and mobile audits; fix any issues that surface; close Phase 8.

**Architecture:** A single markdown checklist file (the deliverable) is committed first. The user walks it top-to-bottom in a real browser + assistive tech, marking each item ☑ / ☒ / ⚠ inline on the file. When an item fails, Claude dispatches a targeted fix and re-marks the item. At the end, the checklist is in the repo as a permanent record of what was audited.

**Tech Stack:** No new tech. Manual audit using existing browsers (Firefox + Chromium DevTools), existing assistive tech (Orca on Linux, VoiceOver on iOS), and existing CSS / Hugo template stack for any fixes.

**Parent spec:** `docs/superpowers/specs/2026-05-13-phase-8-design.md` §4 (Slice 3).

---

## Slicing rationale

Slice 3 is **inherently user-driven**. Claude cannot run a screen reader, open a browser, or use a CB simulator. The plan therefore breaks down into:

1. Draft the checklist (Claude — single commit, fully derived from spec §4).
2. Walk the checklist with the user (user-led, one section at a time; Claude waits for findings).
3. Fix what surfaces (Claude — one targeted fix per item, in-slice).
4. Update CLAUDE.md, merge.

The fix-on-find tasks are **shaped by the walkthrough**, so they're not enumerable in advance. The plan reserves a Task 3 placeholder with a generic structure that any number of fix commits will follow.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` | Create | The full checklist — keyboard / SR / CB / mobile / perf. Five top-level sections, each with concrete items. Marked inline ☑ / ☒ / ⚠ as the walkthrough proceeds. |
| `CLAUDE.md` | Modify | Add Slice 3 to Project status Shipped; mark Phase 8 complete. |
| Whatever needs fixing | Modify | Targeted CSS / template / aria-label tweaks discovered by the walkthrough. Plan a single commit per fix. |

`docs/superpowers/qa-checklists/` is a new directory — first checklist lives here. The path is from spec §4.1.

---

## Working Directory & Branch

Slice branch `slice/phase-8-qa` off `master`. Before Task 1:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git checkout master
git pull origin master
git checkout -b slice/phase-8-qa
```

---

### Task 1: Draft the QA checklist

**Files:**
- Create: `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md`

- [ ] **Step 1: Create slice branch (if not already done)**

```bash
git checkout master
git pull origin master
git checkout -b slice/phase-8-qa
```

- [ ] **Step 2: Create the checklist directory**

```bash
mkdir -p docs/superpowers/qa-checklists
```

- [ ] **Step 3: Write the checklist**

Create `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` with the content below. Mark format: each item is a `- [ ]` checkbox the user will tick ☑ (pass), ☒ (fail with action taken), or ⚠ (deferred / acceptable). Findings live inline directly under their item.

```markdown
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

---

*End of checklist.*
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md
git commit -m "qa: phase 8 final QA checklist (slice 3 deliverable)"
```

---

### Task 2: Walkthrough preparation — start a static server

This is a sanity step before the user walks the checklist. Confirms the audit target is reachable.

- [ ] **Step 1: Build site + Pagefind index locally**

```bash
rm -rf public/
hugo --minify
pagefind --site public/
```

Expected: both commands succeed; `public/pagefind/` exists.

- [ ] **Step 2: Run all the automated checks against the live `public/`**

```bash
python3 tools/check_smoke.py && \
python3 tools/check_page_weights.py && \
python3 tools/check_pagefind_meta.py && \
echo "--- AUTOMATED CHECKS PASS ---"
```

Expected: all pass.

- [ ] **Step 3: Start the server in the background**

```bash
cd public/
python3 -m http.server 8080 &
sleep 1
curl -sI http://localhost:8080/ | head -1
```

Expected: `HTTP/1.0 200 OK`.

- [ ] **Step 4: Tell the user the server is up**

Print: "Server up at http://localhost:8080/. Walk the checklist in `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` and edit it inline with ☑ / ☒ / ⚠ marks + findings. Report any failing items for fixes."

- [ ] **Step 5: NO commit — the server is ephemeral, the checklist already committed.**

---

### Task 3: Fix-on-find pass

This task is **shaped by the walkthrough**. There is no fixed scope. The pattern for each finding is:

1. User reports `☒ <item-number>: <finding>` or paste the modified checklist item.
2. Claude reads the relevant code (template / CSS / icon SVG / etc.).
3. Claude proposes a minimal fix.
4. User approves.
5. Claude makes the edit + commits with message `qa: fix <item-number> — <short description>`.
6. User re-tests the fixed item.
7. User updates the checklist mark from ☒ to ☑.

Each fix is its own commit, mirroring how Slice 1's spot-check surface bugs each got their own commit.

Class of issues we expect to find (rough — actual list comes from the walkthrough):

- Missing `aria-label` on an icon button
- Focus ring not visible on a specific element
- Filter chip arrow-key wrap behaviour off
- Modal focus trap leaks under some condition
- Colour-only status indicator (status badge that didn't survive deuteranopia)
- Mobile breakpoint that overflows at one of the 5 sample widths
- Page sidebar dot ↔ rail transition has a layout glitch
- Heavy image on one library leaf

For anything that needs more than a one-commit fix, open a follow-up spec under `docs/superpowers/specs/` and mark the item `⚠ deferred — see <spec-path>` in the checklist.

#### Generic fix workflow

For each surfacing finding:

- [ ] **Step 1: Read the relevant code path** (template / CSS / JS as appropriate).
- [ ] **Step 2: Propose the diff** (one Edit, scoped).
- [ ] **Step 3: User approves** the diff.
- [ ] **Step 4: Apply the Edit, rebuild + reindex if static-asset-relevant**:
  ```bash
  rm -rf public/
  hugo --minify
  pagefind --site public/
  ```
- [ ] **Step 5: User re-tests the affected page**.
- [ ] **Step 6: Commit**:
  ```bash
  git add <files>
  git commit -m "qa: fix <item-number> — <short description>"
  ```
- [ ] **Step 7: User updates the checklist** mark from ☒ to ☑ and continues.

---

### Task 4: Refresh CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add Phase 8 Slice 3 to the Shipped section**

Find the "Shipped — Phases 0–6 plus targeted polish:" section. Add this bullet after the CI gates trio entry:

```markdown
- **Final QA pass** (Phase 8 Slice 3): Walked the full site through keyboard nav, Orca screen-reader, CB simulation (4 deficiencies), and 5 mobile breakpoints. Checklist + findings committed to `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md`. Fixes from the walkthrough landed in-slice. Closes Phase 8.
```

- [ ] **Step 2: Update Project status section header**

Find: `## Project status (as of 2026-05-13)`. Verify the "Not started" list no longer mentions Phase 8 / final QA. If Phase 8 is the only item under "Not started", remove the section entirely or replace with: "All planned phases are complete. New work — content (Phase 3 elisp pipeline) or runtime features (item embeds, audio player, etc.) — is captured in the deferred-features table or specced separately."

Adjust prose to match the actual current state.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: phase 8 done"
```

---

### Task 5: Slice finishing — merge

- [ ] **Step 1: Verify working tree clean + every task committed**

```bash
git status
git log --oneline master..HEAD
```

Expected: working tree clean. At minimum 3 commits on the branch (checklist + CLAUDE.md + at least one fix). Could be more depending on what the walkthrough surfaced.

- [ ] **Step 2: Run all linters + the unit-test siblings one final time**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 tools/check_garden_fixtures.py && \
python3 tools/check_garden_links.py && \
python3 tools/check_filter_chips_config.py && \
python3 tools/check_research_fixtures.py && \
python3 tools/check_research_links.py && \
python3 tools/check_citations.py && \
python3 tools/check_works_fixtures.py && \
python3 tools/check_works_links.py && \
python3 tools/check_library_fixtures.py && \
python3 tools/check_library_links.py && \
python3 tools/check_library_covers.py && \
rm -rf public/ && hugo --minify && \
python3 tools/check_pagefind_meta.py && \
python3 tools/check_smoke.py && \
python3 tools/check_page_weights.py && \
echo "--- ALL LINTERS PASS ---"
```

Expected: ends with `--- ALL LINTERS PASS ---`.

If any linter fails (e.g., a CSS tweak broke contrast), fix and re-run before merging.

```bash
cd tools && for f in test_check_*.py; do
  result=$(python3 -m unittest "$f" 2>&1 | tail -1)
  echo "$f: $result"
done && cd ..
```

Expected: every `OK`.

- [ ] **Step 3: Stop the dev server if still running**

```bash
pkill -f "python3 -m http.server 8080" 2>/dev/null
sleep 0.5
lsof -i :8080 2>/dev/null | head -3 || echo "8080 free"
```

- [ ] **Step 4: Surface to user for merge authorization**

Per memory `feedback_verify_before_merge.md`: surface the merge ask + a quick summary.

Print:
- Total commit count: `git log --oneline master..HEAD | wc -l`
- File delta: `git diff master..HEAD --stat | tail -1`
- Brief narrative: "Slice adds a QA checklist + N fix commits from the walkthrough. No new tests, no new CI steps. Phase 8 done."

Wait for user approval.

- [ ] **Step 5: Merge + push**

```bash
git checkout master
git merge --no-ff slice/phase-8-qa -m "Merge slice/phase-8-qa: Final QA pass (Phase 8 Slice 3) — closes Phase 8"
git push origin master
git branch -d slice/phase-8-qa
git log --oneline -3
```

- [ ] **Step 6: Verify CI still passes**

Query the GitHub API for the new master run:

```bash
curl -s "https://api.github.com/repos/a3madkour/a3madkour.github.io/actions/runs?branch=master&per_page=1" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for run in data.get('workflow_runs', [])[:1]:
    print(f\"{run['head_sha'][:8]} {run['status']:12} {str(run['conclusion']):10} {run['display_title'][:60]}\")
"
```

If status is `in_progress`, wait and re-run periodically. Expected eventual: `completed success`.

- [ ] **Step 7: Save project memory entry**

Mirror the Slice 1 + Slice 2 memory file pattern at `~/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_phase_8_slice_3_final_qa.md`. Update `MEMORY.md` to add the new entry.

Mention what the walkthrough found + closes Phase 8.

---

## Self-Review Notes

Reviewed against spec §4 (Slice 3 — Final QA pass):

- ✅ §4.1 Deliverable — Task 1 creates the checklist file at the spec-required path.
- ✅ §4.2 Checklist categories — all 5 spec'd categories (keyboard nav / SR / CB / mobile / perf) present in the checklist; sub-items derived from the spec's bulleted lists.
- ✅ Fix-on-find pattern — Task 3 codifies the generic workflow.
- ✅ Slice-finishing — Task 5 mirrors Slices 1+2.

The plan deliberately does NOT enumerate fix tasks (Task 3 is a template). The actual fixes are user-driven and unknowable in advance.

Placeholder scan: no TBD / TODO. The Task 3 generic workflow is intentionally template-shaped because the inputs come from the walkthrough.

Type consistency: no types in this slice.

One forward-looking note: the QA checklist file lives in `docs/superpowers/qa-checklists/` — a new directory. Task 1 creates it. Future QA checklists for future phases land in the same directory.

---

*End of plan.*
