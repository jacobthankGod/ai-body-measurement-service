"""
Authentication & API Key Routes
=============================
Handles Supabase JWT validation and API key issuance.
"""
import json
import hashlib
import secrets
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Configuration - Load from environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://placeholder.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'placeholder_anon_key')

DATA_DIR = Path(__file__).parent.parent.parent / "data"
API_KEYS_FILE = DATA_DIR / "api_keys.json"
USAGE_LOG_FILE = DATA_DIR / "usage_log.json"

DATA_DIR.mkdir(exist_ok=True, parents=True)

# Ensure files exist (create empty structures)
for f in [API_KEYS_FILE, USAGE_LOG_FILE]:
    if not f.exists():
        if f.name.startswith('api_keys'):
            f.write_text("{}")
        else:
            f.write_text("{}")



# ============ Helper Functions ============

def load_json(filepath):
    """Load JSON file safely."""
    try:
        return json.loads(filepath.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filepath, data):
    """Save JSON file safely."""
    filepath.write_text(json.dumps(data, indent=2))

def load_api_keys() -> Dict:
    """Load all API keys from storage."""
    return load_json(API_KEYS_FILE)

def save_api_keys(keys: Dict):
    """Save API keys to storage."""
    save_json(API_KEYS_FILE, keys)

def load_usage_log() -> Dict:
    """Load usage log."""
    return load_json(USAGE_LOG_FILE)

def load_supabase_jwks():
    """Load Supabase JWKS for JWT verification."""
    jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        response = httpx.get(jwks_url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Failed to load JWKS: {e}")
    return None

async def verify_supabase_token(access_token: str) -> Optional[Dict]:
    """Verify Supabase access token and return user info."""
    if not access_token:
        return None
    
    # Verify with Supabase userinfo endpoint
    userinfo_url = f"{SUPABASE_URL}/auth/v1/user"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "apikey": SUPABASE_ANON_KEY
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Token verification failed: {e}")
    return None

def generate_api_key(user_id: str) -> str:
    """Generate a new API key."""
    raw_key = f"{user_id}_{datetime.now().isoformat()}_{secrets.token_hex(16)}"
    api_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32]
    return api_key

def create_api_key_for_user(user_id: str, email: str, tier: str = 'tailor_basic') -> Dict:
    """Create a new API key for user."""
    api_key = generate_api_key(user_id)
    now = datetime.now()
    
    keys = load_api_keys()
    keys[api_key] = {
        'key': api_key,
        'user_id': user_id,
        'email': email,
        'tier': tier,
        'quota': 10 if tier == 'tailor_pro' else 0,
        'used': 0,
        'created_at': now.isoformat(),
        'expires_at': None,
        'active': True
    }
    save_api_keys(keys)
    
    # Initialize usage log
    usage_log = load_usage_log()
    usage_log[api_key] = {
        'monthly': {},
        'daily': {},
        'total': 0,
        'created': now.isoformat()
    }
    save_json(USAGE_LOG_FILE, usage_log)
    
    return {
        'key': api_key,
        'created_at': now.isoformat(),
        'tier': tier
    }

def list_user_api_keys(user_id: str) -> List[Dict]:
    """List all API keys for a user."""
    keys = load_api_keys()
    user_keys = []
    
    for key, data in keys.items():
        if data.get('user_id') == user_id and data.get('active', True):
            user_keys.append({
                'id': key,
                'key_prefix': key[:8] + '****',
                'tier': data.get('tier'),
                'created_at': data.get('created_at'),
                'used': data.get('used', 0)
            })
    
    return user_keys

def revoke_api_key(user_id: str, key_id: str) -> bool:
    """Revoke an API key."""
    keys = load_api_keys()
    
    if key_id not in keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if keys[key_id].get('user_id') != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this key")
    
    keys[key_id]['active'] = False
    keys[key_id]['revoked_at'] = datetime.now().isoformat()
    save_api_keys(keys)
    
    return True


# ============ Routes ============

@router.post("/auth/api-keys")
async def create_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Create a new API key.
    
    Requires valid Supabase JWT token in Authorization header.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    access_token = credentials.credentials
    user = await verify_supabase_token(access_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = user.get('id')
    email = user.get('email') or user.get('email_confirm') or 'unknown'
    
    api_key_data = create_api_key_for_user(user_id, email)
    
    return {
        'success': True,
        'message': 'API key created successfully',
        'api_key': api_key_data['key'],
        'tier': api_key_data['tier'],
        'created_at': api_key_data['created_at'],
        'warning': 'Save this key securely - it will not be shown again'
    }

@router.get("/auth/api-keys")
async def list_api_keys(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    List all API keys for the authenticated user.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    access_token = credentials.credentials
    user = await verify_supabase_token(access_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = user.get('id')
    keys = list_user_api_keys(user_id)
    
    return {
        'success': True,
        'keys': keys,
        'count': len(keys)
    }

@router.delete("/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Revoke an API key.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    access_token = credentials.credentials
    user = await verify_supabase_token(access_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = user.get('id')
    revoke_api_key(user_id, key_id)
    
    return {
        'success': True,
        'message': f'API key {key_id[:8]}... revoked successfully'
    }

@router.get("/auth/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Get current authenticated user info.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    access_token = credentials.credentials
    user = await verify_supabase_token(access_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        'success': True,
        'user': {
            'id': user.get('id'),
            'email': user.get('email'),
            'email_confirmed': user.get('email_confirmed'),
            'created_at': user.get('created_at')
        }
    }
