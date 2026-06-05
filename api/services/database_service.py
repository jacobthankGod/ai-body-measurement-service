"""
Supabase Database Service
========================
Handles persistence for API keys and usage logs.
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
from supabase import create_client, Client

# Environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Use Service Role Key for backend administrative tasks
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

class DatabaseService:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Initialize and return the Supabase client."""
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("Warning: Supabase credentials missing. Database functionality disabled.")
                return None
            try:
                cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                print(f"Error initializing Supabase client: {e}")
                return None
        return cls._instance

    @classmethod
    async def get_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch API key details from Supabase."""
        client = cls.get_client()
        if not client:
            return None

        try:
            response = client.table("api_keys").select("*").eq("key", api_key).eq("is_active", True).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error fetching API key from Supabase: {e}")
        return None

    @classmethod
    async def update_usage(cls, api_key: str):
        """Update usage stats in Supabase."""
        client = cls.get_client()
        if not client:
            return

        now = datetime.now()
        month_key = f"{now.year}-{now.month:02d}"
        day_key = now.strftime('%Y-%m-%d')

        try:
            # 1. Fetch current usage log
            response = client.table("usage_logs").select("*").eq("api_key", api_key).execute()

            if response.data:
                log = response.data[0]
                monthly_usage = log.get("monthly_usage", {})
                daily_usage = log.get("daily_usage", {})

                # Increment counts
                monthly_usage[month_key] = monthly_usage.get(month_key, 0) + 1
                daily_usage[day_key] = daily_usage.get(day_key, 0) + 1

                # Update record
                client.table("usage_logs").update({
                    "total_count": log.get("total_count", 0) + 1,
                    "monthly_usage": monthly_usage,
                    "daily_usage": daily_usage,
                    "last_used": now.isoformat()
                }).eq("api_key", api_key).execute()
            else:
                # Create initial record
                client.table("usage_logs").insert({
                    "api_key": api_key,
                    "total_count": 1,
                    "monthly_usage": {month_key: 1},
                    "daily_usage": {day_key: 1},
                    "last_used": now.isoformat(),
                    "created_at": now.isoformat()
                }).execute()

        except Exception as e:
            print(f"Error updating usage in Supabase: {e}")

    @classmethod
    async def save_api_key(cls, api_key: str, user_id: str, tier: str = "tailor_elite"):
        """Save a new API key to Supabase."""
        client = cls.get_client()
        if not client:
            return False

        try:
            client.table("api_keys").insert({
                "key": api_key,
                "user_id": user_id,
                "tier": tier,
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }).execute()
            return True
        except Exception as e:
            print(f"Error saving API key to Supabase: {e}")
            return False
