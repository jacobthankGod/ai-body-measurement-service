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
        # Verify SSH key
        if [ ! -f "$SSH_KEY" ]; then
            echo "ERROR: SSH key not found at $SSH_KEY"
            exit 1
        fi
        # Copy files
        scp -i "$SSH_KEY" "$LOCAL_DIR/server.py" "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/server.py"
        scp -i "$SSH_KEY" "$(dirname "$0")/../scripts/garment_proxy_health_check.sh" "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/health_check.sh"
        # Restart service
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" "sudo systemctl restart garment-proxy"
        sleep 3
        # Verify health
        ssh -i "$SSH_KEY" "$REMOTE_USER@$EC2_IP" << 'VERIFY'
            echo "=== Service Status ==="
            sudo systemctl is-active garment-proxy
            echo "=== Health Check ==="
            curl -sf --max-time 5 http://127.0.0.1:8001/api/v2/garment/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "FAILED"
            echo "=== Recent Logs ==="
            sudo journalctl -u garment-proxy --no-pager -n 10
VERIFY
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
