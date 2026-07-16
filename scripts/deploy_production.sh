#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Phase 213: Production Deploy Script
# ═══════════════════════════════════════════════════════════════
# Full deployment workflow for KORRA Garment Platform.
#
# Usage:
#   ./scripts/deploy_production.sh [command]
#
# Commands:
#   deploy     - Full deploy (default): git pull, migrate, build, restart
#   frontend   - Deploy frontend assets only (faster)
#   proxy      - Deploy proxy server only
#   migrate    - Run database migrations only
#   status     - Check all services health
#   rollback   - Rollback to previous version
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# ── Config ────────────────────────────────────────────────────
EC2_HOST="korra.work"
EC2_USER="ubuntu"
EC2_KEY="$HOME/Downloads/korra-ai-key.pem"
EC2_DIR="/home/ubuntu"
PROXY_DIR="$EC2_DIR/garment-proxy"
CONTAINER_NAME="korra-ai-prod"
SUPABASE_DB_URL="${SUPABASE_DB_URL:-postgresql://postgres:J@c0b@$$#&12345@db.blsettabymllulsxtziw.supabase.co:5432/postgres}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="/tmp/korra_deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"; }
ok() { echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOG_FILE"; exit 1; }

ssh_ec2() {
    ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$@"
}

scp_ec2() {
    scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$@"
}

# ═══ COMMANDS ═════════════════════════════════════════════════

cmd_deploy() {
    log "Starting full production deploy..."
    echo ""

    # Step 1: Git pull
    log "Step 1/7: Pulling latest code..."
    cd "$REPO_DIR"
    git pull origin main 2>&1 | tee -a "$LOG_FILE"
    ok "Code updated"

    # Step 2: Run migrations
    log "Step 2/7: Running database migrations..."
    cmd_migrate
    ok "Migrations complete"

    # Step 3: Deploy frontend assets
    log "Step 3/7: Deploying frontend assets..."
    cmd_frontend
    ok "Frontend deployed"

    # Step 4: Deploy proxy
    log "Step 4/7: Deploying proxy server..."
    cmd_proxy
    ok "Proxy deployed"

    # Step 5: Verify health
    log "Step 5/7: Verifying health..."
    sleep 3
    cmd_status
    ok "Health verified"

    # Step 6: Sync cell4_code.py to Kaggle
    log "Step 6/7: Syncing cell4_code.py..."
    sync_cell4

    # Step 7: Summary
    echo ""
    log "═══════════════════════════════════════════"
    log "  DEPLOY COMPLETE"
    log "═══════════════════════════════════════════"
    log "  Frontend:    https://korra.work"
    log "  Proxy:       https://korra.work/api/v2/garment/health"
    log "  Dashboard:   https://korra.work/api/v2/garment/quality/dashboard"
    log "  Log:         $LOG_FILE"
    log "═══════════════════════════════════════════"
}

cmd_frontend() {
    log "Deploying frontend assets to EC2..."
    ssh_ec2 "sudo docker cp $REPO_DIR/public/assets/measurement-screen.js $CONTAINER_NAME:/app/public/assets/measurement-screen.js"
    ssh_ec2 "sudo docker cp $REPO_DIR/public/assets/measurement-screen.css $CONTAINER_NAME:/app/public/assets/measurement-screen.css"
    ssh_ec2 "sudo docker cp $REPO_DIR/public/assets/korra_export.js $CONTAINER_NAME:/app/public/assets/korra_export.js"
    ssh_ec2 "sudo docker cp $REPO_DIR/dashboard.html $CONTAINER_NAME:/app/dashboard.html"
    ok "Frontend assets synced"
}

cmd_proxy() {
    log "Deploying proxy server to EC2..."
    scp_ec2 "$REPO_DIR/garment-proxy/server.py" "$EC2_USER@$EC2_HOST:$PROXY_DIR/server.py"
    scp_ec2 "$REPO_DIR/scripts/garment_proxy_health_check.sh" "$EC2_USER@$EC2_HOST:$PROXY_DIR/health_check.sh"
    ssh_ec2 "sudo systemctl restart garment-proxy"
    sleep 2
    # Verify proxy is running
    if ssh_ec2 "sudo systemctl is-active garment-proxy" | grep -q "active"; then
        ok "Proxy restarted and active"
    else
        warn "Proxy may not be running — check journalctl -u garment-proxy"
    fi
}

cmd_migrate() {
    log "Running database migrations..."
    for sql in "$REPO_DIR"/scripts/00*.sql; do
        local name=$(basename "$sql")
        log "  Running $name..."
        PGPASSWORD='J@c0b@$$#&12345' psql "$SUPABASE_DB_URL" -f "$sql" 2>&1 | tee -a "$LOG_FILE" || true
    done
    ok "Migrations applied"
}

cmd_status() {
    log "Checking service health..."
    echo ""

    # Proxy health
    local proxy_health
    proxy_health=$(curl -s -w "\n%{http_code}" "https://korra.work/api/v2/garment/health" 2>/dev/null || echo "000")
    local proxy_code=$(echo "$proxy_health" | tail -1)
    local proxy_body=$(echo "$proxy_health" | head -1)
    if [ "$proxy_code" = "200" ]; then
        ok "Proxy: healthy (HTTP $proxy_code)"
    else
        warn "Proxy: unhealthy (HTTP $proxy_code)"
    fi

    # Tunnel check
    local tunnel_resp
    tunnel_resp=$(curl -s "https://korra.work/api/v2/garment/tunnel-url" 2>/dev/null || echo "{}")
    if echo "$tunnel_resp" | grep -q "trycloudflare.com"; then
        ok "Tunnel: registered"
    else
        warn "Tunnel: NOT registered (Kaggle may be down)"
    fi

    # Cost usage
    local cost_resp
    cost_resp=$(curl -s "https://korra.work/api/v2/garment/cost/usage" 2>/dev/null || echo "{}")
    log "Cost: $cost_resp"

    echo ""
}

cmd_rollback() {
    log "Rolling back to previous version..."
    cd "$REPO_DIR"
    local prev=$(git log --oneline -2 | tail -1 | awk '{print $1}')
    if [ -z "$prev" ]; then
        fail "No previous commit found"
    fi
    log "Rolling back to $prev..."
    git checkout "$prev" 2>&1 | tee -a "$LOG_FILE"
    cmd_deploy
    git checkout main 2>&1 | tee -a "$LOG_FILE"
    ok "Rollback complete"
}

sync_cell4() {
    log "Syncing cell4_code.py with api_server.py..."
    cp "$REPO_DIR/kaggle-garment-backend/api_server.py" "$REPO_DIR/kaggle-garment-backend/cell4_code.py"
    ok "cell4_code.py synced"
}

# ═══ MAIN ═════════════════════════════════════════════════════
COMMAND="${1:-deploy}"

case "$COMMAND" in
    deploy)   cmd_deploy ;;
    frontend) cmd_frontend ;;
    proxy)    cmd_proxy ;;
    migrate)  cmd_migrate ;;
    status)   cmd_status ;;
    rollback) cmd_rollback ;;
    sync)     sync_cell4 ;;
    *)
        echo "Usage: $0 {deploy|frontend|proxy|migrate|status|rollback|sync}"
        exit 1
        ;;
esac
