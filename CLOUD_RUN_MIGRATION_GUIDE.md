# Cloud Run Migration Guide: Zero-Cost Configuration
## Migrating to a Fresh Google Account to Eliminate $15+/Month Bills

---

## Executive Summary

This guide provides step-by-step instructions to migrate your Cloud Run deployment from your current billing account to a fresh Google Cloud Platform (GCP) account. The goal is to achieve **$0/month** billing through proper instance configuration.

### Why You're Being Billed $15+/Month

1. **Idle Instance Allocation**: Cloud Run defaults to keeping instances "warm" if min-instances is set to 1 or higher
2. **Streaming Bandwidth**: Large 3D assets (OBJ files, PNG textures, MediaPipe WASM binaries) being served repeatedly without CDN caching
3. **Always-On CPU**: Running with CPU allocation set to "Always" instead of "During request only"

---

## Phase 1: New GCP Project Setup

### Step 1.1: Create New GCP Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left) → **"New Project"**
3. Enter project name: `korra-zero-cost` (or your preferred name)
4. Note the **Project ID** (e.g., `korra-zero-cost-12345`)

### Step 1.2: Enable Required APIs

In the Google Cloud Console for the new project:

1. **Cloud Run API**:
   - Navigate to: APIs & Services → Library
   - Search: "Cloud Run API" → Enable

2. **Artifact Registry API**:
   - Search: "Artifact Registry API" → Enable

3. **Container Analysis API** (optional, for vulnerability scanning):
   - Search: "Container Analysis API" → Enable

### Step 1.3: Set Up Billing (Free Tier)

1. Go to **Billing** → Link a billing account
2. **IMPORTANT**: Set up billing alerts at $5 and $10 to catch unexpected charges
3. Enable **Free Tier** alerts in billing preferences

---

## Phase 2: Container Migration to Artifact Registry

### Step 2.1: Configure Docker for New Project

```bash
# Install Google Cloud SDK if not installed
# https://cloud.google.com/sdk/docs/install

# Authenticate with the NEW account
gcloud auth login

# Set the new project as active
gcloud config set project YOUR_NEW_PROJECT_ID

# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 2.2: Tag and Push Docker Image

First, get your existing image from the old account:

```bash
# List existing images in old project's Artifact Registry
gcloud config set project OLD_PROJECT_ID
gcloud artifacts docker images list us-central1-docker.pkg.dev/OLD_PROJECT_ID/korra

# Pull the existing image to local machine
gcloud artifacts docker pull us-central1-docker.pkg.dev/OLD_PROJECT_ID/korra/app:latest

# Tag for the new registry
gcloud artifacts docker tag \
    us-central1-docker.pkg.dev/OLD_PROJECT_ID/korra/app:latest \
    us-central1-docker.pkg.dev/YOUR_NEW_PROJECT_ID/korra/app:latest

# Push to new Artifact Registry
gcloud artifacts docker push us-central1-docker.pkg.dev/YOUR_NEW_PROJECT_ID/korra/app:latest
```

### Alternative: Rebuild from Source (Recommended)

```bash
# Clone your repository (if using Git)
git clone https://github.com/YOUR_ORG/ai-body-scan-saas.git
cd ai-body-scan-saas

# Build the Docker image
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_NEW_PROJECT_ID/korra/app:latest .
```

---

## Phase 3: Zero-Cost Cloud Run Deployment

### Step 3.1: Deploy with Zero-Cost Configuration

This is the **MOST IMPORTANT** step. Use these exact settings:

```bash
gcloud run deploy korra-app \
    --image us-central1-docker.pkg.dev/YOUR_NEW_PROJECT_ID/korra/app:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --session-affinity \
    --cpu-boost \
    --min-instances 0 \
    --max-instances 5 \
    --cpu-only-during-request \
    --port 8080
