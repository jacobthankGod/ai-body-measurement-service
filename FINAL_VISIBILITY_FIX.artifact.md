# Final Visibility & Component Parity Hardening Plan
**Status**: Critical Fix for Content Reveal & UI Consistency

The "invisible content" issue is a common pitfall when combining `IntersectionObserver` with `display: none` view-switching. I am implementing a robust, expert-grade fix.

## 1. The Animation Fix (No more "Guessing")
*   **The Problem**: Elements in a `display: none` view have zero intersection. When the view switches to `display: block`, the observer doesn't always "wake up" immediately.
*   **The Expert Solution**:
    1.  Add a `forcedReveal()` function that runs every time `handleRoute()` completes.
    2.  Add a CSS fallback: `@media (prefers-reduced-motion: reduce)` to ensure accessibility.
    3.  Update the observer to `threshold: 0.05` for faster triggers.

## 2. Component Parity (The "Status Quo" Standard)
*   **Hero Section**:
    *   Headline: "AI-powered body measuring for faster, better fit."
    *   Description: "Get accurate body measurements with just a phone. [br][br] Built for tailors, fashion businesses, and people who need their measurements fast."
*   **Image Cards**:
    *   Every section (Platform, Distance, Identity) will use the **12px padding / 24px radius** style.
    *   Remove all text overlays from Distance and Identity cards.
    *   Dimensions will be uniform 1:1 or 4:3 across the 1.5fr grid.

## 3. Accuracy Hardening
*   **Economics**: Re-verify the **$0.50 per scan** cost.
*   **Workflow**: Enforce the **Customer vs Tailor** role separation with line breaks after step headers.

---

## 4. Implementation Steps
1.  **Refactor** the JS `handleRoute` to include an animation trigger.
2.  **Harden** the `.glass-card.image-card` CSS globally.
3.  **Update** HTML copy for the Hero.
4.  **Verify** across all routes.

**Protocol**: Push to GitHub immediately.
