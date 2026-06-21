# KORRA AI: The 100-Step "Unicorn" Mastery Roadmap
**Perspective:** Senior UI/UX Design Lead & Lead Product Engineer
**Goal:** Transition from a technical dashboard to a world-class, outcome-driven "Operating System" with high-end luxury aesthetics.

---

### Phase 1: Global Aesthetic & "Luxury" Core (Steps 1–10)
1.  **Color Space Re-balancing:** Shift from pure `#000000` to a deep, layered `#050505` and `#0B0B0C` palette in `:root`.
2.  **Glass 2.0 Implementation:** Define `.luxury-glass` with a primary `backdrop-filter: blur(40px)` and a subtle `linear-gradient` border.
3.  **Soft Elevation System:** Create CSS variables for three levels of depth: `--Elev-1` (Subtle), `--Elev-2` (Float), `--Elev-3` (Hero).
4.  **Typography Mastery:** Lock `Inter` tracking to `-0.02em` for headings and `+0.01em` for subtext to achieve a "premium tech" feel.
5.  **Global Token Audit:** Replace all hardcoded colors with tokens like `--Accent-Teal`, `--Accent-Gold`, and `--Surface-Soft`.
6.  **Minimalist Outlines:** Reduce global border-widths to `0.5px` where possible to minimize visual noise.
7.  **Restrained Glows:** Implement `.accent-glow` using `box-shadow: 0 0 40px rgba(87, 215, 192, 0.15)` for interactive elements only.
8.  **Depth Overlay Logic:** Standardize `z-index` layers: Navigation (2000), Modals (3000), Toasts (4000).
9.  **Dark Canvas Hardening:** Ensure a consistent 11:1 contrast ratio for all primary body text.
10. **Custom Translucent Tracks:** Finalize the "Invisible" scrollbar that only appears on hover with a thin teal line.

---

### Phase 2: Narrative Copy & Outcome-Driven Language (Steps 11–20)
11. **Technical Scrub (Global):** Map all technical IDs/classes to descriptive narrative labels in the code comments.
12. **CTA Redesign (Individual):** Change "Get Measurements" to "Get body measurements."
13. **CTA Redesign (Merchant):** Change "Synchronize Aesthetics" to "Publish Branded Experience."
14. **Status Label Refactor:** Change "Handshake: ACTIVE" to "Cloud Sync Live."
15. **Error Narrative:** Replace "OOM Failure" with "High Demand: Retrying in Secure Queue."
16. **Success Narrative:** Replace "Settings Saved" with "Brand Profile Optimized."
17. **Empty State Story:** Design "Start your first scan to unlock your size passport" for new users.
18. **Instructional Tone Pass:** Update all `pro-tips` to sound like a personal tailoring assistant.
19. **Metadata Labels:** Change "Industry Vertical" to "Business Focus."
20. **Confidence Language:** Change "99% Precision" to "Clinical-Grade Accuracy."

---

### Phase 3: Progressive Disclosure & Global Nav (Steps 21–30)
21. **Sidebar Tiering:** Hide "Advanced" and "Developer" items by default in a collapsible bottom section.
22. **The 4-Pillar Layout:** Force the sidebar to only show: Home, Clients, Store, Settings.
23. **Contextual Sub-nav:** Only reveal "Webhooks" or "API" once the user clicks "Advanced Settings."
24. **Drawer Logic:** Implement an "Advanced Configuration" sliding drawer for technical fields.
25. **Persistent Progress Bar:** Add a thin, glowing top-bar that shows "Sync State" globally.
26. **Route Transition Fix:** Implement a "Fade-Through" logic where the viewport clears before the new tab loads.
27. **Mobile Bottom-Nav Hardening:** Standardize the 4-tab bar with 64px height and centered FAB.
28. **One-Thumb Reach Audit:** Verify all primary actions are within the bottom 40% of the screen.
29. **Search Overlay:** Replace the fixed search bar with a "Command + K" style global search overlay.
30. **Notification Stack:** Move all status alerts into a single, grouped "Activity Hub" icon.

---

### Phase 4: Role 1 - Individual "Digital Wardrobe" (Steps 31–40)
31. **Hero Viewport Redesign:** Make the 3D Model occupy 70% of the Home screen as a "Virtual Mirror."
32. **Personal Promise First:** Lead with "Welcome back, [Name]. Your fit is verified."
33. **Fit Trends Canvas:** Implement a "Body Health" chart showing measurement stability over time.
34. **Size Passport QR:** Design the QR card to look like a premium black-and-gold credit card.
35. **Brand Matching Cards:** Create visual "Brand Fit" cards (e.g., Nike, Zara) with confidence scores.
36. **Private Mode Toggle:** Add a high-visibility "Privacy Shield" button to blur data instantly.
37. **Measurement Details:** Use progressive disclosure—click a body part to see the specific CM/IN.
38. **Fit Education:** Add "Why this matters" expandable cards for complex biometrics.
39. **Wardrobe Stacking:** Allow users to "Upload Fit Reference" (photo of a shirt that fits them well).
40. **Mobile Mirror Mode:** Trigger full-screen portrait 3D viewer on login.

---

