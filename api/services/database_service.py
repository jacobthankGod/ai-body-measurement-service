"""
Supabase Database Service | UNICORN-GRADE PERSISTENCE
=====================================================
Handles atomic persistence for API keys, usage, and 3D Biometrics.
Uses high-privilege Service Role for critical infrastructure handshakes.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from supabase import create_client, Client

logger = logging.getLogger("KORRA_DB")

# Environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

class DatabaseService:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.error("❌ Infrastructure Failure: Supabase Credentials Missing.")
                return None
            try:
                cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                logger.error(f"❌ Handshake Error: {e}")
                return None
        return cls._instance

    @classmethod
    async def get_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client: return None
        try:
            response = client.table("api_keys").select("*").eq("key", api_key).eq("is_active", True).execute()
            if response.data: return response.data[0]
        except Exception as e: logger.error(f"PfError: API Key Lookup Failed: {e}")
        return None

    @classmethod
    async def save_measurement(cls, user_id: str, client_name: str, height: float, gender: str, biometrics: dict, landmarks: dict = None, mesh_url: str = None):
        """
        UNICORN-GRADE ATOMIC SAVE
        Persists full biometric record to the global PostgreSQL vault.
        """
        client = cls.get_client()
        if not client: return None

        try:
            payload = {
                "user_id": user_id,
                "client_name": client_name,
                "height": height,
                "gender": gender,
                "biometrics": biometrics,
                "landmarks_3d": landmarks if landmarks else {},
                "mesh_url": mesh_url,
                "created_at": datetime.utcnow().isoformat()
            }

            response = client.table("measurements").insert(payload).execute()
            if response.data:
                logger.info(f"✅ UNICORN PERSISTENCE: Record {response.data[0]['id']} locked in vault.")
                return response.data[0]
        except Exception as e:
            logger.error(f"❌ ATOMIC SAVE FAILED: {e}")
            return None

    @classmethod
    async def update_usage(cls, api_key: str):
        client = cls.get_client()
        if not client: return
        now = datetime.now()
        day_key = now.strftime('%Y-%m-%d')
        try:
            response = client.table("usage_logs").select("*").eq("api_key", api_key).execute()
            if response.data:
                log = response.data[0]
                client.table("usage_logs").update({
                    "total_count": log.get("total_count", 0) + 1,
                    "last_used": now.isoformat()
                }).eq("api_key", api_key).execute()
            else:
                client.table("usage_logs").insert({
                    "api_key": api_key, "total_count": 1, "last_used": now.isoformat()
                }).execute()
        except Exception as e: logger.error(f"Usage Update Failed: {e}")

    @classmethod
    async def save_api_key(cls, api_key: str, user_id: str, tier: str = "tailor_pro"):
        client = cls.get_client()
        if not client: return False
        try:
            client.table("api_keys").insert({
                "key": api_key, "user_id": user_id, "tier": tier, "is_active": True
            }).execute()
            return True
        except Exception as e: logger.error(f"Key Persistence Failed: {e}"); return False
