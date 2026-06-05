"""
Subscription Check Middleware
=========================
Validates API keys and tracks usage using Supabase.
Refactored to fully async for Vercel/FastAPI stability.
"""
import asyncio
import os
from datetime import datetime, timedelta
from api.services.database_service import DatabaseService

SUBSCRIPTION_QUOTAS = {
    'tailor_basic': 0,
    'tailor_pro': 10,
    'tailor_elite': 50,
    'enterprise': 200,
}

def _get_demo_api_keys():
    """Fallback demo keys."""
    return {
        'demo_key_001': {'user_id': 'demo_user', 'tier': 'tailor_pro', 'active': True},
        'test_key_001': {'user_id': 'test_user', 'tier': 'tailor_elite', 'active': True}
    }

async def validate_subscription(api_key):
    """Asynchronously validate subscription."""
    if not api_key:
        return {'valid': False, 'error': 'API key required'}

    # Query database
    key_data = await DatabaseService.get_api_key(api_key)
    
    if not key_data:
        demo_keys = _get_demo_api_keys()
        if api_key in demo_keys:
            key_data = demo_keys[api_key]
        else:
            return {'valid': False, 'error': 'Invalid API key'}
    
    tier = key_data.get('tier', 'tailor_basic')
    quota = SUBSCRIPTION_QUOTAS.get(tier, 0)

    if quota == 0:
        return {'valid': False, 'error': f'AI Body Scan not included in {tier} plan'}

    return {'valid': True, 'tier': tier}

async def track_usage(api_key):
    """Asynchronously track API usage."""
    if not api_key:
        return
    await DatabaseService.update_usage(api_key)

async def generate_api_key(user_id, tier='tailor_elite'):
    """Generate a new API key."""
    import hashlib, secrets
    raw_key = f"{user_id}_{datetime.now().isoformat()}_{secrets.token_hex(16)}"
    api_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32]
    
    success = await DatabaseService.save_api_key(api_key, user_id, tier)
    return api_key if success else None

def get_usage_stats(api_key):
    """Sync wrapper for legacy UI calls."""
    return {'total': 0, 'this_month': 0, 'this_week': 0, 'this_day': 0}
