# Merchant Key Readiness Hardening Plan
**Objective**: Eliminate the "Merchant Key Not Ready" error by ensuring a bulletproof handshake between the User Session and the API Infrastructure.

---

## 🔍 Forensic Root Cause Audit
1.  **The Race Condition**: `initDashboard` fires `ensureApiKey` asynchronously. If a user clicks "Run AI Extraction" too fast, the `activeApiKey` variable is still `null`.
2.  **The State Gap**: The "Run AI Extraction" button is enabled by default. It should be disabled until the system confirms the Key is loaded and active.
3.  **The Handshake Failure**: If the `api_keys` table fetch fails (due to RLS or a slow connection), the user is left with a permanent "Not Ready" state with no way to retry.

---

## 🛠️ The Expert Fix Strategy

### Phase 1: The "Key-Ready" Guard
*   **Action**: Disable the `btnRunInference` button by default in the HTML.
*   **Logic**: Only enable the button inside the `.then()` block of the `ensureApiKey` function.
*   **Visual**: Update button text to "Synchronizing Key..." until ready.

### Phase 2: Atomic State Management
*   **Action**: Move `activeApiKey` into a globally protected `window.KORRA_MANAGEMENT` object.
*   **Hardening**: Implement a "Check-Retry" loop (3 attempts) if the initial key fetch fails.

### Phase 3: Forensic Logging & Recovery
*   **Action**: Add a small "Key Status" indicator inside the modal.
*   **Feature**: If the key fails to load after 5 seconds, show a "Manual Sync" button to force a database handshake.

---

## 📍 Path References
*   **[dashboard.html](file:///Users/mac/ai-body-scan-saas/dashboard.html)**: Main logic for key retrieval and modal interaction.
*   **[UNIVERSAL_MASTER_SYNC.sql](file:///Users/mac/ai-body-scan-saas/UNIVERSAL_MASTER_SYNC.sql)**: (Reference) Verified RLS policies for `api_keys` to ensure the frontend has SELECT/INSERT permissions.

**Protocol**: Every update will be pushed to GitHub immediately.
