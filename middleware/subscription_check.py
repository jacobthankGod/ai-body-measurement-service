"""
Subscription Check Middleware
=========================
Validates API keys and tracks subscription usage.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

SUBSCRIPTION_QUOTAS = {
    'tailor_basic': 0,
    'tailor_pro': 10,
    'tailor_elite': 50,
    'enterprise': 200,
}

DATA_DIR = Path(__file__).parent.parent / "data"
API_KEYS_FILE = DATA_DIR / "api_keys.json"
USAGE_LOG_FILE = DATA_DIR / "usage_log.json"

DATA_DIR.mkdir(exist_ok=True)

for f in [API_KEYS_FILE, USAGE_LOG_FILE]:
    if not f.exists():
        f.write_text("{}")

def load_json(filepath):
    try:
        return json.loads(filepath.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filepath, data):
    filepath.write_text(json.dumps(data, indent=2))

def load_api_keys():
    return load_json(API_KEYS_FILE)

def save_api_keys(keys):
    save_json(API_KEYS_FILE, keys)

def load_usage_log():
    return load_json(USAGE_LOG_FILE)

def save_usage_log(log):
    save_json(USAGE_LOG_FILE, log)

def get_user_quota(api_key):
    """Get user's subscription tier and quota."""
    keys = load_api_keys()
    if api_key not in keys:
        return {'valid': False, 'error': 'Invalid API key'}
    
    tier = keys[api_key].get('tier', 'tailor_basic')
    quota = SUBSCRIPTION_QUOTAS.get(tier, 0)
    
    usage_log = load_usage_log()
    user_usage = usage_log.get(api_key, {})
    now = datetime.now()
    month_key = f"{now.year}-{now.month:02d}"
    used = user_usage.get('monthly', {}).get(month_key, 0)
    remaining = max(0, quota - used)
    
    reset_date = datetime(now.year, (now.month % 12) + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
    
    return {
        'valid': True,
        'tier': tier,
        'quota': quota,
        'used': used,
        'remaining': remaining,
        'reset_date': reset_date.isoformat()
    }

def validate_subscription(api_key):
    """Validate subscription for API access."""
    if not api_key:
        return {'valid': False, 'error': 'API key required', 'quota_exceeded': False}
    
    quota = get_user_quota(api_key)
    if not quota.get('valid'):
        return {'valid': False, 'error': quota.get('error'), 'quota_exceeded': False}
    
    if quota['quota'] == 0:
        return {'valid': False, 'error': f'AI Body Scan not included in {quota["tier"]} plan', 'quota_exceeded': True}
    
    if quota['remaining'] <= 0:
        return {'valid': False, 'error': 'Monthly scan quota exhausted', 'quota_exceeded': True}
    
    return {'valid': True, 'error': None, 'quota_exceeded': False, 'remaining': quota['remaining']}

def track_usage(api_key):
    """Track API usage."""
    if not api_key:
        return
    
    try:
        usage_log = load_usage_log()
        now = datetime.now()
        month_key = f"{now.year}-{now.month:02d}"
        day_key = now.strftime('%Y-%m-%d')
        
        if api_key not in usage_log:
            usage_log[api_key] = {'monthly': {}, 'daily': {}, 'total': 0, 'created': now.isoformat()}
        
        usage_log[api_key]['monthly'][month_key] = usage_log[api_key]['monthly'].get(month_key, 0) + 1
        usage_log[api_key]['daily'][day_key] = usage_log[api_key]['daily'].get(day_key, 0) + 1
        usage_log[api_key]['total'] += 1
        usage_log[api_key]['last_used'] = now.isoformat()
        
        save_usage_log(usage_log)
    except Exception as e:
        print(f"Failed to track usage: {e}")

def generate_api_key(user_id, tier='tailor_elite'):
    """Generate a new API key."""
    import hashlib, secrets
    raw_key = f"{user_id}_{datetime.now().isoformat()}_{secrets.token_hex(16)}"
    api_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32]
    
    keys = load_api_keys()
    keys[api_key] = {'user_id': user_id, 'tier': tier, 'created': datetime.now().isoformat(), 'active': True}
    save_api_keys(keys)
    return api_key

def get_usage_stats(api_key):
    """Get usage statistics."""
    usage_log = load_usage_log()
    if api_key not in usage_log:
        return {'total': 0, 'this_month': 0, 'this_week': 0, 'this_day': 0}
    
    user_usage = usage_log[api_key]
    now = datetime.now()
    month_key = f"{now.year}-{now.month:02d}"
    
    this_month = user_usage.get('monthly', {}).get(month_key, 0)
    week_start = now - timedelta(days=now.weekday())
    this_week = sum(c for d, c in user_usage.get('daily', {}).items() 
                if datetime.strptime(d, '%Y-%m-%d') >= week_start)
    today_key = now.strftime('%Y-%m-%d')
    this_day = user_usage.get('daily', {}).get(today_key, 0)
    
    return {'total': user_usage.get('total', 0), 'this_month': this_month, 'this_week': this_week, 'this_day': this_day}
