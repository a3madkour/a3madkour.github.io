---
name: Verify WCAG contrast ratios numerically
description: Compute or look up WCAG contrast ratios programmatically rather than estimating them visually
type: feedback
originSessionId: a0b3cf95-38e8-4e66-b016-c766ae853ea8
---
When proposing a color palette and citing WCAG contrast ratios, compute them precisely (WCAG sRGB → relative luminance → ratio) rather than estimating from how things look. The user caught me citing steel `#2f5a7a` on cool stone `#eeeeea` as 7.4:1 (AAA) when actual is 6.3:1 (AA only).

**Why:** Accessibility commitments need to be verifiable. Citing inflated ratios undermines trust in the design spec and risks shipping non-compliant UI. The CI gate will catch shipped regressions, but the design conversation should already use accurate numbers.

**How to apply:** Whenever picking palette accents and quoting AA/AAA compliance, run the actual WCAG calculation (R, G, B → linearize → 0.2126·Rₗ + 0.7152·Gₗ + 0.0722·Bₗ → ratio = (L₁ + 0.05)/(L₂ + 0.05)). For brainstorm screens this can be a quick mental calc with a calculator or one-line python in Bash. For design specs, attach a small script that computes and asserts ratios.
