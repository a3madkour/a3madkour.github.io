---
name: Use only obvious filler text in fixtures, never AI-authored prose
description: When creating placeholder/fixture content for layouts, use lorem ipsum or "Example 1/Example 2" — never write my own example prose based on project context
type: feedback
originSessionId: 624875d4-e750-49c5-9e96-c5bab4010528
---
When the user asks for fixture/placeholder/dummy content (e.g., test essays for layout design, sample posts, demo content), I must use clearly-marked filler text only:

- **Lorem ipsum** is fine
- **"Example 1", "Example 2", "Title goes here"** is fine
- Anything that is unmistakably placeholder is fine

What I must NOT do: invent my own example prose drawn from project context, even if it would feel "more realistic" or "show off the typography better." That kind of synthesized content can read as authored writing and risks blurring the line between fixture and real work.

**Why:** This site has a hard constraint against AI-generated text (CLAUDE.md, spec §1). The user wants fixtures to be obviously dummy so there is zero risk of placeholder prose ever being mistaken for, or sneaking into, the real published content. They explicitly called out: "do not author your own example based on context."

**How to apply:** Whenever generating fixture content for a layout, mockup, demo, or test page on this site (and likely others — treat as the default unless the user says otherwise), use lorem ipsum or numbered "Example N" stubs. Vary tile sizes / titles / metadata to exercise the layout, but the body text stays as filler. Never write paragraphs of "as if" content.
