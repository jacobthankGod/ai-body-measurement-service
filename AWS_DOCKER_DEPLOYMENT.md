# AWS EC2 Docker Deployment Guide: KORRA AI

This guide documents the final production setup for the KORRA AI body measurement platform on an AWS EC2 instance.

## 1. Infrastructure Architecture
*   **Instance**: `t3.micro` (1 vCPU, 1 GiB RAM).
*   **Storage**: 30 GiB gp3 (Required for Docker images and AI models).
*   **OS**: Ubuntu 24.04 LTS (Noble) or 22.04 LTS.
*   **Security Group Rules (CRITICAL)**:
    *   `SSH (22)`: Your Laptop IP (Must be updated whenever your IP changes).
    *   `HTTP (80)`: `0.0.0.0/0` (For SSL verification).
    *   `HTTPS (443)`: `0.0.0.0/0` (Production traffic).

## 2. Mandatory Server Hardening

### A. Swap Memory (Critical)
The AI inference engine requires more than 1GB of RAM. We must add 2GB of Swap to prevent "Out of Memory" crashes.
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### B. Core Dependencies
Install Docker, Nginx, Certbot, and Git LFS using the native package manager.
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
sudo apt install -y nginx certbot python3-certbot-nginx git-lfs
git lfs install
```

## 3. Nginx Reverse Proxy (The "Green Lock")
Nginx handles SSL and routes traffic from Port 443 to the Docker container on 8080.

### A. Config File: `/etc/nginx/sites-available/korra`
```nginx
server {
    listen 80;
    server_name korra.work www.korra.work;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### B. Activation
```bash
sudo ln -sf /etc/nginx/sites-available/korra /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# SSL Activation (Run after DNS is pointed to ONLY the server IP)
sudo certbot --nginx -d korra.work -d www.korra.work
```

## 4. Troubleshooting DNS Conflicts
If SSL activation fails with a 404, check if your domain has multiple A records.
```bash
host korra.work
```
Ensure **only** `13.60.215.88` is listed. Remove any old IP addresses (like `51.89.113.223`) from your domain registrar.

## 5. Known Production Configurations
*   **COOP/COEP Headers**: Set to `unsafe-none` in `api/main.py` for Paystack.
*   **Inference Throttling**: Limited to 1 concurrent task to protect the `t3.micro` CPU.
*   **Supabase Redirects**: "Site URL" in Supabase must be `https://korra.work`.
