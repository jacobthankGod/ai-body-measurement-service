# Final UX Hardening Plan: Navigation Fix & Premium Polish

This plan addresses the non-functional navigation buttons and applies the requested high-end visual refinements.

## 1. Root Cause Analysis (Navigation Failure)
*   **Hash Inconsistency**: Some buttons are using `href="#signup"` while the routing logic is expecting specific `id` based triggers.
*   **Event Conflict**: The "Nuclear Reset" event delegation might be catching the click but not correctly updating the DOM state because of the hardened CSS visibility rules (`display: none !important`).
*   **DOMContentLoaded vs Load**: The routing engine might be firing before all views are properly registered in the DOM.

## 2. Visual Refinements
*   **Hero Container**: Increase `height` from 700px to 850px for maximum impact.
*   **Animation Removal**: Delete the `float` keyframes and animation properties from the hero image to achieve a "Stable-Luxury" look.
*   **CTA Border**: Add a `1px solid var(--Mint)` border to the `.hero-cta-card` without any `box-shadow` glow, creating a sharp, crisp, premium definition.

## 3. The "Absolute Fix" Strategy

### Step 1: Re-engineered Routing
*   Create a explicit `showView(viewId)` function.
*   The `hashchange` listener will serve as the primary source of truth.
*   Manually invoke the router on script boot.

### Step 2: Visual Implementation
*   Update `.hero-visual` height.
*   Update `.hero-cta-card` CSS with the new Obsidian background and Mint border.

---

## 4. Verification Plan
1. **Direct URL Test**: Manually visit `url/#signin` to ensure it works.
2. **Button Reliability**: Verify that clicking "Get Access" in the header vs the Hero CTA both trigger the same dedicated page.

**Protocol**: Push update to github after every edit.
