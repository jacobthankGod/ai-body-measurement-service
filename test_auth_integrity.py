"""
Auth Integrity Test
==================
Tests the connection to Supabase and API key validation logic.
"""
import os
import asyncio
from api.services.database_service import DatabaseService

async def test_supabase_connection():
    print("🔍 Testing Supabase Connection...")
    client = DatabaseService.get_client()
    if client:
        print("✅ Supabase Client Initialized")
        try:
            # Check if api_keys table exists and is readable
            response = client.table("api_keys").select("count", count="exact").limit(1).execute()
            print(f"✅ Database reachable. API Key count: {response.count}")
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            print("   TIP: Ensure you ran SUPABASE_SETUP.sql in the Supabase SQL Editor.")
    else:
        print("❌ Supabase Client failed to initialize. Check .env values.")

async def verify_test_key():
    test_key = "test_key_precision_3d_001"
    print(f"\n🔍 Verifying Test Key: {test_key}...")
    key_data = await DatabaseService.get_api_key(test_key)
    if key_data:
        print(f"✅ Key is VALID. Tier: {key_data.get('tier')}")
    else:
        print("❌ Key NOT FOUND or INACTIVE in Supabase.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(test_supabase_connection())
    asyncio.run(verify_test_key())
