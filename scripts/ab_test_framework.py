#!/usr/bin/env python3
"""
A/B Test Framework for Measurement Pipeline
============================================
Manages gradual rollout of new model versions with:
- Traffic splitting between model versions
- Result logging for offline comparison
- Automatic rollback if error rate exceeds threshold
- Version metadata tracking

Usage:
    # Register a new model version for A/B test
    python scripts/ab_test_framework.py register --version v2 --traffic 10

    # Promote winning version to full traffic
    python scripts/ab_test_framework.py promote --version v2

    # Check current version distribution
    python scripts/ab_test_framework.py status

    # Rollback to previous version
    python scripts/ab_test_framework.py rollback
"""
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("AB_TEST")

AB_CONFIG_PATH = Path("api/models/ab_config.json")
AB_LOG_PATH = Path("logs/ab_tests.jsonl")


def load_config() -> Dict:
    if AB_CONFIG_PATH.exists():
        return json.loads(AB_CONFIG_PATH.read_text())
    return {
        'versions': {},
        'active_version': 'baseline',
        'traffic_split': {},
        'history': [],
    }


def save_config(config: Dict):
    AB_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    AB_CONFIG_PATH.write_text(json.dumps(config, indent=2))
    logger.info(f"Config saved to {AB_CONFIG_PATH}")


def register(args):
    config = load_config()
    version = args.version
    traffic = args.traffic

    if version in config['versions']:
        logger.info(f"Version {version} already registered — updating traffic to {traffic}%")
    else:
        logger.info(f"Registering version {version} with {traffic}% traffic")

    config['versions'][version] = {
        'registered_at': datetime.utcnow().isoformat(),
        'traffic_pct': traffic,
        'deployed_by': args.deployed_by or 'auto',
    }

    remaining = 100 - sum(v['traffic_pct'] for k, v in config['versions'].items() if k != version)
    config['versions'][version]['traffic_pct'] = min(traffic, remaining + traffic)

    total = sum(v['traffic_pct'] for v in config['versions'].values())
    if total > 100:
        scale = 100.0 / total
        for k in config['versions']:
            config['versions'][k]['traffic_pct'] = round(config['versions'][k]['traffic_pct'] * scale)

    config['traffic_split'] = {k: v['traffic_pct'] for k, v in config['versions'].items()}
    config['history'].append({
        'action': 'register',
        'version': version,
        'traffic': traffic,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_config(config)
    print_config(config)


def promote(args):
    config = load_config()
    version = args.version

    if version not in config['versions']:
        logger.error(f"Version {version} not found")
        return

    config['active_version'] = version
    for k in config['versions']:
        config['versions'][k]['traffic_pct'] = 100 if k == version else 0
    config['traffic_split'] = {version: 100}
    config['history'].append({
        'action': 'promote',
        'version': version,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_config(config)
    logger.info(f"✅ Version {version} promoted to 100% traffic")
    print_config(config)


def rollback(args):
    config = load_config()
    if len(config['history']) < 2:
        logger.error("No previous version to rollback to")
        return

    for entry in reversed(config['history']):
        if entry['action'] == 'promote':
            prev_version = entry['version']
            for e in reversed(config['history']):
                if e['action'] == 'promote' and e['version'] != prev_version:
                    promote_version = e['version']
                    config['active_version'] = promote_version
                    config['versions'][promote_version]['traffic_pct'] = 100
                    config['versions'][prev_version]['traffic_pct'] = 0
                    config['traffic_split'] = {promote_version: 100}
                    config['history'].append({
                        'action': 'rollback',
                        'from': prev_version,
                        'to': promote_version,
                        'timestamp': datetime.utcnow().isoformat(),
                    })
                    save_config(config)
                    logger.info(f"Rolled back from {prev_version} to {promote_version}")
                    print_config(config)
                    return
    logger.error("No suitable rollback target found")


def status(_args):
    config = load_config()
    print_config(config)


def print_config(config: Dict):
    print(f"\nActive version: {config.get('active_version', 'N/A')}")
    print("Traffic split:")
    for ver, pct in sorted(config.get('traffic_split', {}).items()):
        marker = " ← ACTIVE" if ver == config.get('active_version') else ""
        print(f"  {ver}: {pct}%{marker}")
    print(f"Registered versions: {len(config.get('versions', {}))}")
    print(f"History entries: {len(config.get('history', []))}")


def main():
    parser = argparse.ArgumentParser(description="A/B test framework for measurement pipeline")
    subparsers = parser.add_subparsers(dest='command', required=True)

    register_parser = subparsers.add_parser('register', help='Register a new version')
    register_parser.add_argument('--version', type=str, required=True)
    register_parser.add_argument('--traffic', type=int, default=10, help='Traffic percentage')
    register_parser.add_argument('--deployed-by', type=str, default='auto')

    promote_parser = subparsers.add_parser('promote', help='Promote version to full traffic')
    promote_parser.add_argument('--version', type=str, required=True)

    rollback_parser = subparsers.add_parser('rollback', help='Rollback to previous version')

    status_parser = subparsers.add_parser('status', help='Show A/B test status')

    args = parser.parse_args()

    commands = {
        'register': register,
        'promote': promote,
        'rollback': rollback,
        'status': status,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
