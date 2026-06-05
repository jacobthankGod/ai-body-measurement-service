# Absolute Fix Plan: Auth View Collision & Content Integrity

The "Obsidian & Mint" UI is perfect, but a CSS specificity conflict is causing the Sign-In and Sign-Up sections to "bleed" onto the bottom of the Home page.

## 1. Root Cause Diagnosis
*   **CSS Conflict**: The class `.auth-view` sets `display: flex`. Because it appears later in the stylesheet than `.view { display: none }`, the browser prioritizes the flex layout even when the view is supposed to be hidden.
*   **Result**: The Home page renders its footer, then immediately renders the Sign-In and Sign-Up forms underneath it.

## 2. The "Safe Design" Strategy
We will fix the functionality **without touching a single color, font, or spacing variable**.

### Step 1: Specificity Hardening
Update the CSS so that `display: flex` and `display: block` only apply when the `.active` class is present.
- Change `.view` to only handle animations.
- Create `.view:not(.active) { display: none !important; }`.

### Step 2: Content Parity Audit
Double-check every section provided in your list (4 examples, 3D zones, step 01-04) to ensure they are properly wrapped and visible.

---

## 3. Implementation Tasks

### [Frontend]
#### [index.html](file:///Users/mac/ai-body-scan-saas/index.html)
- [ ] Fix view visibility logic in the `<style>` block.
- [ ] Ensure all 20+ listed content sections are 100% visible in the `#viewHome` section.
- [ ] Maintain every Obsidian/Mint HEX code exactly as it is.

---

## 4. Verification Plan
1. **Visual Verification**: Scroll to the bottom of the Home page—the footer should be the final element.
2. **Navigation Verification**: Clicking "Sign In" should instantly swap the view so the Home page is hidden and the Login card is centered.

**Protocol**: Every change pushed to GitHub instantly for Render deployment.
