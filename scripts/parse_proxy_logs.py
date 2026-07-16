#!/usr/bin/env python3
"""
Phase 7: Garment Proxy Log Parser

Parses journalctl output or log file for garment-proxy.
Extracts: request IDs, retry attempts, tunnel state changes, error clusters.

Usage:
  # From local machine via SSH:
  ssh -i ~/Downloads/korra-ai-key.pem ubuntu@13.60.215.88 "sudo journalctl -u garment-proxy --no-pager" | python3 scripts/parse_proxy_logs.py

  # From EC2 directly:
  sudo journalctl -u garment-proxy --no-pager | python3 parse_proxy_logs.py
"""
import re
import sys
from collections import defaultdict

LINE_RE = re.compile(
    r"\[(?P<req_id>[a-f0-9]{12})\]\s+(?P<msg>.*)"
)
TUNNEL_RE = re.compile(
    r"Tunnel URL (updated|pre-check)"
)
TIMEOUT_RE = re.compile(
    r"(Timeout|timeout)"
)
ERROR_RE = re.compile(
    r"(error|Error|ERROR|fail|Fail|FAIL|exception|Exception|EXCEPTION)"
)
HEALTH_RE = re.compile(
    r"/(api/v2/garment/)?health"
)

def parse_logs(lines):
    stats = {
        "total_lines": 0,
        "req_ids": set(),
        "requests_by_id": defaultdict(list),
        "tunnel_events": [],
        "health_checks": 0,
        "health_ok": 0,
        "errors": [],
        "attempts_by_req": defaultdict(int),
        "timeouts": 0,
        "warnings": [],
    }

    for line in lines:
        line = line.rstrip()
        stats["total_lines"] += 1

        # Extract req_id
        m = LINE_RE.search(line)
        if m:
            req_id = m.group("req_id")
            msg = m.group("msg")
            stats["req_ids"].add(req_id)
            stats["requests_by_id"][req_id].append(line)

            # Count attempts
            if "Attempt" in msg:
                stats["attempts_by_req"][req_id] += 1

        # Tunnel events
        if "Tunnel URL" in line:
            stats["tunnel_events"].append(line)

        # Health checks
        if HEALTH_RE.search(line):
            stats["health_checks"] += 1
            if "200" in line or "ALIVE" in line:
                stats["health_ok"] += 1

        # Errors
        if ERROR_RE.search(line):
            stats["errors"].append(line)

        # Timeouts
        if TIMEOUT_RE.search(line):
            stats["timeouts"] += 1

    return stats

def summarize(stats):
    print("=" * 60)
    print("Garment Proxy Log Analysis")
    print("=" * 60)
    print(f"Total log lines:           {stats['total_lines']}")
    print(f"Unique request IDs:        {len(stats['req_ids'])}")
    print(f"Tunnel events:             {len(stats['tunnel_events'])}")
    print(f"Health checks:             {stats['health_checks']}")
    print(f"  Healthy:                 {stats['health_ok']}")
    print(f"  Unhealthy:               {stats['health_checks'] - stats['health_ok']}")
    print(f"Total errors:              {len(stats['errors'])}")
    print(f"Timeouts:                  {stats['timeouts']}")
    print()

    # Per-request summary
    multi_attempt = {k: v for k, v in stats['attempts_by_req'].items() if v > 1}
    if multi_attempt:
        print("--- Requests requiring retries ---")
        for req_id, count in sorted(multi_attempt.items()):
            lines_for_req = stats['requests_by_id'][req_id]
            last_line = lines_for_req[-1] if lines_for_req else ""
            status = "OK" if "OK" in last_line or "completed" in last_line else "FAIL"
            print(f"  {req_id}: {count} attempts → {status}")
        print()

    # Error clusters
    if stats['errors']:
        print("--- Error lines (last 20) ---")
        for line in stats['errors'][-20:]:
            print(f"  {line}")
        print()

    # Tunnel history
    if stats['tunnel_events']:
        print("--- Tunnel events ---")
        for e in stats['tunnel_events']:
            print(f"  {e}")
        print()

    # Health ratio
    if stats['health_checks'] > 0:
        ok_ratio = stats['health_ok'] / stats['health_checks'] * 100
        print(f"Health success rate: {ok_ratio:.1f}% ({stats['health_ok']}/{stats['health_checks']})")

    print("=" * 60)

def main():
    lines = sys.stdin.readlines()
    if not lines:
        print("No input. Pipe journalctl output:\n  ssh ... | python3 parse_proxy_logs.py")
        return 1
    stats = parse_logs(lines)
    summarize(stats)
    return 0

if __name__ == "__main__":
    sys.exit(main())
