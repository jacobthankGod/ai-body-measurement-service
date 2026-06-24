"""
Admin Auth Verification Route
============================
Verifies that the requesting user has an admin role before granting
access to the admin panel. Replaces the previous hardcoded admin key.
"""
import os
import logging
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.services.database_service import DatabaseService

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger("KORRA_ADMIN_AUTH")

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://blsettabymllulsxtziw.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')


async def verify_supabase_token(access_token: str):
    if not access_token:
        return None
    import httpx
    userinfo_url = f"{SUPABASE_URL}/auth/v1/user"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_ANON_KEY},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
    return None


@router.get("/admin/check-admin")
async def check_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    user = await verify_supabase_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    try:
        client = DatabaseService.get_client()
        result = client.table("profiles").select("role").eq("id", user_id).single().execute()
        if result.data and result.data.get("role") == "admin":
            return {"isAdmin": True, "user_id": user_id}
    except Exception as e:
        logger.error(f"Admin check failed: {e}")

    raise HTTPException(status_code=403, detail="Admin access required")
