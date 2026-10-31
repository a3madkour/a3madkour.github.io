# Authoring without Hugo keywords (stub)

**Status:** stub. Filed 2026-10-31 during the S1 essay dogfood. Not designed.

## Problem

Publishing a note writes Hugo/ox-hugo plumbing into the author's org source.
After `a3-publish-mark`, the first real essay (`~/org/essays/test-essay.org`)
read:

```org
#+date: 2026-10-31
#+filetags: :TODO:
#+HUGO_SUMMARY: Things happen
#+TITLE: My title is not for sale
#+HUGO_SECTION: essays
#+HUGO_PUBLISH: t
```

Other sections add `#+HUGO_CUSTOM_FRONT_MATTER: :key value` lines, and garden
library items carry `LIBRARY_*` drawer keys. The source of a piece of writing
should say what it is (its summary, whether it is published, where it goes),
not how one static-site generator spells that.

## Wanted

The author writes neutral, site-agnostic metadata. The pipeline translates it
into whatever ox-hugo and Hugo need, on its own export copy, never in the
source.

## Open questions (for the brainstorm)

- What the neutral spelling is: plain keywords (`#+summary:`, `#+publish:`,
  `#+section:`), a file-level property drawer, or one block.
- How custom front matter (status, weight, refs, …) is written without
  `HUGO_CUSTOM_FRONT_MATTER`.
- Migration: existing notes already carry `HUGO_*` keywords. Read both
  forever, or migrate once with a command?
- Whether `a3-publish-mark` / `a3-publish-status` should hide the keywords
  entirely (for example, a status line) rather than only rename them.
- Interaction with the section contract (`data/sections.json` `source` /
  `fill` hints), which currently names `#+filetags`, `#+title`, `#+date`
  and `LIBRARY_*` drawer keys.

## Constraints known now

- The privacy boundary stays: only what is marked publishes.
- ox-hugo still needs `HUGO_*` at export time. Translating on the export copy
  is the established pattern (`drop-title-heading`, the site-only copy for
  library items).
- Org's file-level property drawer must stay the first element
  (`reference_org_element_file_property_drawer_position`).

## Queue

Roadmap row added beside B1 and C (`2026-10-15-authoring-infra-roadmap.md`
§3). It touches every section, so it should be decided before the C
authoring guide is written.
