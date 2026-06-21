# Free Docker Platform Migration Guide
## Zero-Cost Alternative to Cloud Run Billing Issues

---

## Why This Guide?

The error `[OR_BACR2_44]` indicates Google Cloud billing restrictions on your new account. This is a common issue when:
- Creating a new GCP project without verified billing
- Using a new Google account
- Account flags for fraud prevention

**Solution**: Use a platform that doesn't require billing verification - these platforms are 100% free with no credit card required:

| Platform | Free Tier | Docker Support | Cold Start | Best For |
|----------|-----------|----------------|------------|----------|
| **Railway** | $5/month credit | ✅ Full | ❌ None | Full ML apps |
| **Render** | 750 hours/month | ✅ Full | ⏱️ 30s | Web apps |
| **Fly.io** | 3 shared VMs | ✅ Full | ❌ None | Full apps |
| **Cyclic** | Unlimited requests | ⚠️ Limited | ❌ None | Simple APIs |

**Recommended**: Railway - it gives $5/month free credit (enough for your AI engine) and doesn't require billing verification.

---

## Option 1: Railway (Recommended - Easiest)

### Why Railway?
- $5/month free credit (plenty for your AI workload)
- No credit card required to start
- Full Docker support with persistent storage
- Automatic HTTPS
- Native Python support via Dockerfile

### Step 1.1: Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login (create account at railway.app)
railway login

# Initialize project
railway init

