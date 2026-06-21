# KORRA AI: The 70-Step "Unicorn" Implementation Roadmap
**Goal:** Transition from a technical dashboard to a segmented, role-specific "Operating System" with high-end glassmorphism and narrative-driven UX.

---

### Phase 1: Foundation & Global Logic (Steps 1–10)
1.  **Template Inventory:** Map all current `dashboard.html` HTML snippets (e.g., `#view-overview`, `#view-vault`) to reusable JavaScript components to eliminate clutter.
2.  **Theme Engine:** Initialize `KORRA_THEME_ENGINE` in `dashboard.html` script block to auto-detect `account_type` from Supabase on login and trigger role-specific UI.
3.  **Global Token CSS:** Define CSS variables for `--Mint: #57D7C0`, `--Glass: rgba(255, 255, 255, 0.04)`, and `--Obsidian: #0C0C0C` in `dashboard.html` `:root`.
4.  **Profile Refactor:** Update the central profile fetch logic in `dashboard.html` (`init()` function) to retrieve role-specific metadata like `widget_config` and `brand_mapping`.
5.  **Layout Manager:** Build a logic layer in `dashboard.html` to toggle `.sidebar-nav` (Desktop) vs. Fixed Bottom-Nav (Mobile) based on screen width (Mobile standard 4-tab).
6.  **Jargon Dictionary:** Create a lookup table in JS to map technical terms to friendly terms (e.g., "Webhooks" -> "Auto-Sync", "Avg Precision" -> "Scan Confidence").
7.  **Route Guard:** Implement an internal router in `dashboard.html` to handle dashboard sub-views (tabs) using `window.location.hash` without page reloads.
8.  **Multi-Selection State:** Set up a global JS object in `onboarding.html` to track `userData.selected_verticals` and `userData.selected_sub_specialties` for multi-industry.
9.  **Z-Index Audit:** Standardize glass panel stacking in global CSS to prevent `.modal-overlay` and `.tooltip` overlapping (Standardize to `z-index: 1000+`).
10. **Backend Semaphore:** Confirm the Python semaphore in `api/routes/measurements.py` is locked at `asyncio.Semaphore(1)` to prevent `t3.micro` OOM crashes.

---

### Phase 2: Visual DNA & Glassmorphism (Steps 11–20)
11. **The Glass Class:** Implement `.glass-card` and `.glass-panel` in `dashboard.html` and `index.html` with `backdrop-filter: blur(20px)` and semi-transparent borders.
12. **Neon Glows:** Create `.teal-glow` (box-shadow 0 0 20px) and `.orange-alert` CSS utility classes for active states and critical warnings.
13. **Typography Scaling:** Standardize headers using `Inter 900` (bold) and subtext using `Inter 400` (light) across all `.html` files.
14. **Custom Scrollbars:** Replace browser scrollbars in `dashboard.html` and `onboarding.html` with thin, translucent tracks matching the dark theme.
15. **Entry Animations:** Implement CSS "Fade-Up" reveals (`opacity:0; transform:translateY(20px)`) for all dashboard page transitions (`.tab-view.active`).
16. **Interaction Feedback:** Add subtle `scale(1.02)` and `box-shadow` glows to primary action buttons (`.btn-primary`) using `transition: 0.3s cubic-bezier`.
17. **Hero Metric Layout:** Design the "1-3-All" reveal pattern in `dashboard.html` (1 Big Metric, 3 Small Metrics, 1 Detailed Table) to establish narrative hierarchy.
18. **Passive Indicators:** Replace noisy banners with pulsing `.status-dot` for Sync/Health in `dashboard.html` header to reduce noise and distractions.
19. **Dark Canvas:** Set the global background to a deep `#0C0C0C` in `:root` of all pages to make the teal pop and meet 11:1 contrast ratios.
20. **Contrast Audit:** Verify every UI element in `dashboard.html` meets WCAG 2.1 standards for accessibility using automated testing.

