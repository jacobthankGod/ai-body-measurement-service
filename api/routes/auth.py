"""
Authentication & API Key Routes
=============================
Handles Supabase JWT validation and API key issuance.
"""
import json
import hashlib
import secrets
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Security, Header, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from api.services.email_service import EmailService

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger("KORRA_AUTH")
email_service = EmailService()

# Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://blsettabymllulsxtziw.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

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

@router.get("/auth/session")
async def get_session(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current session - required for admin panel"""
    if not credentials: raise HTTPException(status_code=401, detail="Authorization token required")
    user = await verify_supabase_token(credentials.credentials)
    if not user: raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"success": True, "session": user}

# ============ TRANSACTIONAL EMAIL ROUTES ============

@router.post("/auth/send-verification")
async def send_verification(data: Dict[str, Any] = Body(...)):
    """Trigger branded verification email via Brevo"""
    email = data.get("email")
    user_name = data.get("user_name", "Valued Client")
    redirect_url = data.get("redirect_url")

    if not email or not redirect_url:
        raise HTTPException(status_code=400, detail="Email and redirect_url are required")

    success = await email_service.send_verification_email(email, user_name, redirect_url)

    if success:
        return {"success": True, "message": "Verification email dispatched"}
    else:
        raise HTTPException(status_code=500, detail="Dispatch failure")

@router.post("/auth/send-reset")
async def send_reset(data: Dict[str, Any] = Body(...)):
    """Trigger branded password reset email via Brevo"""
    email = data.get("email")
    reset_url = data.get("reset_url")

    if not email or not reset_url:
        raise HTTPException(status_code=400, detail="Email and reset_url are required")

    success = await email_service.send_password_reset_email(email, reset_url)

    if success:
        return {"success": True, "message": "Reset email dispatched"}
    else:
        raise HTTPException(status_code=500, detail="Dispatch failure")
