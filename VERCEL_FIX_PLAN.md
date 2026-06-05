# Absolute Fix Plan: Vercel 500 & Integrity Restoration

I have performed a deep audit of the Vercel logs and the codebase. We have a "Perfect Storm" of three issues causing the `FUNCTION_INVOCATION_FAILED`.

## 1. Root Cause Diagnosis

### Issue A: Infinite Recursion (Critical)
In `api/main.py`, the endpoint `extract_measurements` imports a function as `extract_logic` but then accidentally calls **itself** (`await extract_measurements(request)`). This causes a Stack Overflow / Crash.

### Issue B: Event Loop Conflict
The `subscription_check.py` is using `loop.run_until_complete()` inside a sync function. In a running FastAPI/Vercel environment, this often triggers `RuntimeError: This event loop is already running`.

### Issue C: Dependency Bloat
Vercel has a **250MB limit**. Our current `requirements.txt` includes TensorFlow and MediaPipe (~1.2GB total). Vercel is failing to initialize the environment because the package is too large.

---

## 2. The "Perfect & Functional" Strategy

### Step 1: Fix the Recursion
Rename the lazy-loaded functions in `api/main.py` to ensure they call the external logic, not themselves.

### Step 2: Fully Async Middleware
Refactor `subscription_check.py` and `measurements.py` to be fully `async`. This removes the dangerous `run_until_complete` calls.

### Step 3: Dual-Requirement System
- **requirements.txt (Lean)**: Optimized for Vercel (< 250MB).
- **requirements.docker.txt (Full)**: Unlocked with all "Crucial" models for Local/Render/Railway.

---

## 3. Implementation Tasks

### [Bug Fixes]
- [ ] **[api/main.py](file:///Users/mac/ai-body-scan-saas/api/main.py)**: Fix recursion and standardize CORS.
- [ ] **[subscription_check.py](file:///Users/mac/ai-body-scan-saas/middleware/subscription_check.py)**: Convert to fully async.
- [ ] **[measurements.py](file:///Users/mac/ai-body-scan-saas/api/routes/measurements.py)**: Update to use async user validation.

### [Dependency Management]
- [ ] **[requirements.txt](file:///Users/mac/ai-body-scan-saas/requirements.txt)**: Lean version for Vercel stability.
- [ ] **[requirements.docker.txt](file:///Users/mac/ai-body-scan-saas/requirements.docker.txt)**: Full "Crucial" version.

---

## 4. Verification Plan
1. **GitHub Push**: Every file change will be immediately pushed.
2. **Local Startup**: Run `uvicorn api.main:app` to verify no recursion.
3. **Vercel Deploy**: Verify the build succeeds under 250MB.

**Protocol**: Push update to github after every edit.
