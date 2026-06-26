# KORRA: Gap-Closure Master Plan (Production Hardening)
**Objective**: Transition from Prototype to a functional "Digital Artisan Infrastructure."
**Design System**: Strict Obsidian & Mint (#000000 base, #C6FF00 accent, 1150px grid).

---

## Phase 1: Structural Integrity (Killing the 404s)
**Goal**: Create standalone pages for all header navigation links to complete the Multi-Page Architecture.

*   **[NEW] [about.html](file:///Users/mac/ai-body-scan-saas/about.html)**:
    *   Content: KORRA's mission, the "Distance Factor" philosophy, and the Artisan Empowerment narrative.
*   **[NEW] [casestudies.html](file:///Users/mac/ai-body-scan-saas/casestudies.html)**:
    *   Content: The "London Client. Lagos Tailor." success story and industrial waste reduction metrics.
*   **[MOD] [index.html](file:///Users/mac/ai-body-scan-saas/index.html)**:
    *   Action: Update navigation `href` values from placeholders to actual `.html` paths.

---

## Phase 2: Functional Intelligence (The Living Dashboard)
**Goal**: Wire the "Merchant Workbench" to live data and real user actions.

*   **[MOD] [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html)**:
    *   **Live Vault**: Implement `supabase.from('measurements').select('*')` to replace the "No data found" empty state.
    *   **Stat Engine**: Calculate "Total Scans" and "Remaining Credits" dynamically from the database.
    *   **New Scan Trigger**: Implement the "New Scan" modal/overlay to capture client data.
*   **[MOD] [api/main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)**:
    *   Action: Harden the `/api/v2/measurements` endpoints to ensure they correctly serve the dashboard's fetch requests.

---

## Phase 3: Operational Power (Merchant API & Payments)
**Goal**: Enable artisans to scale their business using KORRA's infrastructure.

*   **[MOD] [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html)**:
    *   **API Command Center**: Add a "Generate API Key" feature allowing merchants to integrate KORRA into their own sites.
    *   **Credit Top-up**: Link the "Credits" card to a Paystack payment modal for the $0.50/scan model.
*   **[MOD] [api/services/paystack_service.py](file:///Users/mac/ai-body-scan-saas/api/services/paystack_service.py)**:
    *   Action: Finalize the transaction verification loop to update Supabase credits upon successful payment.

---

## Phase 4: Infrastructure Hardening (Security & UX)
**Goal**: Professionalize the session management and environment configuration.

*   **[MOD] [index.html](file:///Users/mac/ai-body-scan-saas/index.html)**:
    *   **Session Persistence**: If a user is logged in, change the "Sign In" button to "Go to Workbench."
*   **[MOD] [signup.html](file:///Users/mac/ai-body-scan-saas/signup.html)**:
    *   **Auto-Redirect**: Ensure users are taken straight to the dashboard after email verification.

---

## Verification Protocol
1.  **Cross-Page Check**: Navigate from Home -> About -> Sign In -> Dashboard -> Home. (Zero 404s).
2.  **Data Check**: Create a test measurement in Supabase; verify it appears in the Dashboard vault instantly.
3.  **Auth Check**: Attempt to visit `/dashboard` while logged out; verify instant kickback to `/signin`.

**Protocol**: Every implementation step will be followed by a `git push origin main`.