```

### Step 3.2: Verify Zero-Cost Settings via Console

1. Go to [cloud.google.com/run](https://cloud.google.com/run)
2. Select your new project
3. Click on the service **"korra-app"**
4. Check these settings in the **Configuration** tab:

| Setting | Value | Reason |
|---------|-------|--------|
| **Minimum instances** | 0 | Prevents idle billing |
| **Maximum instances** | 5 | Prevents runaway scaling |
| **CPU allocation** | CPU is only allocated during request processing | **KEY SAVINGS** |
| **Scaling** | Enable CPU boost for faster startup | Optional |

### Step 3.3: Confirm Container Port

Your Dockerfile already has `ENV PORT=8080`, which is correct for Cloud Run. Ensure your uvicorn command uses `${PORT}`:

```dockerfile
# From your existing Dockerfile - this is correct
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
```

---

## Phase 4: Environment Variables Setup

### Step 4.1: Identify Required Environment Variables

Your application uses these environment variables (from api/config.py and auth.py):

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (if needed) | Supabase Dashboard → Settings → API |
| `CORS_ORIGINS` | Allowed CORS origins | Comma-separated list |
| `BREVO_API_KEY` | Email sending API key | Brevo Dashboard |
| `VERCEL` | Set to "0" for Cloud Run | Set to "0" |
| `RENDER` | Set empty for Cloud Run | Leave empty |

### Step 4.2: Set Environment Variables in Cloud Run

```bash
# Set each environment variable
gcloud run deploy korra-app \
    --update-env-vars SUPABASE_URL=https://YOUR_PROJECT.supabase.co,SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Or via Console:
1. Go to Cloud Run service → **Edit & Deploy New Revision**
2. Expand **"Container, Networking, Security"**
3. Add Environment Variables in the form

### Step 4.3: Verify Supabase Configuration

If you're **keeping the same Supabase project**, the existing `SUPABASE_URL` and `SUPABASE_ANON_KEY` will work.

If you're **moving to a new Supabase project**:
1. Create new Supabase project
2. Run your SQL setup scripts
3. Update `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Cloud Run

---

## Phase 5: Supabase Auth Update (CRITICAL)

### Step 5.1: Update Site URL for Google Sign-In

If you're using Supabase Auth with Google Sign-In:

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project → **Authentication** → **Providers** → **Google**
3. Look for **"Site URL"** in settings
4. **UPDATE** this to your new Cloud Run URL: `https://korra-app-XXXXXXXX.us-central1.run.app`

### Why This Is Critical

If you don't update the Site URL:
- Google Sign-In will fail with redirect URI mismatch
- Users cannot log in
- OAuth flow will be broken

### Step 5.2: Update Authorized Redirect URIs

In Google Cloud Console (for the new project):
1. Go to **APIs & Services** → **Credentials**
2. Click on your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://YOUR_NEW_PROJECT.supabase.co/auth/v1/callback
   ```
4. Add to **Authorized JavaScript origins**:
   ```
   https://korra-app-XXXXXXXX.us-central1.run.app
   ```

---

## Phase 6: DNS and Custom Domain (Optional)

### Step 6.1: Map Custom Domain

If you're using a custom domain (e.g., `api.korra.work`):

```bash
gcloud run domain-mappings create \
    --service korra-app \
    --domain api.korra.work