# Select "Docker" as the service type
# Enter project name: korra-ai
```

### Step 1.2: Configure railway.json

Create `railway.json` in your project root:

```json
{
  "build": {
    "builder": "Docker",
    "dockerfile_path": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 1.3: Set Environment Variables

```bash
# Set environment variables via CLI
railway variables set SUPABASE_URL=https://yourproject.supabase.co
railway variables set SUPABASE_ANON_KEY=your_anon_key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_service_key
railway variables set PORT=8080
```

Or via Railway Dashboard:
1. Go to [railway.app](https://railway.app)
2. Select your project → **Variables**
3. Add each environment variable

### Step 1.4: Deploy

```bash
# Deploy to Railway
railway up
```

### Step 1.5: Get Your URL

```bash
# Get the deployed URL
railway domain
```

Your app will be available at: `https://korra-ai-production.up.railway.app`

---

## Option 2: Render (Already Configured)

Your project already has `RENDER_DEPLOYMENT_GUIDE.md` with instructions.

### Quick Start for Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `korra-ai`
   - **Environment**: `Docker`
   - **Instance Type**: `Free`
5. Add Environment Variables:
   - `SUPABASE_URL`: your_supabase_url
   - `SUPABASE_ANON_KEY`: your_anon_key
   - `PORT`: `8080`
6. Click **Deploy Web Service**

### Important: Keep Alive Script (Required)

Render's free tier sleeps after 15 minutes. Add a keep-alive ping:

```python
# Create keep_alive.py
import schedule
import time
import requests

def ping_app():
    try:
        requests.get("https://your-app.onrender.com/health", timeout=5)
        print("Pinged app to keep awake")
    except:
        print("Ping failed")

# Run every 10 minutes
schedule.every(10).minutes.do(ping_app)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Add this as a separate background worker in Render.

---

## Option 3: Fly.io (Full Docker)

### Why Fly.io?
- 3 shared CPUs for free (generous)
- Full Docker support
- Global edge deployments
- No credit card on Hobby plan

### Step 3.1: Install Flyctl

```bash
# Install Fly CLI
brew install flyctl

# Login
fly auth login
```

### Step 3.2: Create Fly Configuration

```bash
# Initialize project
fly launch --image your-docker-image
```

This creates `fly.toml`. Configure it:

```toml
app = "korra-ai"

[build]
  image = "your-image"

[deploy]
  num_replicas = 1

[[services]]
  protocol = "http"
  internal_port = 8080

  [[services.ports]]
    port = 80
    handlers = ["http"]
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Step 3.3: Set Secrets

```bash
fly secrets set SUPABASE_URL=https://xxx.supabase.co
fly secrets set SUPABASE_ANON_KEY=xxx
```

### Step 3.4: Deploy

```bash
fly deploy
```

---

## Option 4: DenoDeploy (For Deno/Kotlin)

If you're open to using Deno instead of Python:
- **DenoDeploy** has a generous free tier
- Supports Python via Pyodide
- But requires rewriting Python code to JS/TS

Not recommended if you want to keep your Python codebase.

---

## Comparison: Which Is Best for Your AI Engine?

| Factor | Railway | Render | Fly.io |
|-------|---------|--------|-------|
| **Free Credit** | $5/month | 750 hrs/mo | 3 VMs |
| **ML Libraries** | ✅ Full | ⚠️ Limited | ✅ Full |
| **Cold Starts** | None | 30 sec | None |
| **Persistence** | ✅ Easy | ✅ Easy | ✅ Easy |
| **Setup Time** | 10 min | 15 min | 20 min |

**Railway is recommended because:**
1. Enough free compute for your AI engine ($5/month)
2. No cold starts (keeps your ML models loaded)
3. Simple billing (no credit card = no issues)
4. Native Docker support

---

## Environment Variables Needed (All Platforms)

Regardless of which platform you choose, you'll need these:

```
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_key_here
PORT=8080
PYTHONUNBUFFERED=1
VERCEL=0
RENDER=
```

To find these:
1. **Supabase**: Dashboard → Settings → API
2. **Environment**: Copy from your current Cloud Run configuration

---

## Architecture After Migration

### Frontend (Already Free)
- **Vercel**: Serves all HTML files (index.html, dashboard.html, etc.)
- Already configured with `vercel.json`
- Free tier: 100GB bandwidth/month

### Backend (Choose One)
- **Railway** ($5 free credit/mo): Full Python + MediaPipe
- **Render** (750 free hrs): Full Python + MediaPipe
- **Fly.io** (3 free VMs): Full Python + MediaPipe

### Database (Already Free)
- **Supabase**: Free tier has 500MB storage, 2GB bandwidth
- No changes needed

### Static Assets
- **Supabase Storage**: Serve .obj, .png files
- Already integrated

---

## Quick Migration: Step-by-Step

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **Login** → **Sign Up with GitHub**
3. Authorize Railway to access your GitHub repos

### Step 2: Connect Repository

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Select: `jacobthankGod/ai-body-measurement-service`
4. Select **Docker** as the builder

### Step 3: Add Variables

In Railway dashboard, add:
```
SUPABASE_URL = https://xxx.supabase.co
SUPABASE_ANON_KEY = xxx
PORT = 8080
```

### Step 4: Deploy

Click **Deploy** - Railway will:
1. Detect your Dockerfile
2. Build the container
3. Deploy to production

### Step 5: Update Supabase Auth

After getting your Railway URL (`https://korra-ai-production.up.railway.app`):

1. Go to Supabase Dashboard → Authentication → Providers → Google
2. Update **Site URL** to your new Railway URL
3. Update Google Cloud Console authorized redirect URIs

---

## Testing Your New Deployment

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Test measurement endpoint
curl -X POST https://your-app.railway.app/api/measurements/extract \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/test.jpg"}'
```

---

## Troubleshooting

### Issue: " billing account not verified" on Railway?
Railway doesn't require billing - if you see this, it's likely a different issue. Contact Railway support.

### Issue: Container crashes on startup?
- Check logs in Railway Dashboard → Deployments → View Logs
- Common fix: Set `PORT=8080` environment variable
- Your Dockerfile may need adjustment

### Issue: "No matching credential" for Docker?
Run:
```bash
railway login
docker logout
railway docker credentials
```

---

## Cost Summary

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | Vercel | Free |
| Backend (API) | Railway | Free ($5 credit) |
| Database | Supabase | Free |
| Static Assets | Supabase Storage | Free |
| **Total** | | **$0/month** |

This architecture is completely free and avoids all billing issues!

---

## Migration Checklist

- [ ] Create Railway account (use GitHub login)
- [ ] Deploy Docker image to Railway
- [ ] Set environment variables (SUPABASE_URL, ANON_KEY)
- [ ] Get Railway URL
- [ ] Update Supabase Site URL
- [ ] Update Google OAuth redirect URIs
- [ ] Test all endpoints
- [ ] Verify zero billing

Good luck!
