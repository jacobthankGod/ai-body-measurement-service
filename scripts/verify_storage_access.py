#!/usr/bin/env python3
"""Verify Supabase Storage access for dataset pipeline buckets."""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("STORAGE_VERIFY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)


def verify_bucket(bucket_name: str, expected_public: bool = False):
    """Verify bucket exists and is accessible."""
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # List files in bucket
        files = supabase.storage.from_(bucket_name).list()
        logger.info(f"✅ '{bucket_name}': {len(files)} files accessible")

        # Check a few files
        for f in files[:3]:
            name = f.get('name', f)
            logger.info(f"   - {name}")

        return True
    except Exception as e:
        logger.error(f"❌ '{bucket_name}': {e}")
        return False


def main():
    logger.info("Verifying Supabase Storage access...")
    logger.info(f"URL: {SUPABASE_URL}")

    all_ok = True
    all_ok &= verify_bucket("scan_photos")
    all_ok &= verify_bucket("meshes")

    try:
        all_ok &= verify_bucket("training_data")
    except Exception:
        logger.warning("⚠️ 'training_data' bucket may not exist yet (create manually if needed)")

    if all_ok:
        logger.info("\n✅ All buckets accessible")
    else:
        logger.warning("\n⚠️ Some buckets had issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
