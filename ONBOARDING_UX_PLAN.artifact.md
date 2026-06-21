# Implementation Plan: Onboarding UX & Dashboard Hardening

## 1. Onboarding Phase Recovery
*   **Target:** `onboarding.html`
*   **Action:** Update `showPhase()` to explicitly scroll the `.form-panel` container.
*   **Logic:**
    ```javascript
    const formPanel = document.querySelector('.form-panel');
    if (formPanel) formPanel.scrollTo({ top: 0, behavior: 'smooth' });
    ```
*   **State:** Check Supabase profile for `onboarding_phase` and resume automatically.

## 2. Dashboard De-Cluttering (The "Artisan" Mode)
*   **Target:** `dashboard.html`
*   **Sidebar Refactor:**
    *   Primary: Home, Clients, Measurements, Settings.
    *   Hidden/Grouped: API Keys, Webhooks, Webhooks Ledger.
*   **Terminology Update:**
    *   "Avg Precision" -> "Scan Confidence"
    *   "Scan Velocity" -> "Measurement Trends"

## 3. Brand Studio (Shopify-style Editor)
*   **Target:** `dashboard.html` (Widget Tab)
*   **Action:** implement a 60/40 split screen.
    *   **Left (60%):** Configuration inputs (Brand color, Logo upload, Theme selection).
    *   **Right (40%):** A fixed "Floating Mobile Device" mockup running the live widget.
*   **Tech:** Use `element.style.setProperty('--primary-color', value)` to update the preview instantly.

## 4. Visual "Unicorn" Polish
*   **Global CSS:** Implement a `.glass-panel` class with `backdrop-filter: blur(20px)` and semi-transparent borders.
*   **Animations:** Use the already implemented Intersection Observer to reveal content with "Fade-Up" effects.
