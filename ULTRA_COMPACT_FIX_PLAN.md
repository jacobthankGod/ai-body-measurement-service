# Ultra-Compact Layout Implementation Plan

This plan fixes the "too big" content and "screen-edge touching" issues by aligning all elements (Header, Marketing Sections, CTA Card) to a strict 1000px centered grid.

## 1. Grid Re-Architecture
*   **Header**: Currently 100% width. Will be changed to contain a centered 1000px wrapper.
*   **Container**: Hardened to `max-width: 1000px` with `width: 90%` to ensure a safety margin on all screen sizes.
*   **Hero Visual**: The 100vw image container stays as is for impact, but its content (Headline, Sub, CTA) will be constrained to the 1000px axis.

## 2. Component Refinement
*   **Platform Section**: Reduce the grid gap from 64px to 40px to fit comfortably within 1000px.
*   **Case Studies**: Ensure the 4-column grid doesn't feel cramped by optimizing card padding.
*   **Benefits & Steps**: Enforce the 1000px limit on all horizontal rows.

## 3. Navigation Integrity
*   Maintain the hash-based routing (`#signin`, `#signup`).
*   Ensure the `btnNavSignIn` and `btnNavSignUp` are correctly centered within the new header container.

---

## 4. Implementation Steps
1.  Update `.container` CSS.
2.  Refactor `<header>` to include a centered container.
3.  Audit all `<section>` tags to ensure they use `.container` correctly.
4.  Verify on multiple viewport widths.

**Protocol**: Push update to github after every edit.
