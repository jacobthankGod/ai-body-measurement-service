# Absolute Fix Plan: 403 Permission Errors & Auth Hardening

The current 403 errors indicate a disconnect between the Frontend requests and the Backend security layer. Specifically, the error `exceptions.UserAuthError` coming from a Chrome extension context suggests that either the API key is missing, invalid in Supabase, or the request headers are being stripped.

## 1. Root Cause Analysis
*   **Missing Supabase Tables**: If `api_keys` table isn't initialized with the correct test keys, every request fails.
*   **Header Name Mismatch**: The backend expects `X-API-Key`, but some client-side libraries or proxies might be using `Authorization` or stripping custom headers.
*   **CORS Preflight Failure**: If the browser's `OPTIONS` request fails due to strict CORS, the subsequent `POST` will throw a 403.
*   **Chrome Extension Interference**: The logs show `chrome-extension://...`, suggesting a browser extension might be intercepting or modifying the requests.

## 2. The "Absolute Fix" Strategy

### Step 1: Backend Auth Hardening
*   Update `api/main.py` to handle CORS more robustly (explicitly allow `X-API-Key`).
*   Implement a "Safe Fallback" in `middleware/api_key_auth.py` that checks for a `PRECISIONFIT_MASTER_KEY` environment variable to ensure you are never locked out.

### Step 2: Supabase Data Integrity
*   Ensure the `api_keys` table has a default `test_key_precision_3d_001` with `is_active=true`.
*   Verify that `DatabaseService` handles connection timeouts gracefully.

### Step 3: Global Exception Formatting
*   Ensure all 401/403 errors return a standard JSON structure: `{"error": {"message": "...", "code": 403}}`. This prevents the "Uncaught in Promise" crashes on the frontend.

---

## 3. Implementation Tasks

### [Backend Security]
#### [main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)
- Explicitly add `X-API-Key` to `allow_headers`.
- Add a diagnostic endpoint `/api/v2/debug-auth` to test key validity.

#### [api_key_auth.py](file:///Users/mac/ai-body-scan-saas/middleware/api_key_auth.py)
- Refactor to handle both `X-API-Key` header and an optional `apiKey` query parameter for easier debugging.

---

## 4. Verification Plan
1.  **Direct API Test**: Use `curl` to hit `/api/v2/health` with the header.
2.  **Auth Debug Test**: Hit `/api/v2/debug-auth` to confirm Supabase connectivity.
3.  **CORS Audit**: Verify that the browser console no longer shows header-related blocks.

**Protocol**: Every file change will be immediately committed and pushed to GitHub.
