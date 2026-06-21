# KORRA AI: Senior UI/UX Forensic Audit Report
**Date:** June 20, 2026
**Auditor:** Senior UI/UX Design Lead (Expert Persona)

## 1. Executive Summary
The current Korra AI platform demonstrates strong core functionality but suffers from **"Technical Debt in the UI"**. The interface is currently a "Developer's Dashboard" being presented to Artisans. To achieve "Unicorn" status, we must transition from a data-dumping utility to a **narrative-driven experience**.

## 2. Critical Friction Points

### A. The Onboarding "Dead-End" & Navigation
*   **Audit Finding:** Phase transitions fail to reset the viewport. Because the UI uses a fixed split-layout, the parent `window` scroll is independent of the child `form-panel`.
*   **UX Impact:** Users enter a new step (e.g., from Gender to Industry) but remain scrolled at the bottom, missing the headline and initial inputs. This creates a "broken" feel.
*   **Recommendation:** Implement targeted scroll-to-top on the `.form-panel` DOM element.

### B. "The Developer's Shadow" (Sidebar & Jargon)
*   **Audit Finding:** The sidebar exposes high-friction technical items (Webhooks, API Access, Ledger) at the same hierarchy as "Home" and "Clients".
*   **UX Impact:** Non-technical tailors feel overwhelmed. The "Invisible Navigation" principle is violated; the menu is a distraction rather than a tool.
*   **Recommendation:** Flatten the primary menu to 4 key pillars: **Overview, Clients, Measurements, settings**. Move all "Dev-Mode" items into an **Advanced** or **Developer Hub** sub-section.

### C. Repetitive Noise & Clutter
*   **Audit Finding:** High-frequency status badges ("Sync Active", "Health: ACTIVE") compete for visual attention with core data.
*   **UX Impact:** Banners that require manual dismissal create "Click Fatigue".
*   **Recommendation:** Use "Passive Indicators" (pulsing dots, subtle border glows) for status, and reserve high-visibility banners only for **Actionable Errors** (e.g., "Payment Failed").

### D. Information Hierarchy (The "Narrative" Problem)
*   **Audit Finding:** Dashboards use a uniform 3-card stat grid. There is no "Hero Metric".
*   **UX Impact:** The user doesn't know what to celebrate or what to worry about.
*   **Recommendation:** Adopt the **"1-3-All" Reveal Pattern**:
    1.  One massive Hero Metric (e.g., "Active Clients this Month").
    2.  Three supporting data points (Accuracy, Growth, Credits).
    3.  Detailed tables only via progressive disclosure (clicking "View All").

## 3. Visual Identity: "The Unicorn Shift"

### A. From Flat to Glass (Glassmorphism)
*   Current surfaces are solid `#171717`.
*   **Target:** Semi-transparent blurred panels (`backdrop-filter: blur(20px)`) with a 1px linear-gradient border (`rgba(255,255,255,0.1)` to `transparent`) to create depth and a futuristic AI feel.

### B. Mobile "Thumb-Reach" Navigation
*   **Current:** Sidebar collapses or stays at the top.
*   **Target:** Fixed bottom-tab bar with a central floating action button (FAB) for the core "Start Scan" task.

---

## 4. Proposed Implementation Plan

### Phase 1: Navigation & State Recovery
*   [ ] **Onboarding Scroll Fix:** Update `showPhase()` to target `.form-panel`.
*   [ ] **State Persistence:** Ensure `localStorage` or Supabase session state is checked before initializing `Phase 1` to allow users to resume.

### Phase 2: Dashboard De-Cluttering
*   [ ] **Menu Flattening:** Hide Webhooks/API/Ledger from the main view.
*   [ ] **Terminology Scrub:**
    *   "Artisan Overview" -> "Command Center"
    *   "Implementation" -> "Widget Setup"
    *   "Webhooks" -> "Auto-Sync"

### Phase 3: The "Brand Studio" Live Preview
*   [ ] **Shopify-style Editor:** 2-column layout (Control Panel on Left | Live Device Mockup on Right).
*   [ ] **Instant CSS-in-JS Binding:** Update widget theme variables in real-time as the user types/picks colors.

### Phase 4: Aesthetic Hardening
*   [ ] **Glassmorphism Component Library:** Create standard `.glass-panel` and `.neon-glow` CSS classes.
*   [ ] **Mobile Bottom Nav:** Implement standard 4-tab mobile navigation.
