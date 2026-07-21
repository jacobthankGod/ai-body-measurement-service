#!/usr/bin/env bash
# deploy_production.sh — Persistent deployment to EC2
# All files go to HOST-mounted volumes, not inside container.
# Survives container recreate/restart.
set -euo pipefail

# ── Config ──────────────────────────────────────────────────
EC2_HOST="${EC2_HOST:-ubuntu@13.60.215.88}"
EC2_KEY="${EC2_KEY:-$HOME/Downloads/korra-ai-key.pem}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

SSH="ssh -i $EC2_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $EC2_HOST"
SCP="scp -i $EC2_KEY -o StrictHostKeyChecking=no"

# ── Colors ──────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Pre-flight ──────────────────────────────────────────────
[ -f "$EC2_KEY" ] || err "SSH key not found: $EC2_KEY"
$SSH "echo ok" >/dev/null 2>&1 || err "Cannot reach EC2: $EC2_HOST"

# ── Parse args ──────────────────────────────────────────────
TARGET="${1:-all}"
# Targets: proxy | frontend | all

deploy_proxy() {
    log "Deploying proxy server.py..."
    $SCP "$PROJECT_DIR/garment-proxy/server.py" "$EC2_HOST:/tmp/server.py"
    $SSH "
        sudo cp /home/ubuntu/garment-proxy/server.py /home/ubuntu/garment-proxy/server.py.bak
        sudo cp /tmp/server.py /home/ubuntu/garment-proxy/server.py
        sudo systemctl restart garment-proxy
        sleep 2
        if sudo systemctl is-active --quiet garment-proxy; then
            echo 'Proxy: OK'
        else
            echo 'Proxy: FAILED — rolling back'
            sudo cp /home/ubuntu/garment-proxy/server.py.bak /home/ubuntu/garment-proxy/server.py
            sudo systemctl restart garment-proxy
            exit 1
        fi
    "
    log "Proxy deployed ✓"
}

deploy_frontend() {
    log "Deploying frontend to persistent host volume..."
    $SCP "$PROJECT_DIR/public/assets/measurement-screen.js" "$EC2_HOST:/home/ubuntu/app/public/assets/"
    $SCP "$PROJECT_DIR/public/assets/measurement-screen.css" "$EC2_HOST:/home/ubuntu/app/public/assets/"
    $SCP "$PROJECT_DIR/public/assets/korra_export.js" "$EC2_HOST:/home/ubuntu/app/public/assets/"
    $SSH "
        # Verify files exist on host volume
        wc -l /home/ubuntu/app/public/assets/measurement-screen.js \
              /home/ubuntu/app/public/assets/measurement-screen.css \
              /home/ubuntu/app/public/assets/korra_export.js
    "
    log "Frontend deployed ✓"
}

verify() {
    log "Verifying deployment..."
    $SSH "
        # Proxy health
        HEALTH=\$(curl -s http://localhost:8001/health)
        STATUS=\$(echo \$HEALTH | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"status\",\"unknown\"))' 2>/dev/null)
        echo \"Proxy health: \$STATUS\"

        # Docker container running
        STATUS=\$(sudo docker inspect korra-ai-prod --format '{{.State.Status}}' 2>/dev/null || echo 'not found')
        echo \"Container: \$STATUS\"

        # Frontend files in container (via volume mount)
        sudo docker exec korra-ai-prod wc -l /app/public/assets/measurement-screen.js \
            /app/public/assets/measurement-screen.css /app/public/assets/korra_export.js 2>/dev/null

        # Volume mounts
        sudo docker inspect korra-ai-prod --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' 2>/dev/null | grep assets
    "
    log "Verification complete ✓"
}

case "$TARGET" in
    proxy)   deploy_proxy ;;
    frontend) deploy_frontend ;;
    all)     deploy_proxy; deploy_frontend; verify ;;
    verify)  verify ;;
    *)       echo "Usage: $0 [proxy|frontend|all|verify]"; exit 1 ;;
esac
