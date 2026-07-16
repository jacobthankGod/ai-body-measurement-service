#!/bin/bash
# Health check for Garment Proxy (used by systemd ExecStartPost or cron)
# Returns 0 if proxy is healthy, 1 if unhealthy.
set -euo pipefail

HOST="${1:-http://127.0.0.1:8001}"
TIMEOUT="${2:-5}"

# Check proxy health endpoint
if ! curl -sf --max-time "$TIMEOUT" "$HOST/api/v2/garment/health" > /dev/null 2>&1; then
    echo "HEALTH FAIL: Proxy at $HOST not responding"
    exit 1
fi

# Check that tunnel is registered
TUNNEL_URL=$(curl -sf --max-time "$TIMEOUT" "$HOST/api/v2/garment/tunnel-url" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('active_url',''))" 2>/dev/null || echo "")
if [ -z "$TUNNEL_URL" ] || [ "$TUNNEL_URL" = "not set" ]; then
    echo "HEALTH WARN: Proxy at $HOST has no tunnel URL registered"
    # Don't exit 1 — tunnel can register later via keep-alive
else
    echo "HEALTH OK: $HOST | Tunnel: ${TUNNEL_URL:0:50}..."
fi

exit 0
