#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Deploy / Manage Garment Reconstruction Proxy on EC2
# Usage:
#   ./deploy.sh              — push code + restart service
#   ./deploy.sh launch       — launch new EC2 instance with bootstrap
#   ./deploy.sh restart      — restart the service
#   ./deploy.sh logs         — tail proxy logs
#   ./deploy.sh status       — check health
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

EC2_IP="${EC2_IP:-13.60.215.88}"
SSH_KEY="${SSH_KEY:-/Users/mac/Downloads/korra-ai-key.pem}"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/garment-proxy"
LOCAL_DIR="$(dirname "$0")"

# ── Commands ───────────────────────────────────────────────────
case "${1:-deploy}" in
    deploy|"")
        echo "=== Deploying proxy to EC2 ==="
        scp -i "$SSH_KEY" "$LOCAL_DIR/server.py" "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/server.py"
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo systemctl restart garment-proxy"
        sleep 2
        echo "=== Service restarted ==="
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo journalctl -u garment-proxy --no-pager -n 5"
        ;;

    launch)
        echo "=== Launching new EC2 instance ==="
        # Use user-data to auto-bootstrap
        BOOTSTRAP=$(cat "$LOCAL_DIR/bootstrap.sh")
        echo "Instance will auto-configure on first boot."
        echo "Run: aws ec2 run-instances --user-data file://$LOCAL_DIR/bootstrap.sh ..."
        echo "Or paste bootstrap.sh content into EC2 launch wizard > Advanced > User Data."
        ;;

    restart)
        echo "=== Restarting proxy service ==="
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo systemctl restart garment-proxy"
        sleep 2
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo journalctl -u garment-proxy --no-pager -n 5"
        ;;

    logs)
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo journalctl -u garment-proxy -f --no-pager"
        ;;

    status)
        echo "=== Proxy Health ==="
        curl -s "https://korra.work/api/v2/garment/health" | python3 -m json.tool 2>/dev/null || echo "Failed to reach proxy"
        echo ""
        echo "=== EC2 Service Status ==="
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo systemctl is-active garment-proxy" 2>/dev/null || echo "Cannot reach EC2"
        ;;

    *)
        echo "Usage: $0 {deploy|launch|restart|logs|status}"
        exit 1
        ;;
esac
