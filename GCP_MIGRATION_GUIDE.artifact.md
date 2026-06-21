# KORRA | GCP Migration & Zero-Cost Cloud Run Guide
**Goal:** Migrate to a fresh account while minimizing billing to < $1.00/mo.

## 1. New Project Initialization
1.  **Create Project**: Go to [GCP Console](https://console.cloud.google.com/) and create `korra-production-v2`.
2.  **Enable APIs**:
    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com
    ```

## 2. Artifact Registry (The Image Vault)
1.  **Create Repository**:
    ```bash
    gcloud artifacts repositories create korra-repo --repository-format=docker --location=us-central1
    ```
2.  **Auth & Push**:
    ```bash
    # Build your local image (Includes all new .md files)
    docker build -t us-central1-docker.pkg.dev/[PROJECT_ID]/korra-repo/korra-api:latest .

    # Push to new account
    docker push us-central1-docker.pkg.dev/[PROJECT_ID]/korra-repo/korra-api:latest
    ```

## 3. The "Zero-Cost" Deployment
Deploy using these specific flags to avoid the $15+ idle billing:

```bash
gcloud run deploy korra-api \
  --image us-central1-docker.pkg.dev/[PROJECT_ID]/korra-repo/korra-api:latest \
  --location us-central1 \
  --min-instances 0 \
  --max-instances 5 \
  --cpu-throttling \
  --allow-unauthenticated
```

**Why this saves money:**
*   `--min-instances 0`: You pay $0 when nobody is using the site.
*   `--cpu-throttling`: CPU is only allocated during request processing. Cloud Run defaults to "Always On" which costs ~$15/mo per instance. **This is the fix.**

## 4. Environment Variables
Ensure these are set in the Cloud Run "Variables" tab:
*   `SUPABASE_URL`
*   `SUPABASE_ANON_KEY`
*   `PAYSTACK_PUBLIC_KEY`
*   `JWT_SECRET` (Match your Supabase secret)

## 5. CRITICAL: Supabase Redirect Sync
**If you do not do this, Google Sign-In will loop forever.**
1.  **Copy your new Cloud Run URL** (e.g., `https://korra-api-xyz.a.run.app`).
2.  **Go to Supabase Dashboard** -> `Authentication` -> `URL Configuration`.
3.  **Site URL**: Change this to your **new Cloud Run URL**.
4.  **Redirect URLs**: Add `[NEW_URL]/onboarding` and `[NEW_URL]/dashboard`.
