"""
Setup Supabase storage bucket for garment reconstruction results.
Run this once: python scripts/setup_garment_storage.py
"""
import os
import sys
from pathlib import Path

# Load env from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://blsettabymllulsxtziw.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_SERVICE_KEY:
    print("ERROR: Set SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Create bucket
try:
    client.storage.create_bucket("garment_results", options={"public": False})
    print("Created bucket: garment_results")
except Exception as e:
    if "already exists" in str(e).lower():
        print("Bucket garment_results already exists")
    else:
        print(f"Error: {e}")

# Set RLS policy: service_role can do everything, users can read own files
print("Bucket setup complete.")
print("Note: RLS for storage buckets is managed via the Supabase dashboard.")
print("Go to Storage > garment_results > Policies and add:")
print("  - SELECT policy: allow authenticated users to read files in their folder")
print("  - INSERT/UPDATE/DELETE policy: allow service_role only")
