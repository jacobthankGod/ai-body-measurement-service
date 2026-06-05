"""
Admin Routes
==========
Admin-only endpoints for dashboard and management.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

router = APIRouter()

# Simple API key protection (in production, use proper auth)
ADMIN_API_KEY = APIKeyHeader(name="X-API-Key", auto_error=False)

# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
API_KEYS_FILE = DATA_DIR / "api_keys.json"
USAGE_LOG_FILE = DATA_DIR / "usage_log.json"

# Ensure data files exist
DATA_DIR.mkdir(exist_ok=True)
for f in [API_KEYS_FILE, USAGE_LOG_FILE]:
    if not f.exists():
        f.write_text("{}")


# ============ Helpers ============

def load_json(filepath):
    try:
        return json.loads(filepath.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ============ Response Models ============

class StatsResponse(BaseModel):
    total_api_keys: int
    active_keys: int
    total_scans: int
    tier_breakdown: Dict[str, int]
    recent_activity: List[Dict]


# ============ Routes ============

@router.get("/admin/stats", response_model=StatsResponse)
async def get_admin_stats(api_key: str = Security(ADMIN_API_KEY)):
    """
    Get global statistics for admin dashboard.
    
    Requires X-API-Key header for authentication.
    """
    # Load data
    keys_data = load_json(API_KEYS_FILE)
    usage_log = load_json(USAGE_LOG_FILE)
    
    # Calculate stats
    total_api_keys = len(keys_data)
    active_keys = sum(1 for k in keys_data.values() if k.get('active', True))
    total_scans = sum(u.get('total', 0) for u in usage_log.values())
    
    # Tier breakdown
    tier_breakdown = {}
    for key, data in keys_data.items():
        tier = data.get('tier', 'unknown')
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
    
    # Recent activity (last 5 keys)
    recent_activity = []
    for key, data in list(keys_data.items())[:5]:
        recent_activity.append({
            'key_prefix': key[:8] + '****',
            'user_id': data.get('user_id', 'unknown'),
            'tier': data.get('tier', 'unknown'),
            'created_at': data.get('created_at'),
            'used': usage_log.get(key, {}).get('total', 0)
        })
    
    return {
        'total_api_keys': total_api_keys,
        'active_keys': active_keys,
        'total_scans': total_scans,
        'tier_breakdown': tier_breakdown,
        'recent_activity': recent_activity
    }


@router.get("/admin/api-keys")
async def get_all_api_keys(api_key: str = Security(ADMIN_API_KEY)):
    """
    Get all API keys (admin only).
    """
    keys_data = load_json(API_KEYS_FILE)
    usage_log = load_json(USAGE_LOG_FILE)
    
    all_keys = []
    for key, data in keys_data.items():
        usage = usage_log.get(key, {})
        all_keys.append({
            'id': key,
            'key_prefix': key[:8] + '****',
            'user_id': data.get('user_id', 'unknown'),
            'email': data.get('email', ''),
            'tier': data.get('tier', 'unknown'),
            'active': data.get('active', True),
            'created_at': data.get('created_at'),
            'used': usage.get('total', 0),
            'last_used': usage.get('last_used')
        })
    
    return {
        'keys': all_keys,
        'count': len(all_keys)
    }


@router.get("/admin/usage")
async def get_usage_logs(api_key: str = Security(ADMIN_API_KEY)):
    """
    Get usage logs (admin only).
    """
    usage_log = load_json(USAGE_LOG_FILE)
    
    return {
        'logs': usage_log,
        'count': len(usage_log)
    }