```

### Step 6.2: Verify DNS Settings

1. Get the SSL certificate after mapping:
   ```bash
   gcloud run domain-mappings describe api.korra.work
   ```

2. Update your DNS A/CNAME records with your domain registrar

---

## Phase 7: Cost Optimization Checklist

### Verify These Settings to Ensure $0/Month

- [ ] **Min instances = 0** (not 1 or higher)
- [ ] **Max instances = 5** (prevents runaway costs)
- [ ] **CPU allocation = "During request only"** (not "Always")
- [ ] **No CPU always allocated** (check Cloud Console)

### Additional Optimizations

1. **Serve Static Assets from CDN** instead of Cloud Run:
   - Upload `.obj`, `.png`, `.js` files to Supabase Storage or Vercel
   - Use Cloud Run ONLY for AI processing

2. **Configure CDN Caching**:
   ```bash
   # Set up Cloud CDN with Cloud Load Balancing
   gcloud compute backend-services create korra-backend \
       --protocol HTTP2 \
       --enable-cdn
    
   gcloud compute url-maps create korra-url-map \
       --default-service korra-backend
   ```

---

## Phase 8: Testing the Migration

### Step 8.1: Functional Test Script

```bash
# Test the new endpoint
curl -X POST https://korra-app-XXXXXXXX.us-central1.run.app/api/measurements/extract \
    -H "Content-Type: application/json" \
    -d '{"image_url": "https://example.com/test-image.jpg"}'
```

### Step 8.2: Verify Zero Cost

1. Wait 24-48 hours after deployment
2. Go to **Billing** → **Cloud Run** costs
3. Confirm charges are $0.00 or minimal (few cents for egress)

### Step 8.3: Monitor for Idle Billing

Set up a Google Cloud Billing alert:
1. Go to **Billing** → **Budgets & alerts**
2. Create budget at $1.00
3. Set alert at 50%, 90%, 100%

---

## Troubleshooting

### Problem: Still Getting Billed

**Check:**
1. Is `min-instances` set to 0? (not 1)
2. Is CPU allocation set to "During request only"?
3. Do you have any other services running?

### Problem: Google Sign-In Broken

**Fix:**
1. Update Site URL in Supabase Dashboard
2. Update Authorized redirect URIs in Google Cloud Console
3. Update CORS_ORIGINS environment variable

### Problem: 502 Bad Gateway

**Fix:**
1. Check container health: `gcloud run revisions describe korra-app-XXXXX`
2. Check logs: `gcloud logging read "resource.type=cloud_run_revision"`
3. Verify PORT environment variable is set to 8080

---

## Quick Reference: Commands

```bash
# Deploy with zero-cost config
gcloud run deploy korra-app \
    --image us-central1-docker.pkg.dev/PROJECT_ID/korra/app:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 5 \
    --cpu-only-during-request \
    --port 8080

# Update environment variables
gcloud run deploy korra-app \
    --update-env-vars SUPABASE_URL=https://XXX.supabase.co,SUPABASE_ANON_KEY=XXX

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.service korra-app" --limit 50

# Get service URL
gcloud run services describe korra-app --format="get(status.url)"
```

---

## Migration Timeline

| Phase | Time | Notes |
|-------|------|-------|
| 1. New GCP Project | 10 minutes | Enable APIs |
| 2. Container Migration | 15-30 minutes | Build + push |
| 3. Deploy & Configure | 10 minutes | Zero-cost settings |
| 4. Environment Variables | 5 minutes | Set variables |
| 5. Supabase Auth Update | 5 minutes | Critical for auth |
| 6. Testing | 30 minutes | Full functional test |
| **Total** | **~1.5 hours** | |

---

## After Migration: Cost Monitoring

### Set Up Monthly Alerts

1. Go to **Billing** → **Budgets & alerts**
2. Create budget: $0.50
3. Alert thresholds: 50%, 90%, 100%

### Set Up Daily Cost Check

```bash
# Add to crontab for daily check
0 0 * * * gcloud billing budgets list --format="get(budget)" && echo "Check costs"
```

---

## Important Notes

1. **Free Tier**: New GCP accounts get 180 days of free tier, including 180,000 vCPU-seconds and 360,000 GiB-seconds of Cloud Run
2. **Egress**: Outbound data transfer may incur charges; keep static assets on CDN
3. **Cold Starts**: With min-instances=0, expect ~10-30 second cold start on first request

---

## Need Help?

If you encounter issues:
1. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Verify all environment variables are set correctly
3. Ensure Supabase Site URL matches your Cloud Run URL

Good luck with your zero-cost migration! 🚀
