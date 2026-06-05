"""
Subscription Routes
=================
"""
from fastapi import APIRouter, Header, HTTPException
from middleware.subscription_check import get_user_quota, get_usage_stats
from datetime import datetime

router = APIRouter()

TIER_FEATURES = {
    'tailor_basic': [],
    'tailor_pro': ['dual_scan', 'priority_queue'],
    'tailor_elite': ['dual_scan', 'priority_queue', 'analytics'],
    'enterprise': ['dual_scan', 'priority_queue', 'analytics', 'white_label']
}

@router.get("/subscriptions/status")
async def get_subscription_status(x_api_key: str = Header(None)):
    """Get subscription status for authenticated user."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    quota = get_user_quota(x_api_key)
    if not quota.get('valid'):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    usage = get_usage_stats(x_api_key)
    tier = quota.get('tier', 'tailor_basic')
    
    return {
        "tier": tier,
        "scans_used": usage['this_month'],
        "scans_remaining": quota.get('remaining', 0),
        "reset_date": quota.get('reset_date'),
        "features": TIER_FEATURES.get(tier, []),
        "usage": usage
    }