---

### Phase 3: Onboarding Hardening (Steps 21–30)
21. **Panel Viewport Fix:** Update `showPhase()` in `onboarding.html` to target `.form-panel` for `scrollTo({ top: 0, behavior: 'smooth' })` on next-flow entry.
22. **State Persistence:** Update `saveProgress()` in `onboarding.html` to save industry and demographic selections to Supabase `profiles` in real-time.
23. **Back-Navigation Logic:** Ensure `prevPhase()` in `onboarding.html` correctly resets to the full Industry Grid if a sub-selection view was active.
24. **First Run Experience (FRX):** Trigger a "Welcome Tour" (Intro JS) in `dashboard.html` only for users where `onboarding_completed: false`.
25. **Auto-Role Population:** Pre-fill the dashboard UI based on the user's `account_type` (Individual, Artisan, Merchant, Enterprise) retrieved in `initSession()`.
26. **Verification Icon:** Confirm `success-verify.png` (high-res 3D thumbs-up) is loading from the local asset path in `verification-success.html`.
27. **Progress Pulsing:** Add a breathing animation to the `.segment.active` onboarding progress segment in `onboarding.html` using `@keyframes breathe`.
28. **Narrative Header:** Dynamically change the `<h2>` text in `onboarding.html` based on the detected `account_type` to reinforce user persona.
29. **Mobile Keyboard Guard:** Adjust CSS padding in `onboarding.html` `.form-container` so mobile keyboards don't cover the "Continue" buttons.
30. **Force HTTPS:** Implement a client-side redirect in `api/main.py` or middleware to ensure onboarding only runs on secure connections for `getUserMedia`.

---

### Phase 4: Role 1 - Individual "Digital Wardrobe" (Steps 31–40)
31. **Dev-Item Suppression:** Hide all API, Webhook, and Merchant Implementation menus in `dashboard.html` for `account_type === 'individual'`.
32. **Mirror Mode:** Center the `dashboard-3d-viewport` visual as the primary focus (Hero Metric) of the home screen in `dashboard.html`.
33. **Brand Matcher Logic:** Implement the mapping layer in JS (e.g., "Your waist = Zara Medium") based on extracted measurement ranges and brand tables.
34. **QR Passport:** Create a "Show at Shop" view in `dashboard.html` with a massive, high-contrast QR code generated via `qrcode.min.js`.
35. **Measurement Trends:** Build the "Fit History" chart using `usageChart` canvas in `dashboard.html` showing body changes over time.
36. **Data Education:** Add "What is this?" tooltips for technical biometrics like "Inseam" or "Crotch Depth" in the `measurementResultsCard`.
37. **Goal Tracking:** Allow users to set a "Target Fit" (e.g., Slim vs. Relaxed) in their profile settings to guide size recommendations.
38. **Passport Export:** Update `window.KORRA_EXPORT.pdf` to support a "Pocket Size Sheet" format for printing and physical sharing.
39. **Privacy Shield:** Add a "Ghost Mode" toggle in `dashboard.html` to hide specific sensitive data columns in the profiles table from shared links.
40. **Wardrobe Stacking:** Optimize the 3D Model viewer for full-screen portrait view on mobile devices for the "Virtual Mirror" feel.

---

