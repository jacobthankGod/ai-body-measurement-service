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

def validate_subscription(api_key):
    """
    Unified API key validation.
    ALL keys (merchant, admin, publishable) are looked up in the api_keys table.
    Admin bypass (korra_admin_* / PRECISIONFIT_MASTER_KEY) still works for
    development but returns no user_id, so persistence is skipped.
    """
    if not api_key:
        return {'valid': False, 'error': 'API key required'}

    master_key = os.environ.get("PRECISIONFIT_MASTER_KEY")
    is_admin = (master_key and api_key == master_key) or api_key.startswith("korra_admin_")

    # All keys go through api_keys table — single source of truth
    key_data = DatabaseService.get_api_key(api_key)

    if not key_data:
        if is_admin:
            return {'valid': True, 'tier': 'enterprise', 'is_admin': True}
        return {'valid': False, 'error': 'Invalid API key'}

    user_id = key_data.get('user_id')
    tier = key_data.get('tier', 'tailor_basic')
    quota = SUBSCRIPTION_QUOTAS.get(tier, 0)

    if quota == 0 and not is_admin:
        return {'valid': False, 'error': f'AI Body Scan not included in {tier} plan'}

    return {'valid': True, 'tier': tier, 'is_admin': is_admin, 'user_id': user_id}

def track_usage(api_key):
    """Asynchronously track API usage."""
    if not api_key:
        return
    # Skip tracking for admin keys
    if api_key.startswith("korra_admin_"):
        return
    DatabaseService.update_usage(api_key)

async def check_and_decrement_credits(user_id: str):
    """Verifies user has credits and decrements 1. Returns True if successful."""
    client = DatabaseService.get_client()
    try:
        res = client.table("profiles").select("credits").eq("id", user_id).single().execute()
        credits = res.data.get('credits', 0) if res.data else 0

        if credits > 0:
            client.table("profiles").update({"credits": credits - 1}).eq("id", user_id).execute()
            return True
        return False
    except: return False

async def refund_credit(user_id: str):
    """Adds 1 credit back to the user account (Phase 20 Refund Protocol)."""
    client = DatabaseService.get_client()
    try:
        res = client.table("profiles").select("credits").eq("id", user_id).single().execute()
        credits = res.data.get('credits', 0) if res.data else 0
        client.table("profiles").update({"credits": credits + 1}).eq("id", user_id).execute()
        return True
    except: return False


def get_user_quota(api_key: str):
    """
    Get user quota information for a given API key.
    Returns tier, quota, used, remaining, and reset_date.
    """
    if not api_key:
        return {'valid': False, 'error': 'API key required'}
    
    # Check for admin keys
    master_key = os.environ.get("PRECISIONFIT_MASTER_KEY")
    if (master_key and api_key == master_key) or api_key.startswith("korra_admin_"):
        return {
            'valid': True,
            'tier': 'enterprise',
            'quota': 999999,
            'used': 0,
            'remaining': 999999,
            'reset_date': None
        }
    
    # Get key data from database
    key_data = DatabaseService.get_api_key(api_key)
    if not key_data:
        return {'valid': False, 'error': 'Invalid API key'}
    
    tier = key_data.get('tier', 'tailor_basic')
    quota = SUBSCRIPTION_QUOTAS.get(tier, 0)
    
    # Get usage stats (approximated for now)
    client = DatabaseService.get_client()
    try:
        res = client.table("usage_logs").select("id").eq("api_key", api_key).execute()
        used = len(res.data) if res.data else 0
    except:
        used = 0
    
    remaining = max(0, quota - used)
    
    # Calculate reset date (first of next month)
    now = datetime.now()
    if now.month == 12:
        reset_date = datetime(now.year + 1, 1, 1).strftime('%Y-%m-%d')
    else:
        reset_date = datetime(now.year, now.month + 1, 1).strftime('%Y-%m-%d')
    
    return {
        'valid': True,
        'tier': tier,
        'quota': quota,
        'used': used,
        'remaining': remaining,
        'reset_date': reset_date
    }


def get_usage_stats(api_key: str):
    """
    Get usage statistics for a given API key.
    Returns this_month and total usage counts.
    """
    if not api_key:
        return {'this_month': 0, 'total': 0}
    
    # Check for admin keys
    if api_key.startswith("korra_admin_"):
        return {'this_month': 0, 'total': 0}
    
    client = DatabaseService.get_client()
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1).isoformat()
    
    try:
        # Get this month's usage
        res_month = client.table("usage_logs").select("id").eq("api_key", api_key).gte("created_at", start_of_month).execute()
        this_month = len(res_month.data) if res_month.data else 0
        
        # Get total usage
        res_total = client.table("usage_logs").select("id").eq("api_key", api_key).execute()
        total = len(res_total.data) if res_total.data else 0
    except:
        this_month = 0
        total = 0
    
    return {
        'this_month': this_month,
        'total': total
    }
