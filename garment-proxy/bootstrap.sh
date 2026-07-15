#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# EC2 Bootstrap Script — Garment Reconstruction Proxy
# Runs on every instance launch via cloud-init user-data.
# Zero manual intervention required.
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

LOG="/var/log/garment-bootstrap.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== Garment Proxy Bootstrap: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# ── Config ─────────────────────────────────────────────────────
REPO_URL="https://github.com/YOUR_USERNAME/ai-body-scan-saas.git"  # Update this
REPO_DIR="/home/ubuntu/ai-body-scan-saas"
PROXY_DIR="/home/ubuntu/garment-proxy"
SERVICE_NAME="garment-proxy"
SUPABASE_URL="https://blsettabymllulsxtziw.supabase.co"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsc2V0dGFieW1sbHVsc3h0eml3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAwNTY3NjksImV4cCI6MjA5NTYzMjc2OX0.PuMsTbgyRRcCQ04Y7Y9Y75WjRqmzgMP4S2_B4372V_U"

# ── System deps ────────────────────────────────────────────────
apt-get update -qq
apt-get install -y -qq python3 python3-pip nginx jq curl > /dev/null 2>&1 || true

# ── Python deps ────────────────────────────────────────────────
pip3 install --break-system-packages -q fastapi uvicorn httpx python-multipart 2>/dev/null || \
pip3 install -q fastapi uvicorn httpx python-multipart

# ── Clone/pull repo ───────────────────────────────────────────
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR" && git pull --quiet
else
    git clone --quiet "$REPO_URL" "$REPO_DIR" 2>/dev/null || true
fi

# ── Copy proxy code ────────────────────────────────────────────
mkdir -p "$PROXY_DIR"
cp "$REPO_DIR/garment-proxy/server.py" "$PROXY_DIR/server.py"

# ── Systemd service ────────────────────────────────────────────
cat > /etc/systemd/system/${SERVICE_NAME}.service << UNIT
[Unit]
Description=Garment Reconstruction Proxy
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${PROXY_DIR}
ExecStart=/usr/bin/python3 ${PROXY_DIR}/server.py
Restart=always
RestartSec=5
Environment=KAGGLE_TUNNEL_URL=
Environment=SUPABASE_URL=${SUPABASE_URL}
Environment=SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

# ── Nginx config ───────────────────────────────────────────────
if ! grep -q 'api/v2/garment' /etc/nginx/sites-enabled/korra 2>/dev/null; then
    sed -i '/# End of server block/i\
\
# Garment reconstruction proxy\
location /api/v2/garment/ {\
    proxy_pass http://127.0.0.1:8001;\
    proxy_set_header Host \$host;\
    proxy_set_header X-Real-IP \$remote_addr;\
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\
    proxy_set_header X-Forwarded-Proto \$scheme;\
    proxy_buffering off;\
    proxy_read_timeout 180s;\
    client_max_body_size 20M;\
    add_header Access-Control-Allow-Origin *;\
    add_header Access-Control-Allow-Methods "POST, GET, OPTIONS";\
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";\
}' /etc/nginx/sites-enabled/korra
    nginx -t && systemctl reload nginx
fi

echo "=== Bootstrap complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "Tunnel URL will be auto-registered by Kaggle keep-alive script."
