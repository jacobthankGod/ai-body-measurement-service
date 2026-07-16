#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Phase 237: Frontend Deploy Script
# ═══════════════════════════════════════════════════════════════
# Deploys frontend assets (JS, CSS, export) to EC2 production.
#
# Usage:
#   ./scripts/deploy_frontend.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

EC2_HOST="korra.work"
EC2_USER="ubuntu"
EC2_KEY="$HOME/Downloads/korra-ai-key.pem"
CONTAINER_NAME="korra-ai-prod"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

ssh_ec2() {
    ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$@"
}

scp_ec2() {
    scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$@"
}

# ── Step 1: Copy files to EC2 ──────────────────────────────────
log "Copying frontend assets to EC2..."

scp_ec2 "$REPO_DIR/public/assets/measurement-screen.js" "$EC2_USER@$EC2_HOST:/tmp/measurement-screen.js"
scp_ec2 "$REPO_DIR/public/assets/measurement-screen.css" "$EC2_USER@$EC2_HOST:/tmp/measurement-screen.css"
scp_ec2 "$REPO_DIR/public/assets/korra_export.js" "$EC2_USER@$EC2_HOST:/tmp/korra_export.js"

# ── Step 2: Copy into running container ─────────────────────────
log "Copying into Docker container..."

ssh_ec2 "sudo docker cp /tmp/measurement-screen.js $CONTAINER_NAME:/app/public/assets/measurement-screen.js && \
         sudo docker cp /tmp/measurement-screen.css $CONTAINER_NAME:/app/public/assets/measurement-screen.css && \
         sudo docker cp /tmp/korra_export.js $CONTAINER_NAME:/app/public/assets/korra_export.js"

ok "Assets copied into container"

# ── Step 3: Verify files are served ────────────────────────────
log "Verifying assets are served..."

JS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://korra.work/assets/measurement-screen.js")
CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://korra.work/assets/measurement-screen.css")
EXPORT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://korra.work/assets/korra_export.js")

if [ "$JS_STATUS" = "200" ] && [ "$CSS_STATUS" = "200" ] && [ "$EXPORT_STATUS" = "200" ]; then
    ok "All assets verified (JS=$JS_STATUS, CSS=$CSS_STATUS, Export=$EXPORT_STATUS)"
else
    fail "Asset verification failed (JS=$JS_STATUS, CSS=$CSS_STATUS, Export=$EXPORT_STATUS)"
fi

# ── Step 4: Verify content freshness ───────────────────────────
JS_LINES=$(curl -s "https://korra.work/assets/measurement-screen.js" | wc -l)
CSS_LINES=$(curl -s "https://korra.work/assets/measurement-screen.css" | wc -l)
JS_LOCAL_LINES=$(wc -l < "$REPO_DIR/public/assets/measurement-screen.js")
CSS_LOCAL_LINES=$(wc -l < "$REPO_DIR/public/assets/measurement-screen.css")

log "Remote JS: $JS_LINES lines (local: $JS_LOCAL_LINES)"
log "Remote CSS: $CSS_LINES lines (local: $CSS_LOCAL_LINES)"

if [ "$JS_LINES" -eq "$JS_LOCAL_LINES" ] && [ "$CSS_LINES" -eq "$CSS_LOCAL_LINES" ]; then
    ok "Content freshness verified"
else
    echo -e "${RED}[WARN]${NC} Line count mismatch — cache may need clearing"
fi

echo ""
ok "Frontend deploy complete"