### Phase 5: Role 2 - Tailor "Command Center" (Steps 41–50)
41. **Operational Dashboard:** Set the default view to the "Active Client Ledger."
42. **Search Logic Upgrade:** Implement "Smart Filters" (e.g., "Recently Scanned," "Needs Pattern").
43. **Craftsman Note Area:** Redesign the notes section to look like a high-end leather notebook.
44. **Quality Scoring Badge:** Add a glowing "AI Confidence" badge to every client card.
45. **One-Click Export Strip:** Add a floating action bar to client profiles for OBJ/PDF/CSV.
46. **Studio Invite Portal:** Design the "Studio QR" poster as a beautiful, printable PDF.
47. **Client Handshake Monitor:** Use a pulsing pulse-icon to show when a client is "Currently Scanning."
48. **Pattern Logic Integration:** Implement a "Cut Ready" status based on measurement completeness.
49. **Artisan Iconography:** Use custom-drawn line icons for Ruler, Scissors, and Thread.
50. **Mobile FAB Optimization:** Make the "Start Scan" button a large, glowing teal FAB.

---

### Phase 6: Role 3 - Brand Studio "Experience Editor" (Steps 51–60)
51. **The Cinema Viewport:** Set the Right Preview to 65% width with a device frame that floats.
52. **The Customization Rail:** Make the Left Rail 35% width, slim, with grouped accordions.
53. **Live CSS Binding:** Bind every input (color, radius) to CSS variables with zero latency.
54. **Logo Overlay Editor:** Allow dragging the brand logo into different corners of the widget.
55. **Widget Landing View:** Redesign the "Welcome" screen of the widget to look like a luxury invite.
56. **ROI Dashboard:** Add a "Revenue Recovered" counter based on return-rate reductions.
57. **Conversion Funnel Visual:** Implement a sleek, glowing funnel chart for scan drop-offs.
58. **Advanced Theme Presets:** Add "Midnight," "Paper," and "Holographic" one-click themes.
59. **Multi-Platform Preview:** Switch between "Hosted Page," "Overlay," and "Embedded" views.
60. **Publish State Bar:** Add a bottom-fixed bar for "Discard" vs. "Publish Changes."

---

### Phase 7: Role 4 - Enterprise "Intelligence Hub" (Steps 61–70)
61. **Aggregated Intelligence:** Design the "Global Body Shape Distribution" as a 3D bar chart.
62. **Regional Heatmap:** Implement a world map with glowing dots for scan density.
63. **Staff Permission Matrix:** Build a clean "Role Switcher" (Owner, Designer, Factory, Staff).
64. **GDPR Audit Trail:** Create a ledger of who accessed what data and when.
65. **Industrial API Dashboard:** Show "Heartbeat" stats for 10,000+ monthly scan quotas.
66. **Bulk Data Action Bar:** Enable multi-select for profiles to "Export for Factory."
67. **Security Fortress View:** Show active IP address locks and security status.
68. **Compliance Export:** One-click "Privacy Report" for legal teams.
69. **Rate Limit Gauge:** A high-end radial gauge showing monthly API consumption.
70. **Team Member Activity:** A vertical feed of "Recent Factory Actions."

---

### Phase 8: Component Engineering (Steps 71–80)
71. **Metric Card Refactor:** Create a unified `StatCard` with sparklines and big numbers.
72. **Input Field Standardization:** implement the "Focus Glow" and "Valid Check" icons.
73. **Modal Refactor:** Use the `.luxury-glass` for all popups with "Spring" entry animations.
74. **Button System:** Define `btn-hero`, `btn-primary`, `btn-ghost`, and `btn-danger`.
75. **Tooltip Library:** Standardize all "What is this?" info bubbles with 0.3s delay.
76. **Avatar System:** Design high-end "Professional Initials" for users without photos.
77. **Table Ledger System:** Implement sticky headers and "Row-Click" expansion.
78. **Toggle Switches:** Re-design as sleek, high-contrast "Mercury" sliders.
79. **Progress Ring:** Design a specific "AI Thinking" ring that orbits the 3D model.
80. **Toast Notification System:** Implement "Stacking" toasts at the bottom right.

---

### Phase 9: Mobile Master Pass (Steps 81–90)
81. **Mobile Header Collapse:** Shrink the header height to 56px when scrolling.
82. **Thumb-Driven Modals:** All popups must now be "Bottom Sheets" on mobile.
83. **Haptic Feedback Mapping:** Define where mobile devices should vibrate (e.g., Scan Success).
84. **Touch Target Pass:** Verify every button is exactly 48x48px or larger.
85. **Gesture Controls:** Implement "Swipe to Delete" for client ledger rows.
86. **Mobile Preview Lock:** Ensure the Brand Studio preview frame is un-scrollable.
87. **Scan Orientation Guard:** Force the device to "Portrait" during scan capture.
88. **Low-Light Indicator:** Add a warning if the camera environment is too dark.
89. **Bottom-Nav Badge logic:** Show red dots for "Needs Pattern" or "New Result."
90. **Offline State UI:** Build the "Sync Paused" mobile overlay for poor signal areas.

---

### Phase 10: Production Launch & Monitoring (Steps 91–100)
91. **CSS Compression Pass:** Minify and optimize all "Unicorn" stylesheets.
92. **Image Asset Optimization:** Convert all JPGs/PNGs to WebP for faster loading.
93. **Global Font-Weight Audit:** Ensure `Inter 900` is used only for Hero text.
94. **Health Check V3:** Implement a "Deep Sync Check" across all roles.
95. **SSL Maintenance Pass:** Verify the auto-renewal logic for `korra.work`.
96. **Supabase Redirect Lock:** Finalize the "Site URL" to `https://korra.work`.
97. **Environment Key Security:** Audit the `.env` on the AWS server for leaks.
98. **OOM Stress Test:** Run 5 concurrent scans on the `t3.micro` instance to verify semaphore.
99. **Final Remote Update:** Trigger `update.sh` with the 100-step finalized build.
100. **Global Launch Health Report:** Visit every page and verify 100% health scores.
