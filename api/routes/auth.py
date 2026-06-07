"""
Authentication & API Key Routes
=============================
Handles Supabase JWT validation, API key issuance, and Automated Comms.
"""
import json
import hashlib
import secrets
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Security, Header, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from api.services.email_service import EmailService

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger("KORRA_AUTH")

# Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://blsettabymllulsxtziw.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

# --- PHASE 16: NOTIFICATIONS ---

@router.post("/auth/notifications/welcome")
async def trigger_welcome_email(
    payload: dict = Body(...)
):
    """
    Explicit trigger for the Phase 16 Welcome series.
    Can be called by the frontend success state or a DB trigger.
    """
    email = payload.get("email")
    name = payload.get("name", "Artisan")

    if not email:
        raise HTTPException(status_code=400, detail="Recipient email required")

    result = await EmailService.send_welcome_email(email, name)
    return {"success": True, "dispatch": result}

# ============ EXISTING AUTH LOGIC ============

async def verify_supabase_token(access_token: str) -> Optional[Dict]:
    if not access_token: return None
    userinfo_url = f"{SUPABASE_URL}/auth/v1/user"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_ANON_KEY},
                timeout=10
            )
            if response.status_code == 200: return response.json()
    except Exception as e: logger.error(f"Token verification failed: {e}")
    return None

@router.get("/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials: raise HTTPException(status_code=401, detail="Authorization token required")
    user = await verify_supabase_token(credentials.credentials)
    if not user: raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"success": True, "user": user}
