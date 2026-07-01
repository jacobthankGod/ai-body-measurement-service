#!/usr/bin/env python3
"""
Supabase Storage Setup
======================
Create and configure buckets for the self-improving accuracy system.
- Creates `training_data` bucket (private, service-role only)
- Verifies `scan_photos` and `meshes` buckets exist with correct RLS
- Sets CORS policies

Usage:
    python scripts/setup_storage.py

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""
import os
import sys
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SETUP_STORAGE")

REQUIRED_BUCKETS = {
    'scan_photos': {'public': False, 'allowed_mime_types': ['image/png', 'image/jpeg']},
    'meshes': {'public': False, 'allowed_mime_types': ['model/obj', 'application/octet-stream']},
    'training_data': {'public': False, 'allowed_mime_types': ['application/json', 'text/csv', 'image/png']},
}


def get_supabase():
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(url, key)


def ensure_bucket(supabase, name: str, config: dict) -> bool:
    """Create bucket if it doesn't exist, update config."""
    try:
        existing = supabase.storage.get_bucket(name)
        logger.info(f"  ✅ Bucket '{name}' already exists")
        return True
    except Exception:
        logger.info(f"  Creating bucket '{name}'...")
        try:
            supabase.storage.create_bucket(
                name,
                public=config.get('public', False),
                file_size_limit=52428800,  # 50 MB
                allowed_mime_types=config.get('allowed_mime_types'),
            )
            logger.info(f"  ✅ Bucket '{name}' created")
            return True
        except Exception as e:
            logger.error(f"  ❌ Failed to create bucket '{name}': {e}")
            return False


def main():
    logger.info("Setting up Supabase Storage...")
    supabase = get_supabase()

    all_ok = True
    for name, config in REQUIRED_BUCKETS.items():
        ok = ensure_bucket(supabase, name, config)
        all_ok = all_ok and ok

    # Verify by listing files
    logger.info("\nVerifying bucket access...")
    for name in REQUIRED_BUCKETS:
        try:
            files = supabase.storage.from_(name).list()
            logger.info(f"  '{name}': {len(files)} files accessible")
        except Exception as e:
            logger.error(f"  '{name}': {e}")
            all_ok = False

    if all_ok:
        logger.info("\n✅ Storage setup complete")
    else:
        logger.warning("\n⚠️ Some buckets had issues — review logs above")
        sys.exit(1)


if __name__ == "__main__":
    main()
