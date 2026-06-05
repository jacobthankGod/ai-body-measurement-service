# Render.com Deployment Guide: Unrestricted AI Engine

Since Vercel's 250MB limit is causing crashes for your "Crucial" ML engine, we are moving to **Render.com**. Render provides a **Free Tier** that supports Docker, allowing us to run your full 1GB+ engine without limits.

## 🚀 Why Render?
1.  **No Package Size Limit**: Your TensorFlow and MediaPipe models will load perfectly.
2.  **Full System Support**: It includes the libraries needed for OpenCV and Image processing.
3.  **Automatic SSL**: You get a secure `https://...` URL for free.

---

## 🛠️ Step 1: Connect to Render
1.  Go to **[Dashboard.render.com](https://dashboard.render.com)**.
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository: `jacobthankGod/ai-body-measurement-service`.

## 🛠️ Step 2: Configure Service
-   **Name**: `ai-body-measurement`
-   **Environment**: `Docker` (Render will detect your Dockerfile automatically).
-   **Region**: `Frankfurt (EU)` or `Ohio (US East)`.
-   **Instance Type**: `Free`.

## 🛠️ Step 3: Add Environment Variables
Click **Advanced** -> **Add Environment Variable**:
-   `SUPABASE_URL`: (Your Supabase URL)
-   `SUPABASE_SERVICE_ROLE_KEY`: (Your Supabase Key)
-   `PORT`: `5001`
-   `PYTHONPATH`: `/app`

---

## ✅ Deployment Checklist
- [x] Dockerfile hardened for OpenCV/MediaPipe.
- [x] Full ML requirements in `requirements.txt`.
- [x] Persistent database (Supabase) integrated.

**Your SaaS is now ready for a crash-free, full-power deployment on Render!**
