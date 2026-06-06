# KORRA: True Industrial Self-Hosting Roadmap
**Standard**: Enterprise SaaS (Stripe/Uber Grade)
**Objective**: Own the "Brain" of the platform by self-hosting all JS dependencies to eliminate CDN failures and extension conflicts.

---

## Phase 1: Dependency Procurement
*   **Action**: Use `curl` to download the official Supabase v2.x production minified build.
*   **Target**: `/Users/mac/ai-body-scan-saas/public/assets/supabase.min.js`
*   **Benefit**: No more 403 Forbidden errors from external CDNs.

## Phase 2: Local Asset Infrastructure
*   **Action**: Verify `/public/assets` directory permissions and mapping in FastAPI.
*   **Hardening**: Ensure the server serves these files with correct `application/javascript` MIME types and caching headers.

## Phase 3: Core Page Migration (Landing & Auth)
*   **Action**: Update `index.html`, `signin.html`, and `signup.html`.
*   **Change**: Replace `<script src="https://cdn...">` with `<script src="/assets/supabase.min.js"></script>`.
*   **Benefit**: Site boots in half the time; un-blockable by Monica AI.

## Phase 4: Operational Page Migration (Dashboard)
*   **Action**: Update `dashboard.html`.
*   **Change**: Transition all operational views to use the local library.
*   **Feature**: Ensure "New Scan" and "Merchant API" handshakes remain intact.

## Phase 5: Support Page Migration (Narrative)
*   **Action**: Update `about.html`, `casestudies.html`, `theoryofchange.html`, `sizepassport.html`, and `legal.html`.
*   **Benefit**: 100% universal dependency parity across the entire 7-page ecosystem.

## Phase 6: Logic Simplification (Removal of "The Hack")
*   **Action**: Delete all "Triple-CDN Fallback" logic, "Dependency Polling" loops, and "Handshake Delay" alerts.
*   **Result**: Clean, elegant, readable code that any senior engineer can maintain.

## Phase 7: Global Namespace Standardization
*   **Action**: Standardize the database instance as `window.KORRA_CORE`.
*   **Benefit**: Absolute protection against future extension conflicts or variable name hijacking.

## Phase 8: Security Hardening (CSP)
*   **Action**: Implement Content Security Policy (CSP) headers in [api/main.py](file:///Users/mac/ai-body-scan-saas/api/main.py).
*   **Logic**: Restrict script execution to local files only (`'self'`).

## Phase 9: Forensic Stress Test
*   **Action**: Test signup and dashboard flows with Monica AI, AdBlockers, and low-bandwidth simulation.
*   **KPI**: Zero "Security Handshake Delay" alerts; instant button activation.

## Phase 10: Production Release & Cleanup
*   **Action**: Final `git push`, Render deployment verification, and archive legacy "Hack" documentation.

---

**Protocol**: Every implementation step will be followed by a `git push origin main`.
