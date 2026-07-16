#!/bin/bash
# ═══════════════════════════════════════════════════════
# KORRA Health Check Monitor
# Runs via cron every 5 minutes to check:
#   1. Garment proxy health endpoint
#   2. Kaggle tunnel connectivity
#   3. Logs results to /var/log/korra_health.log
#   4. Sends alert email on failure (configurable)
# ═══════════════════════════════════════════════════════
set -euo pipefail

# ── Configuration ──
PROXY_HOST="${PROXY_HOST:-http://127.0.0.1:8001}"
PROXY_TIMEOUT="${PROXY_TIMEOUT:-10}"
TUNNEL_CHECK_TIMEOUT="${TUNNEL_CHECK_TIMEOUT:-15}"
LOG_FILE="${LOG_FILE:-/var/log/korra_health.log}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
CHECK_INTERVAL=300  # 5 minutes

# ── Logging ──
log() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $1" | tee -a "$LOG_FILE"
}

# ── Ensure log file exists ──
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/korra_health.log"

# ── Alert function ──
send_alert() {
    local subject="$1"
    local body="$2"
    if [ -n "$ALERT_EMAIL" ] && command -v mail &>/dev/null; then
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
        log "ALERT SENT: $subject → $ALERT_EMAIL"
    elif [ -n "$ALERT_EMAIL" ] && command -v sendmail &>/dev/null; then
        {
            echo "Subject: $subject"
            echo "To: $ALERT_EMAIL"
            echo "Content-Type: text/plain"
            echo ""
            echo "$body"
        } | sendmail "$ALERT_EMAIL" 2>/dev/null || true
        log "ALERT SENT: $subject → $ALERT_EMAIL"
    else
        log "ALERT (no mail configured): $subject"
    fi
}

# ── Check 1: Proxy health endpoint ──
check_proxy() {
    local status_code
    status_code=$(curl -sf -o /dev/null -w '%{http_code}' --max-time "$PROXY_TIMEOUT" "$PROXY_HOST/api/v2/garment/health" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ]; then
        log "PROXY OK: $PROXY_HOST responded with $status_code"
        return 0
    else
        log "PROXY FAIL: $PROXY_HOST returned status $status_code"
        return 1
    fi
}

# ── Check 2: Kaggle tunnel connectivity ──
check_tunnel() {
    local tunnel_url
    tunnel_url=$(curl -sf --max-time "$PROXY_TIMEOUT" "$PROXY_HOST/api/v2/garment/tunnel-url" 2>/dev/null \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('active_url',''))" 2>/dev/null || echo "")

    if [ -z "$tunnel_url" ] || [ "$tunnel_url" = "not set" ]; then
        log "TUNNEL WARN: No tunnel URL registered (proxy may need Kaggle restart)"
        return 1
    fi

    # Probe the tunnel endpoint
    local tunnel_status
    tunnel_status=$(curl -sf -o /dev/null -w '%{http_code}' --max-time "$TUNNEL_CHECK_TIMEOUT" "$tunnel_url" 2>/dev/null || echo "000")

    if [ "$tunnel_status" = "200" ] || [ "$tunnel_status" = "404" ]; then
        log "TUNNEL OK: ${tunnel_url:0:60}... (HTTP $tunnel_status)"
        return 0
    else
        log "TUNNEL FAIL: ${tunnel_url:0:60}... returned HTTP $tunnel_status"
        return 1
    fi
}

# ── Main check loop ──
run_checks() {
    local proxy_ok=true
    local tunnel_ok=true
    local failures=()

    if ! check_proxy; then
        proxy_ok=false
        failures+=("proxy")
    fi

    if ! check_tunnel; then
        tunnel_ok=false
        failures+=("tunnel")
    fi

    # Summary
    if [ ${#failures[@]} -eq 0 ]; then
        log "HEALTH CHECK PASSED: proxy=ok tunnel=ok"
    else
        local fail_str
        fail_str=$(IFS=,; echo "${failures[*]}")
        log "HEALTH CHECK FAILED: ${fail_str}"
        send_alert \
            "[KORRA ALERT] Health check failed: ${fail_str}" \
            "KORRA health check failed at $(date '+%Y-%m-%d %H:%M:%S')

Failed components: ${fail_str}
Proxy: $PROXY_HOST
Log: $LOG_FILE

Recent log entries:
$(tail -10 "$LOG_FILE" 2>/dev/null)"
    fi
}

# ── Entry point ──
if [ "${1:-}" = "--once" ]; then
    run_checks
else
    log "Health monitor started (PID $$, interval ${CHECK_INTERVAL}s)"
    while true; do
        run_checks
        sleep "$CHECK_INTERVAL"
    done
fi
