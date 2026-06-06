# KORRA: 10-Phase Global Infrastructure Roadmap
**Mission**: Transform from a high-fidelity prototype into a production-ready "Digital Artisan Infrastructure."
**Visual Spec**: Strict Obsidian & Mint (#000000 / #57D7C0), 1150px grid, Multi-Page Architecture.

---

## ✅ Phase 1: Brand Hardening & UI Foundation
*   **Status**: COMPLETED
*   **Deliverables**: Standardized 1150px layout, Obsidian/Mint palette, and high-contrast glassmorphism.
*   **Files**: `index.html`, `signin.html`, `signup.html`.

## ✅ Phase 2: Narrative & Impact Authority
*   **Status**: COMPLETED
*   **Deliverables**: Integrated 150-word "Global Reach" story, "London-to-Lagos" case study, and DIV Fund alignment.
*   **Files**: `index.html`, `about.html`, `casestudies.html`.

## ✅ Phase 3: Multi-Page "Real Page" Transition
*   **Status**: COMPLETED
*   **Deliverables**: Eliminated SPA routing, created dedicated standalone `.html` files for all primary views.
*   **Files**: `signin.html`, `signup.html`, `dashboard.html`.

## 🔄 Phase 4: Authentication Depth & Session Persistence
*   **Status**: IN PROGRESS
*   **Goal**: Professionalize the onboarding flow to capture industrial-grade data.
*   **Action**: Update [signup.html](file:///Users/mac/ai-body-scan-saas/signup.html) to capture "Company Name," "Industry," and "Monthly Volume."
*   **Logic**: Implement landing page session-detection to auto-redirect logged-in users to the workbench.

## 🔄 Phase 5: The Merchant Workbench (Functional Core)
*   **Status**: IN PROGRESS
*   **Goal**: Turn the dashboard into a living tool.
*   **Action**: Wire [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html) to live Supabase data (`measurements` table).
*   **Feature**: Implement tab-persistence using URL hashes (e.g., `/dashboard#api`).

## 🚀 Phase 6: AI Extraction Handshake (The Engine)
*   **Status**: PENDING
*   **Goal**: Activate the "New Scan" button.
*   **Action**: Connect the [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html) modal to the [api/routes/measurements.py](file:///Users/mac/ai-body-scan-saas/api/routes/measurements.py) endpoint.
*   **Requirement**: Real file upload for front/side photos and height input.

## 🚀 Phase 7: Merchant API Command Center
*   **Status**: PENDING
*   **Goal**: Empower tailors to scale.
*   **Action**: Implement real API key generation in [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html) using Supabase `api_keys` table.
*   **Requirement**: "Copy to Clipboard" functionality and status tracking.

## 🚀 Phase 8: Economic Infrastructure (Payments)
*   **Status**: PENDING
*   **Goal**: Finalize the $0.50/scan business model.
*   **Action**: Integrate Paystack popup in the "Credits" section of [dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html).
*   **Backend**: Finish verification logic in [api/services/paystack_service.py](file:///Users/mac/ai-body-scan-saas/api/services/paystack_service.py).

## 🚀 Phase 9: Global Support Ecosystem (Content)
*   **Status**: PENDING
*   **Goal**: Close all dead footer links.
*   **Deliverables**:
    *   [NEW] [theoryofchange.html](file:///Users/mac/ai-body-scan-saas/theoryofchange.html) (DIV Fund specific).
    *   [NEW] [sizepassport.html](file:///Users/mac/ai-body-scan-saas/sizepassport.html) (Individual user focus).
    *   [NEW] [legal.html](file:///Users/mac/ai-body-scan-saas/legal.html) (Privacy & Terms).

## 🚀 Phase 10: Production Launch & Security Audit
*   **Status**: PENDING
*   **Goal**: Zero-fail deployment.
*   **Action**: Lockdown CORS in [api/main.py](file:///Users/mac/ai-body-scan-saas/api/main.py), implement production error logging, and finalize Render environment variables.

---

**Protocol**: Every implementation phase will be followed by a `git push origin main`.
