# Horizontal Spacing Fix Plan (Desktop + Mobile)

This plan fixes the "edge crowding" issue to restore the premium, balanced feel of the PrecisionFit 3D SaaS.

## 1. Root Cause Analysis
*   **Insufficient Side Padding**: The current `.container` and specific component wrappers (Hero CTA, Case Study Grid) lack enough horizontal padding to prevent content from nearly touching the viewport edges on medium-sized desktops and mobile devices.
*   **Full-Width Headers**: The header content currently sits at the very edges of the screen, which breaks the vertical alignment with the centered content below.

## 2. Technical Refinement Strategy
I will implement a "Safe-Side" margin system without redesigning any UI elements.

### Step 1: Container Hardening
*   Update `.container` to include a fixed percentage-based padding `padding: 0 5%;` combined with a `max-width: 1100px`.
*   This ensures that as the screen narrows, the content always stays at least 5% away from the edge.

### Step 2: Component-Specific Padding
*   **Header**: Move navigation and logo inside a centered `container` wrapper with identical side-padding to match the body.
*   **Hero CTA Card**: Enforce `width: 100%` and `max-width: 1000px` within a padded parent container.
*   **Grid Layouts**: Add `padding-left` and `padding-right` to split-content blocks (Platform, Case Studies, Benefits) to ensure cards don't "clip" the viewport edge.

### Step 3: Responsive Spacing
*   Mobile (max-width 800px): Increase side padding to `24px` to ensure text never touches the glass of the smartphone screen.

## 3. Implementation Rules
*   **Strict No-Touch**: Do not change HEX colors, Font sizes, or Section ordering.
*   **Alignment Only**: Focus purely on the left/right "breathing room."

---

## 4. Verification Plan
1. **Viewport Stress Test**: Resize browser from 1920px down to 320px—verify that a consistent "white space" (black space in our case) gutter remains on both sides of every single card and text block.

**Protocol**: Push update to github after every edit.
