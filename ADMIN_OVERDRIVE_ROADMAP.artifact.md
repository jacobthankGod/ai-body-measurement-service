# KORRA: Admin Overdrive (10-Phase Roadmap)
**Objective**: Transform the Admin Terminal from a visual placeholder into an authoritative "Master Control" for the entire global artisan infrastructure.

---

## 🏗️ Phase 1: Tab-View Infrastructure
*   **Action**: Implement a CSS/JS "Tab Switcher" in [admin.html](file:///Users/mac/ai-body-scan-saas/admin.html).
*   **Deliverables**: Dedicated views for **Overview**, **Registry**, **Health**, and **Finance**.
*   **UI**: Synchronized sidebar navigation highlighting the active tab.

## 📊 Phase 2: Live Global Stat Engine
*   **Action**: Wire the "Total Merchants" and "Total Scans" stat cards to real-time Supabase counts.
*   **Logic**: Use `select('*', { count: 'exact', head: true })` for lightweight fetching.

## 💰 Phase 3: Financial Intelligence (Revenue)
*   **Action**: Sum the `amount_paid` from the `invoices` table to populate "Revenue (NGN)".
*   **Hardening**: Ensure proper formatting of high-value Naira strings.

## ⚡ Phase 4: AI Latency Handshake
*   **Action**: Implement a client-side timer that pings `/api/v2/health` and measures the round-trip time.
*   **UI**: Update "AI Engine Latency" card in real-time.

## 🔍 Phase 5: Merchant Search & Filtering
*   **Action**: Add a high-contrast search bar to the Registry view.
*   **Logic**: Real-time filtering of the `merchantList` by Name, Industry, or Email.

## 🛠️ Phase 6: Credit Overdrive (The Handshake)
*   **Action**: Create a "Credit Override Modal" in [admin.html](file:///Users/mac/ai-body-scan-saas/admin.html).
*   **Logic**: Implement `UPDATE public.profiles SET credits = X` with immediate UI synchronization.

## 🔑 Phase 7: Admin Key Command Center
*   **Action**: Implement "Reveal & Copy" functionality for the `korra_admin_` key.
*   **Security**: Ensure the raw key is never visible in the DOM until the "Eye Icon" is clicked.

## 📓 Phase 8: Financial Audit Ledger
*   **Action**: Populate the "Financial Audit" tab with a live transaction history from the `invoices` table.
*   **UI**: Columns for Merchant, Amount, Reference, and Date.

## 🩺 Phase 9: System Health Dashboard
*   **Action**: Build the "System Health" tab with server status indicators and recent error logs (fetched from a new admin-only endpoint).

## 🔒 Phase 10: Zero-Fail Production Lockdown
*   **Action**: Perform a final security audit of Super-User session persistence.
*   **Hardening**: Force a `z-index: 9999999` on the admin header to ensure absolute click authority.

---

**Protocol**: Every phase implementation will be pushed to GitHub immediately.