### Phase 5: Role 2 - Tailor "Command Center" (Steps 41–50)
41. **Ledger-First Landing:** Set the `#view-vault` (Client List/Ledger) as the default active tab for `account_type === 'artisan'`.
42. **Advanced Search:** Implement height-range and date-range filtering for `ledgerSearch` in `dashboard.html` for fast client retrieval.
43. **Craftsman Notes:** Add a rich-text field for "Specific Tailoring Requirements" (patterns, fabrics) on client cards in the `scanList`.
44. **Export Center:** Build a bulk-download area in `dashboard.html` for PDF pattern sheets and 3D OBJ mesh files for design software.
45. **Handshake Monitor:** Create a "Status Indicator" in the client table showing if clients have completed their photos or are still "Sync Paused".
46. **Studio Invite:** Generate a custom link using `window.location.origin + '/share?m=' + userId` to pre-identify the tailor in the client's signup.
47. **Credit Monitor:** Place "Credits Remaining" in the top-right header for constant visibility to prevent scan interruptions.
48. **Quality Scoring:** Display an AI confidence score (e.g., 98% Accurate) for each scan based on the `body_shape` and `debug` output.
49. **Artisan Visuals:** Use "Ruler" and "Scissors" iconography from the provided design system to reinforce the professional craftsman persona.
50. **Mobile Scanning:** Optimize the "Start Scan" FAB (Floating Action Button) for one-thumb reach in the mobile bottom-nav.

---

### Phase 6: Role 3 - Brand Studio "Shopify Editor" (Steps 51–60)
51. **Split-Screen Studio:** Design the "Settings on Left | Preview on Right" editor layout in the Widget tab of `dashboard.html` (60/40 ratio).
52. **Neon Color Binding:** Bind the color picker (`widgetColorPrimary`) directly to the live widget CSS variables via `element.style.setProperty('--primary-color', val)`.
53. **Identity Sync:** Allow logo uploads that update the widget header in real-time in the `widgetLivePreview` (Device Mockup).
54. **Theme Toggles:** Implement "Glass", "Light", and "Dark" preset modes for the widget in `dashboard.html` applying unique CSS variable sets.
55. **Conversion Dashboard:** Build the "Return Rate Reduction" hero chart in `dashboard.html` showing percentage saved by accurate sizing.
56. **Drop-off Funnel:** Implement a heatmap/funnel chart showing where users stop in the scan flow in `dashboard.html` analytics view.
57. **No-Code Snippet:** Update `window.copyWidgetCode` to handle automated clipboard fallback (`KORRA_UTILS.copyToClipboard`) in `dashboard.html`.
58. **Heartbeat API:** Show a "Sync Active" indicator for Shopify/E-commerce integrations ensuring data is flowing to their inventory.
59. **Multi-Device Mockup:** Allow switching the preview between Phone, Tablet, and Laptop frames in the `widgetLivePreview`.
60. **Branding Lock:** Ensure widget settings are persisted to the `widget_config` JSON column in the Supabase `profiles` table.

---

### Phase 7: Role 4 - Enterprise "Intelligence Hub" (Steps 61–65)
61. **Aggregate Insights:** Build the "Global Average Body Shape" statistical view in `dashboard.html` for high-level market intelligence.
62. **Regional Heatmaps:** Implement a world map showing Body Type distribution by country using `chart.js` or `d3.js` in `dashboard.html`.
63. **Staff Permissions:** Create the "Team Member" invite view in `dashboard.html` to allow role-restriction for factory workers vs. designers.
64. **GDPR Compliance:** Build the "Right to be Forgotten" portal for bulk data deletion and audit trails of data access.
65. **Industrial API Management:** Design a high-capacity API key dashboard for enterprise developers with rate-limit monitoring.

---

### Phase 8: Mobile Polish & Production (Steps 66–70)
66. **Bottom-Nav Hardening:** Finalize the 4-tab mobile navigation bar (Home, Clients, Scan, Settings) with 48px minimum touch targets.
67. **Accessibility Final Pass:** Verify keyboard navigation and ARIA screen reader tags across all `.html` files using the `Senior UX` audit checklist.
68. **Update Guide Update:** Finalize `REMOTE_UPDATE_GUIDE.md` with the new SSL renewal logic and `update.sh` automated health checks.
69. **Production Deployment:** Trigger the final `update.sh` on the AWS instance (`13.60.215.88`) with correct `--env-file` mapping.
70. **Global Health Check:** Verify `https://korra.work` is 100% healthy across all 4 journeys (Individual, Artisan, Brand, Enterprise).
