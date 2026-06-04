"""
API Key Authentication Middleware
=========================
"""
import json
from pathlib import Path
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
DATA_DIR = Path(__file__).parent.parent / "data"

def load_api_keys():
    keys_file = DATA_DIR / "api_keys.json"
    if keys_file.exists():
        with open(keys_file) as f:
            return json.load(f)
    return {}

async def validate_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    keys = load_api_keys()
    if api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key
