---
name: next-slice
description: "Polish + bugfix tier roadmap shipped 2026-06-07 in two site specs. Active queue is now polish/bugfix Tier 1 (correctness bugs). Sub-project E (explorables) deferred to Tier 8 per author's 2026-06-07 reorder. Source-of-truth files in site repo."
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c08431e-013f-458c-a665-ac6e0c33baf8
---

## Source of truth (read these first, they're durable across CLAUDE.md churn)

- **Active tier roadmap**: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` (site repo). 8 tiers, items with severity/source/entry points, reorder decision log.
- **Long-horizon deferrals**: `docs/superpowers/specs/2026-06-07-deferred-features-registry.md` (site repo). Trigger-gated capabilities; promotion path from registry → roadmap when triggers fire.

## Next session

**Tier 1 — Correctness bugs.** Recommended starting point: bug **1.1 — `finish-publish` advances past failed `delete-bundle`** (data-integrity, highest severity). Then 1.2 (`--rewrite-file-link` parity, architectural). Smaller bugs (1.3-1.8) batch when convenient.

Each Tier 1 fix gets its own commit with a production-mirroring failing test FIRST, then the fix. Use `superpowers:systematic-debugging`. Stage dotfiles by exact path per the bystander rule.

## Tier-at-a-glance

1. **Correctness bugs** (8 items, this session's TODO)
2. **UX polish** (3 items — anchor affordance is the big one, needs brainstorm)
3. **Phase 8 QA walkthrough** (5 categories — human-driven, author owns)
4. **Hygiene / cleanup** (6 small items — batch session)
5. **Tooling gaps** (`a3-unpublish-deliberate` + publish-author helpers)
6. **Small new features** (About Now widget)
7. **Deferred CI ergonomics** (LHCI 4.2 / 4.3 — trigger-gated)
8. **Large new features** — sub-project E (explorables), org→synced-poetry export

See the roadmap spec for the full breakdown.

## State of the world at session start (next session)

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- `master` after this session's roadmap commit (TBD on push). Pre-this-session: `41c7a37`.
- `content/essays/example-multi/index.md` bundle contains `<img src="diagram-1.svg" />` (Task 9 verified) — figref bug closed.

**Dotfiles (`~/dotfiles/`):**
- `main` at `99f0240` (async-pub cleanup; pushed to origin).
- Pre-existing dirty tracked files (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`, `config.org`, `config.el`) — author's in-progress local work, NEVER commit.
- Stale `.elc` files frequently shadow source. Recommend `find ~/dotfiles/emacs-configs/custom/lisp -name '*.elc' -delete` before next interactive Emacs session.
- `org-math-lint` venv at `~/org/notes/tools/org-math-lint/.venv/` — recreate if math validation gate is needed. See [[reference-org-math-lint-venv-platform]].

**Personal notes (`~/org/`):**
- `essays/example-multi.org` — has `:ID: 394db383-e408-44a2-a347-20ad7a54c5e7` drawer.
- `essays/assets/394db383-e408-44a2-a347-20ad7a54c5e7/diagram-1.svg` — moved here from sibling location.
- `essays/diagram-1.svg` — gone (moved into per-essay assets dir).

## Related memories

- [[project-figref-inert-missing-complete]] — figref bug shipped 2026-06-07
- [[project-async-pub-cleanup-complete]] — async-pub cleanup + mode-line hygiene shipped 2026-06-07
- [[project-async-publish-complete]] — async publish pipeline shipped 2026-06-07
- [[project-d2-complete]] — D.2 multi-target export shipped 2026-06-04
- [[project-phase-3-decomposition]] — parent decomposition; sub-project E queued for Tier 8
