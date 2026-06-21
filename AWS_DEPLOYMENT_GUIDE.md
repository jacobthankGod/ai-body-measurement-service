# AWS Deployment Guide
## Best Free Options for Your Docker-Based AI Body Scanning App

---

## Recommendation: Amazon EC2 (T3.micro)

For your AI body scanning app with MediaPipe and ML libraries, **Amazon EC2 T3.micro** is the best choice:

| Factor | EC2 T3.micro | Lambda | Lightsail |
|--------|-------------|--------|-----------|
| **Docker Support** | ✅ Full | ❌ Limited | ✅ Full |
| **ML Libraries** | ✅ All fit | ❌ Too large | ✅ All fit |
| **Free Hours** | 750 hrs/mo | 400K GB-seconds | ❌ $5/mo |
| **Persistence** | ✅ Easy | ❌ Ephemeral | ✅ Easy |
| **Best For** | Your app | Simple APIs | Beginners |

---

## Phase 1: AWS Account Setup

### Step 1.1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **Create an account**
3. Enter email and password
4. Enter account name (e.g., "KORRA AI")
5. Enter credit card info (required for identity, but won't be charged if within Free Tier)
6. Verify phone number
7. Select **Basic Plan** (free)

### Step 1.2: Navigate to EC2

1. Log into [console.aws.amazon.com](https://console.aws.amazon.com)
2. Search for **EC2** in the search bar
3. Click **EC2** → **Instances**
4. Click **Launch instances**

---

## Phase 2: Launch EC2 T3.micro

### Step 2.1: Configure Instance

In the EC2 Launch wizard:

| Setting | Value | Notes |
|---------|-------|-------|
| **Name** | `korra-ai-server` | Your server name |
| **Amazon Machine Image (AMI)** | `Ubuntu Server 22.04 LTS` | Free tier eligible |
| **Instance Type** | `t3.micro` | 2 vCPU, 1 GiB RAM - FREE |
| **Key Pair** | Create new | Download .pem file for SSH |

### Step 2.2: Configure Storage

| Setting | Value | Notes |
|---------|-------|-------|
| **Root Volume** | 30 GiB | Default, free tier eligible |
| **Volume Type** | gp3 (General Purpose SSD) | Free tier includes 30 GiB |

### Step 2.3: Configure Security Group

Create a new security group with these rules:

| Rule | Type | Port | Source |
|------|------|------|--------|
| SSH | TCP | 22 | My IP |
| HTTP | TCP | 80 | Anywhere |
| HTTPS | TCP | 443 | Anywhere |
| Custom TCP | TCP | 8080 | Anywhere (for your app) |

### Step 2.4: Launch

Click **Launch Instance** and wait 2-3 minutes for the instance to start.

---

## Phase 3: Connect to EC2

### Step 3.1: Get Instance Public IP

1. Go to EC2 → Instances
2. Select your `korra-ai-server`
3. Copy the **Public IPv4 address** (e.g., `54.123.45.67`)

### Step 3.2: SSH into Server

Mac/Linux:
```bash
chmod 400 korra-ai-key.pem
ssh -i korra-ai-key.pem ubuntu@54.123.45.67
```

Windows (PowerShell):
```powershell
ssh -i korra-ai-key.pem ubuntu@54.123.45.67
```

---

## Phase 4: Install Docker on EC2

### Step 4.1: Update and Install Dependencies

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Add current user to docker group
sudo usermod -aG docker ubuntu

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker
```

### Step 4.2: Verify Docker

```bash
# Check Docker version
docker --version

# Run test container
docker run hello-world
```

---

## Phase 5: Deploy Your AI Body Scan App

### Option A: Pull from Existing Registry

If you already have your Docker image pushed to a registry (Docker Hub, Google Artifact Registry, etc.):

```bash
# Login to your registry (if private)
docker login

# Pull your image
docker pull your-registry/korra-ai:latest

# Run the container
docker run -d \
  --name korra-ai \
  -p 8080:8080 \
  -e SUPABASE_URL=https://yourproject.supabase.co \
  -e SUPABASE_ANON_KEY=your_anon_key \
  -e SUPABASE_SERVICE_ROLE_KEY=your_service_key \
  --restart unless-stopped \
  your-registry/korra-ai:latest
```

### Option B: Build from Source

Clone and build on EC2:

```bash
# Install Git and clone your repo
sudo apt install -y git
git clone https://github.com/jacobthankGod/ai-body-measurement-service.git
cd ai-body-measurement-service

# Build the Docker image
docker build -t korra-ai:latest .

# Run the container
docker run -d \
  --name korra-ai \
  -p 8080:8080 \
  -e SUPABASE_URL=https://yourproject.supabase.co \
  -e SUPABASE_ANON_KEY=your_anon_key \
  -e SUPABASE_SERVICE_ROLE_KEY=your_service_key \
  -e PORT=8080 \
  --restart unless-stopped \
  korra-ai:latest
```

---

## Phase 6: Keep App Running (Production)

### Step 6.1: Set Up Systemd Service

Create a systemd service for automatic restart:

```bash
# Create service file
sudo nano /etc/systemd/system/korra.service
```

Add this content:

```ini
[Unit]
Description=KORRA AI Body Scan Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ai-body-scan-saas
ExecStartPre=/usr/bin/docker pull your-registry/korra-ai:latest
ExecStart=/usr/bin/docker run --name korra-ai -p 8080:8080 \
  -e SUPABASE_URL=https://yourproject.supabase.co \
  -e SUPABASE_ANON_KEY=your_anon_key \
  -e SUPABASE_SERVICE_ROLE_KEY=your_service_key \
  -e PORT=8080 \
  --restart unless-stopped \
  your-registry/korra-ai:latest
ExecStop=/usr/bin/docker stop korra-ai
ExecStopPost=/usr/bin/docker rm korra-ai
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable korra
sudo systemctl start korra
```

### Step 6.2: Set Up Automatic Updates

Add a cron job to pull latest images daily:

```bash
# Edit crontab
crontab -e
```

Add:

```
0 3 * * * docker pull your-registry/korra-ai:latest && docker restart korra-ai
```

---

## Phase 7: Domain & SSL (Optional)

### Step 7.1: Point Domain to EC2

1. Go to your domain registrar (Namecheap, GoDaddy, etc.)
2. Create an **A Record**:
   - Host: `api` (or `@` for root)
   - Value: Your EC2 Public IP (`54.123.45.67`)
   - TTL: 3600 (1 hour)

### Step 7.2: Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts to enter email and agree to terms

# Auto-renewal is automatic
```

---

## Phase 8: Zero-Billing Configuration

To ensure you don't get charged:

### Step 8.1: Use T3.micro Only

- T3.micro is in the Free Tier (750 hours/month)
- Don't upgrade to larger instance types

### Step 8.2: Set Up Billing Alerts

1. Go to [console.aws.amazon.com/billing](https://console.aws.amazon.com/billing)
2. Click **Budgets** → **Create budget**
3. Set:
   - **Budget name**: `korra-ai`
   - **Amount**: $5
   - **Alert threshold**: 50%, 80%, 100%
4. Enter your email for alerts

### Step 8.3: Use CloudWatch for Auto-Start/Stop (Advanced)

To save even more, stop the EC2 when not in use:

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure AWS credentials (from IAM user)
aws configure

# Create start/stop script (optional - to save on non-free hours)
```

---

## Environment Variables Reference

Your app needs these variables:

| Variable | Where to Find | Example |
|----------|---------------|---------|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API | `https://xyz.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API | `eyJhbGciOiJIUz...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API | `eyJhbGciOiJIUz...` |
| `PORT` | Set to `8080` | `8080` |
| `PYTHONUNBUFFERED` | Set to `1` | `1` |

---

## Important: Update Supabase Auth

After deployment, update your auth settings:

1. Go to Supabase Dashboard → Authentication → Providers → Google
2. Update **Site URL** to your EC2 URL: `http://54.123.45.67:8080` (or your domain)
3. In Google Cloud Console, update:
   - **Authorized redirect URIs**
   - **Authorized JavaScript origins**

---

## Troubleshooting

### Issue: Can't Connect to EC2

- Check Security Group rules (enable port 22 for SSH, 8080 for app)
- Verify instance is "Running" state
- Check your IP in the SSH rule

### Issue: App Won't Start

- Check logs: `docker logs korra-ai`
- Verify environment variables are set correctly
- Check port isn't already in use: `docker ps`

### Issue: High Bill

- Never upgrade beyond t3.micro
- Set up billing alerts
- Only use when needed (or use Lambda for occasional workloads)

---

## Cost Summary

| Component | AWS Service | Free Tier | Cost |
|-----------|-------------|-----------|------|
| Server | EC2 t3.micro | 750 hrs/mo | $0 |
| Transfer | Data Transfer | 15 GB/mo | $0 |
| Storage | EBS | 30 GB | $0 |
| Domain (optional) | Route 53 | $12/year | ~$0 |
| **Total** | | | **$0/mo** |

**Note**: If you exceed Free Tier limits, costs are minimal:
- EC2 t3.micro: ~$0.01/hour ($7.30/month)
- Data transfer: ~$0.09/GB

---

## Quick Summary: Commands

```bash
# 1. SSH into server
ssh -i korra-ai-key.pem ubuntu@54.123.45.67

# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Run your app
docker run -d \
  --name korra-ai \
  -p 8080:8080 \
  -e SUPABASE_URL=https://xxx.supabase.co \
  -e SUPABASE_ANON_KEY=xxx \
  -e PORT=8080 \
  --restart unless-stopped \
  your-registry/korra-ai:latest

# 4. Check logs
docker logs -f korra-ai

# 5. Check app health
curl http://localhost:8080/health
```

---

## Migration Checklist

- [ ] Create AWS account (with credit card)
- [ ] Launch EC2 t3.micro instance
- [ ] Configure security group (ports 22, 80, 443, 8080)
- [ ] SSH and install Docker
- [ ] Deploy your Docker image
- [ ] Set environment variables (Supabase keys)
- [ ] Test the app
- [ ] Update Supabase Site URL
- [ ] Set up billing alerts
- [ ] (Optional) Set up domain + SSL

Good luck with your AWS deployment!
