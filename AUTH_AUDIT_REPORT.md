# AI Body Scan SaaS — Auth & API Key Audit Report

**Scope**
- Review whether users can sign in to create an **API key** for backend usage.
- Review required functionality/flows for **Sign Up / Sign In** and downstream **API key issuance**.
- Identify gaps between the current implementation and the expected “sign in → create API key” capability.

**Files inspected**
- `/Users/mac/ai-body-scan-saas/index.html` (new landing + Supabase auth)
- `/Users/mac/ai-body-scan-saas/api/main.py` (FastAPI entry point)
- `/Users/mac/ai-body-scan-saas/api/routes/*` (existing routers)

---

## 1. Frontend authentication (Supabase)

### What exists
`/Users/mac/ai-body-scan-saas/index.html` loads Supabase JS via CDN and uses:
- `supabase.auth.signUp({ email, password })`
- `supabase.auth.signInWithPassword({ email, password })`
- `persistSession: true` and session auto-refresh.

UI behavior:
- Sign In / Sign Up modals
- Signed-in top-right pill shows `session.user.email`

### What is missing / risks
1. **API key creation flow needs backend alignment**
   - The landing page includes an “API Keys” modal and calls a backend endpoint (`POST /api/v2/auth/api-keys`) using the Supabase access token.
   - The backend implementation must exist and must accept `Authorization: Bearer <supabase_access_token>`.

2. **Potential security gaps to review**
   - The backend verifies Supabase tokens via Supabase `/auth/v1/user` (requires correct Supabase configuration and network access).
   - API keys are stored in local JSON files (`api/data/api_keys.json` and `usage_log.json`). This is sufficient for development, but **not suitable** for production multi-instance deployments.


---

## 2) Backend authentication & API key issuance

### What exists in FastAPI routers
From current repo structure, FastAPI includes routers for:
- `api/routes/health.py`
- `api/routes/measurements.py`
- `api/routes/subscriptions.py`
- `api/routes/payments.py`

### What exists in FastAPI
- `api/main.py` includes `auth.router` under `prefix="/api/v2"`.
- `api/routes/auth.py` implements:
  - `POST /api/v2/auth/api-keys` (create)
  - `GET /api/v2/auth/api-keys` (list)
  - `DELETE /api/v2/auth/api-keys/{key_id}` (revoke)
  - `GET /api/v2/auth/me` (current user)

### What remains to verify / risks
1. **Supabase token verification path**
   - `api/routes/auth.py` verifies the access token by calling Supabase endpoint: `/auth/v1/user`.
   - This requires the Supabase URL/Anon key to be correct and network access from the runtime.

2. **Local JSON key store**
   - API keys and usage are stored in local files under `api/data/` (`api_keys.json`, `usage_log.json`).
   - This works for single-instance deployments, but breaks under horizontal scaling / serverless concurrency.


---

## 3) Measurements and API key requirements

### Observed behavior (based on existing docs/code patterns)
The system appears to use an `X-API-Key` header (commonly) for authenticated measurement usage.

### Gap
- There is no documented or implementable flow to generate that `X-API-Key` for a Supabase-authenticated user.

---

## 4) Required functionality checklist (expected)

### A. Sign up / sign in
✅ Present on frontend (Supabase auth).

### B. Session handling
✅ Present in frontend (persist + onAuthStateChange).

### C. Sign in → create API key
❌ Not present.
- Missing backend endpoint(s) to create API keys.
- Missing JWT verification and user identity mapping.

### D. Persist issued API key
❌ Not present (no backend auth/key store found in current router set).

### E. Use issued API key against measurement endpoints
⚠️ Possibly supported by `measurements` route (depends on implementation), but without key issuance, end-to-end flow fails.

---

## 5) Severity & Impact

- **Severity: High**
- **Impact: Users cannot obtain API credentials after signing in.**
- This blocks onboarding for developers and any productized access model.

---

## 6) Recommended implementation (high level)

### Backend
1. Add a new router (e.g. `api/routes/auth.py`) and include it in `api/main.py`.
2. Implement endpoints:
   - `POST /api/v2/auth/signup` (optional if you rely purely on Supabase)
   - `POST /api/v2/auth/apikeys` to create a key for the authenticated user
   - `GET /api/v2/auth/apikeys` to list keys
   - `DELETE /api/v2/auth/apikeys/{id}` to revoke
3. Validate Supabase JWT on protected routes:
   - Verify `Authorization: Bearer <access_token>` with Supabase public keys.
4. Persist API keys:
   - Store hashed key values and metadata (owner user id, created_at, last_used, revoked).

### Frontend
1. Add an “API Keys” section after sign-in.
2. Call the backend key creation endpoint using the Supabase access token.
3. Display the generated key once, securely.

---

## 7) Concrete next steps to proceed
1. Locate where API keys are currently expected/validated in `api/routes/measurements.py`.
2. Search for existing key storage models in:
   - `api/models/` and any DB integration.
3. Implement `auth` router + key issuance endpoints.
4. Add frontend UI + wiring for key generation.

---

**Status**: Incomplete end-to-end auth-to-API-key flow.

