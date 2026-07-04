# Remote Update Guide: KORRA AI on AWS

Use this guide to push updates from your local computer to the AWS production server.

## 1. The "Standard" Update (Git-based)
Run this from your **local terminal** whenever you push new code to GitHub.

```bash
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 "~/update.sh && sudo systemctl reload nginx"
```

## 2. The "Large File" Update (SCP-based)
If you get an `Argument list too long` error, use **SCP** to transfer files directly.

```bash
# 1. Sync HTML files
scp -i ~/Downloads/korra-ai-key.pem index.html onboarding.html dashboard.html verification-success.html ubuntu@13.60.215.88:~/app/

# 2. Sync API logic
scp -i ~/Downloads/korra-ai-key.pem api/main.py ubuntu@13.60.215.88:~/app/api/

# 3. Restart Container
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 "~/update.sh"
```

---

## 3. Server Setup: `~/update.sh`
This script lives at `~/update.sh` on the EC2 instance. It automates the Docker lifecycle.

```bash
#!/bin/bash
echo "🚀 Starting Update Sequence..."
cd ~/app
git lfs install
git pull

echo "📦 Rebuilding Container..."
docker build -t korra-ai .

echo "♻️ Restarting Service..."
docker rm -f korra-ai-prod || true

# Auto-create .env if missing
if [ ! -f ~/app/.env ]; then
  cp ~/app/.env.example ~/app/.env
  echo "‼️ NEW .env CREATED. Please edit ~/app/.env with your keys."
fi

docker run -d \\
  --name korra-ai-prod \\
  -p 8080:8080 \\
  --env-file ~/app/.env \\
  -v /home/ubuntu/tailornet_data:/app/api/services/tailornet_data \\
  -v ~/app/public/meshes:/app/public/meshes \\
  --restart unless-stopped \\
  korra-ai:latest

echo "✅ Update Complete."
```

---

## 4. Troubleshooting SSL & Connectivity

### A. "Operation timed out"
**Fix**: Your laptop IP changed. Update the **SSH (Port 22)** rule in the AWS Security Group to "My IP".

### B. "Argument list too long"
**Fix**: Stop using `cat` and `ssh` to send file contents. Use the **SCP** method described in Section 2.

### C. "502 Bad Gateway"
This means Nginx is working, but the Docker app hasn't started.
**Fix**: Check if your `.env` file has the correct `PORT=8080` and run `~/update.sh`.

---

## 5. Post-Update Verification
1. **SSL Health**: Visit `https://korra.work`.
2. **API Health**: `https://korra.work/api/v2/health`
3. **Logs**: `docker logs -f korra-ai-prod`
