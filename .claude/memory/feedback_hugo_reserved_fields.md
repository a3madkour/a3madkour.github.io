---
name: hugo-reserves-both-type-and-kind-as-frontmatter-field-names
description: "When designing per-fixture enums on a Hugo site, avoid `type:` AND `kind:` — both collide with built-in page attributes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ec310218-1708-418e-b53d-565a7a9baa4e
---

Hugo reserves `type` (layout discriminator — used by the works `cascade.type` pattern to route descendants to `layouts/works-games/single.html` etc.) AND `kind` (the `.Kind` page method returning "page" / "section" / "home" / "term" / "taxonomy"). Setting either on a descendant page in frontmatter creates breakage:

- `type:` set on a descendant overrides the cascade per Hugo's cascade docs ("cascading fields override the same fields in lower-level pages, unless they're explicitly set on the lower-level page"). Layout lookup fails.
- `kind:` shadows the `.Kind` method in template access patterns (`.Params.kind` accesses the frontmatter value, but `.Kind` returns the page kind; mixing them is confusing and template-engine behavior varies).

**Why:** Both collisions were discovered empirically during Phase 6 works-section implementation. First `type:` broke (rename to `kind:` was made in [[project_works_section_slice]] Task 4), then `kind:` also broke the build (rename to `game_kind:` was made in Task 11). Two collisions in one slice burned ~30 minutes of rework.

**How to apply:** When designing a new fixture frontmatter contract that needs an enum or category field, **start with a domain-prefixed name** (`game_kind`, `note_flavor`, `music_format` etc.) — don't reach for generic words like `type` or `kind`. Reserve those generic names for actual Hugo behaviour. The filter chip dim's machine key (the URL/chip-key) can stay short (`kind`, `flavor`); only the frontmatter field name and the `.Params.X` template accessor need to be unambiguous.
