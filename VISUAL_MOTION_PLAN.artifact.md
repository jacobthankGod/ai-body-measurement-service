# Visual Consistency & Motion Hardening Plan
**Architect**: UI/UX Expert
**Goal**: Enforce absolute component parity across all sections and implement modern cinematic entrance animations.

---

## 1. Brand Integrity (Hero Section)
*   **Headline**: "AI-powered body measuring for faster, better fit."
*   **Description**: "Get accurate body measurements with just a phone. <br><br> Built for tailors, fashion businesses, and people who need their measurements fast."

## 2. Component Standardization (The "Status Quo" Blueprint)
Every core section (Platform, Distance, Identity) will now use the **Exact Same Image Card Spec**:
*   **Dimensions**: Match the aspect ratio and size of the "Status Quo" card.
*   **Styling**: 12px internal padding, 24px border-radius.
*   **Interaction**: Mint border hover highlight.
*   **Cleanliness**: Remove all overlaid text from within the cards.

## 3. Cinematic Motion (Scroll-Triggered)
*   **Trigger**: Intersection Observer API.
*   **Animation**: "Spring Slide-Up" (Opacity 0 -> 1, TranslateY 40px -> 0).
*   **Target**: All sections *except* the Hero.

---

## 4. Implementation Steps
1.  **Refactor** Hero copy.
2.  **Harmonize** CSS for all `.glass-card` elements to use the Status Quo hover logic globally.
3.  **Cleanse** internal text from image-based containers.
4.  **Inject** the Intersection Observer script for smooth reveal animations.

**Protocol**: Push to GitHub after every edit.
