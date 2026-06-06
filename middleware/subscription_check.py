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
    'enterprise': 999999,
}

async def validate_subscription(api_key):
    """Asynchronously validate subscription."""
    if not api_key:
        return {'valid': False, 'error': 'API key required'}

    # --- ADMIN OVERDRIVE BYPASS (Phase 3) ---
    # Any key starting with 'korra_admin_' or matching the MASTER_KEY has infinite credits.
    master_key = os.environ.get("PRECISIONFIT_MASTER_KEY")
    if (master_key and api_key == master_key) or api_key.startswith("korra_admin_"):
        return {'valid': True, 'tier': 'enterprise', 'is_admin': True}

    # Query database for standard merchant keys
    key_data = await DatabaseService.get_api_key(api_key)
    
    if not key_data:
        return {'valid': False, 'error': 'Invalid API key'}
    
    tier = key_data.get('tier', 'tailor_basic')
    quota = SUBSCRIPTION_QUOTAS.get(tier, 0)

    # Note: In Phase 8, this will check 'usage_logs' table against 'quota'
    if quota == 0:
        return {'valid': False, 'error': f'AI Body Scan not included in {tier} plan'}

    return {'valid': True, 'tier': tier}

async def track_usage(api_key):
    """Asynchronously track API usage."""
    if not api_key:
        return
    # Skip tracking for admin keys
    if api_key.startswith("korra_admin_"):
        return
    await DatabaseService.update_usage(api_key)
