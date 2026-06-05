# Expert UI/UX Audit: Figma-Style Sizing & Spacing
**Status**: Critical Refinement Needed for "Pixel-Perfection"

While the "Gallery" scale provides high impact, a true "Figma-Expert" design requires more sophisticated typographic rhythm and spatial consistency.

## 1. Audit Findings

### A. Typographic Collision (High Severity)
*   **The Problem**: 72px titles in a 1000px container create awkward 2-word line breaks on many laptop screens.
*   **The Fix**: Implement **Fluid Typography** using `clamp()` (e.g., 48px to 72px). This ensures the "Expert" scale remains without breaking the layout.

### B. Spatial Inconsistency (Medium Severity)
*   **The Problem**: Mixing various padding values (40px, 60px, 80px) creates a jittery visual flow.
*   **The Fix**: Implement a strict **8pt Spacing Grid**. All margins, gaps, and paddings will be multiples of 8 (16, 32, 48, 64, 80, 120, 160).

### C. Visual Balance (Low Severity)
*   **The Problem**: 240px vertical padding on every section can feel "disconnected" for related content.
*   **The Fix**: Use **Rhythmic Vertical Spacing**.
    *   Primary Sections: 200px
    *   Sub-sections/Related content: 120px

---

## 2. Implementation Plan: "The Figma Refactor"

### Phase 1: Global Grid Hardening
*   Define a strict 12-column CSS grid concept within the 1000px container.
*   Standardize all horizontal gutters to **32px**.

### Phase 2: High-Fidelity Component Resizing
*   **Buttons**: Hardened to **56px** (Standard) and **72px** (Hero) with exact pixel-heights.
*   **Cards**: Standardize all card padding to **48px** for better internal breathing room without shrinking content.
*   **Images**: Implement consistent aspect-ratios (16:9 or 4:3) for all marketing tiles.

### Phase 3: Fluid Responsiveness
*   Refactor all `px` sizes for text into `rem` or `clamp()` for smoother transitions between 1440px and 375px viewports.

---

## 3. Strict Rules
*   **NO COLOR CHANGES**: #0A0A0A and #57D7C0 are permanent.
*   **NO ORDER CHANGES**: The marketing flow is preserved.

**Protocol**: Every change pushed to GitHub instantly.
