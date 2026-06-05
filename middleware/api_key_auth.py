"""
API Key Authentication Middleware
=========================
"""
import json
import os
from pathlib import Path
from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from api.services.database_service import DatabaseService

# Support both header and query param for maximum compatibility
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(request: Request, api_key: str = Security(API_KEY_HEADER)):
    # 1. Check header first
    key = api_key
    
    # 2. Fallback to query parameter if header is missing (useful for debug/legacy)
    if not key:
        key = request.query_params.get("apiKey")

    if not key:
        raise HTTPException(
            status_code=401,
            detail={"error": "API key required", "code": "AUTH_REQUIRED"}
        )

    # 3. Check for master system key
    master_key = os.environ.get("PRECISIONFIT_MASTER_KEY")
    if master_key and key == master_key:
        return key

    # 4. Validate against Supabase
    key_data = await DatabaseService.get_api_key(key)
    if not key_data:
        raise HTTPException(
            status_code=403,
            detail={"error": "Invalid or inactive API key", "code": "INVALID_KEY"}
        )
    
    return key
