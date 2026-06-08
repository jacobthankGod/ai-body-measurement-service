"""
Supabase Database Service | UNICORN-GRADE PERSISTENCE
=====================================================
Handles atomic persistence for API keys, usage, 3D Biometrics, and Invitations.
"""
import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from supabase import create_client, Client

logger = logging.getLogger("KORRA_DB")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

class DatabaseService:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_KEY: 
                logger.error("❌ DatabaseService: SUPABASE_URL or SUPABASE_KEY is None in ENV!")
                return None
            try:
                cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e: 
                logger.error(f"❌ DatabaseService: Failed to create client: {e}")
                return None
        return cls._instance

    @classmethod
    async def create_invitation(cls, merchant_id: str, client_name: str) -> str:
        """Atomic Invitation Persistence."""
        client = cls.get_client()
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=1)
        try:
            client.table("invitations").insert({
                "token": token,
                "merchant_id": merchant_id,
                "client_name": client_name,
                "expires_at": expires_at.isoformat()
            }).execute()
            return token
        except Exception as e:
            logger.error(f"Invite Persistence Failed: {e}")
            return None

    @classmethod
    async def verify_invitation(cls, token: str) -> Optional[dict]:
        """Verify invitation against PostgreSQL vault."""
        client = cls.get_client()
        try:
            res = client.table("invitations").select("*").eq("token", token).execute()
            if not res.data: return None
            invite = res.data[0]
            if datetime.fromisoformat(invite["expires_at"]) < datetime.utcnow():
                return None
            return invite
        except Exception as e: return None

    @classmethod
    async def save_measurement(cls, user_id: str, client_name: str, height: float, gender: str, biometrics: dict, landmarks: dict = None, mesh_url: str = None):
        client = cls.get_client()
        if not client: 
            logger.error("❌ DatabaseService: Supabase client is None - ENV variables missing!")
            return None
        try:
            payload = {
                "user_id": user_id, "client_name": client_name, "height": height,
                "gender": gender, "biometrics": biometrics, "landmarks_3d": landmarks if landmarks else {},
                "mesh_url": mesh_url, "created_at": datetime.utcnow().isoformat()
            }
            logger.info(f"💾 DatabaseService: Inserting payload for {client_name}, height={height}, gender={gender}")
            logger.info(f"💾 Payload keys: {list(payload.keys())}")
            
            response = client.table("measurements").insert(payload).execute()
            
            if response.data:
                logger.info(f"✅ DatabaseService: Insert successful! ID: {response.data[0].get('id')}")
                return response.data[0]
            else:
                logger.error("❌ DatabaseService: Insert returned no data")
                return None
        except Exception as e:
            logger.error(f"❌ DatabaseService.save_measurement FAILED: {e}")
            return None

    @classmethod
    async def get_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client: return None
        try:
            response = client.table("api_keys").select("*").eq("key", api_key).eq("is_active", True).execute()
            return response.data[0] if response.data else None
        except: return None

    @classmethod
    async def update_usage(cls, api_key: str):
        client = cls.get_client()
        if not client: return
        try:
            res = client.table("usage_logs").select("*").eq("api_key", api_key).execute()
            if res.data:
                client.table("usage_logs").update({"total_count": res.data[0]["total_count"] + 1, "last_used": datetime.now().isoformat()}).eq("api_key", api_key).execute()
            else:
                client.table("usage_logs").insert({"api_key": api_key, "total_count": 1, "last_used": datetime.now().isoformat()}).execute()
        except: pass
