# Layout Polish & Navigation Hardening Plan
**Goal**: Solve navigation reliability, maximize visual contrast, and correct section orientation.

---

## 1. Aesthetic Hardening (Pure Black)
*   **Background**: Change `--Obsidian` from `#0A0A0A` to `#000000`.
*   **Contrast**: Ensure all glass-card borders and mint accents remain high-contrast against pure black.

## 2. Hero Headline Refactor (One-Line)
*   **Headline**: "AI-powered body measuring for faster, better fit."
*   **Style**: Remove `<br>`, reduce `font-size` slightly (using `clamp()`), and set `color: var(--Mint)`.

## 3. Section Re-Orientation (The Swap)
*   **Cross-Border Impact**:
    *   Change grid order to: `[Image Card] [Content Block]`.
    *   Grid ratio: `1.5fr 1fr`.
    *   Standardize image card sizing and internal padding.

## 4. Component Standardization (Biometric Identity)
*   **Image Card**: Add a high-fidelity image, remove all internal text, and match the "Status Quo" dimensions perfectly.

## 5. Navigation Absolute Fix
*   **The Audit**: The current listener relies solely on `hashchange`. If a user clicks a button while already on that view (e.g. refreshing a failed reveal), nothing happens.
*   **The Fix**:
    1.  Explicitly call `handleRoute()` inside the click listener for all primary navigation buttons.
    2.  Ensure `preventDefault()` is handled correctly for `<a>` tags.
    3.  Verify button IDs in the header match the script.

---

**Protocol**: Every update pushed to GitHub immediately.
