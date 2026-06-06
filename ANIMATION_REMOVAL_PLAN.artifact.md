# Animation Removal & Instant Visibility Plan
**Status**: High-Priority Cleanup

The user has requested the total removal of animations. We are shifting from a "Motion Reveal" UX to a "Zero-Latency Instant" UX.

## 1. CSS Deletion
*   Remove `.reveal` class definition.
*   Remove `.reveal.active` class definition.
*   Remove all `transition` and `transform` properties associated with the reveal system.

## 2. HTML Sanitization
*   Globally remove the `reveal` class from all `<section>` and `<div>` tags.
*   Ensure all content is `opacity: 1` and `transform: none` by default.

## 3. JavaScript Purge
*   Delete the `IntersectionObserver` setup.
*   Delete the `forcedReveal()` function.
*   Remove the observer trigger from `handleRoute()`.

---

## 4. Visual Integrity Maintenance
*   **Grid**: Maintain the **1150px Nops-width**.
*   **Imagery**: Maintain the **1.5fr large visual grid**.
*   **Colors**: **Strict Obsidian & Mint**.
*   **Copy**: Preserve the **Hardened Startup Narrative**.

**Protocol**: Push to GitHub immediately after edit.
