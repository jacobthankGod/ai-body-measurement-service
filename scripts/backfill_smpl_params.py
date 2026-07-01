#!/usr/bin/env python3
"""
Backfill SMPL Parameters for Existing Scans
============================================
Re-runs HMR inference on archived photos to extract smpl_params and joints3d.
Only processes scans WHERE smpl_params IS NULL AND photo_front_url IS NOT NULL.

Usage:
    # Dry run (count only):
    python scripts/backfill_smpl_params.py --limit 50 --dry-run

    # Actual backfill:
    python scripts/backfill_smpl_params.py --limit 20

    # Resume from last processed scan:
    python scripts/backfill_smpl_params.py --limit 20 --resume <scan_id>

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY env vars
"""
import os
import sys
import json
import time
import logging
import argparse
import gc
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import numpy as np
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("BACKFILL")

# Safety limits for t3.micro
BATCH_SIZE = 20
SLEEP_BETWEEN_SCANS = 3  # seconds, to prevent OOM
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3


def get_supabase_client():
    """Create Supabase client with service role key."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(url, key)


def get_scans_without_smpl(supabase, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Query measurements table for scans missing SMPL params."""
    response = supabase.table("measurements") \
        .select("id, photo_front_url, photo_side_url, photo_front_url, "
                "height, gender, body_shape, clinical_realism_index") \
        .is_("smpl_params", "null") \
        .not_.is_("photo_front_url", "null") \
        .order("created_at") \
        .offset(offset) \
        .limit(limit) \
        .execute()
    return response.data


def download_with_retry(url: str, dest: Path, desc: str = "") -> bool:
    """Download a file with retry and exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.get(url, timeout=DOWNLOAD_TIMEOUT)
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"{desc}: rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                return True
            logger.warning(f"{desc}: HTTP {resp.status_code} (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"{desc}: {e} (attempt {attempt + 1})")
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    return False


def extract_smpl_from_photos(front_path: Path, height: float, gender: str,
                              side_path: Optional[Path] = None) -> Tuple[Optional[Dict], Optional[List]]:
    """Run HMR on photos, return (smpl_params, joints3d) or (None, None) on failure."""
    from PIL import Image
    from api.services.extract_measurements import HMRMasterEngine

    engine = HMRMasterEngine()
    img_f = np.array(Image.open(str(front_path)))
    img_s = np.array(Image.open(str(side_path))) if side_path and side_path.exists() else None

    try:
        result = engine.extract(img_f, height, gender, side_image=img_s)
        if isinstance(result, tuple) and len(result) >= 9:
            return result[7], result[8]  # smpl_params, joints3d
        logger.warning(f"Engine returned {len(result) if isinstance(result, tuple) else 'non-tuple'} elements")
        return None, None
    except Exception as e:
        logger.error(f"HMR extraction failed: {e}")
        return None, None
    finally:
        del engine, img_f
        if img_s is not None:
            del img_s
        gc.collect()


def update_scan_in_db(supabase, scan_id: str, smpl_params: Optional[Dict],
                       joints3d: Optional[List]) -> bool:
    """Update measurement record with SMPL params."""
    try:
        payload = {}
        if smpl_params:
            payload["smpl_params"] = smpl_params
        if joints3d:
            payload["joints_3d"] = joints3d
        if not payload:
            return False

        supabase.table("measurements") \
            .update(payload) \
            .eq("id", scan_id) \
            .execute()
        return True
    except Exception as e:
        logger.error(f"DB update failed for {scan_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Backfill SMPL params from archived scans")
    parser.add_argument('--limit', type=int, default=BATCH_SIZE,
                        help=f'Scans to process (default: {BATCH_SIZE})')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--dry-run', action='store_true', help='Count only, do not process')
    parser.add_argument('--resume', type=str, help='Resume from a specific scan ID')
    parser.add_argument('--tmp-dir', type=str, default='/tmp/backfill_smpl',
                        help='Temp directory for downloaded photos')
    args = parser.parse_args()

    supabase = get_supabase_client()
    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Discover how many scans need backfill
    count_response = supabase.table("measurements") \
        .select("id", count="exact") \
        .is_("smpl_params", "null") \
        .not_.is_("photo_front_url", "null") \
        .execute()
    total_eligible = count_response.count if hasattr(count_response, 'count') else 'unknown'
    logger.info(f"Total scans without SMPL params: {total_eligible}")

    scans = get_scans_without_smpl(supabase, limit=args.limit, offset=args.offset)
    logger.info(f"Fetched {len(scans)} scans for processing (limit={args.limit}, offset={args.offset})")

    if not scans:
        logger.info("No scans to process. Backfill may be complete.")
        return

    if args.dry_run:
        logger.info("Dry run mode — no changes made")
        for s in scans:
            logger.info(f"  Would process: {s['id']} ({s.get('gender', '?')}, "
                        f"{s.get('height', '?')}cm, CRI={s.get('clinical_realism_index', '?')})")
        return

    processed = 0
    failed = 0
    skipped = 0

    for scan in scans:
        scan_id = scan['id']

        # Resume support: skip scans until we hit the resume point
        if args.resume and scan_id < args.resume:
            skipped += 1
            continue

        logger.info(f"[{processed + 1}/{len(scans)}] Processing {scan_id} "
                    f"({scan.get('gender', '?')}, {scan.get('height', '?')}cm)")

        front_url = scan.get('photo_front_url')
        if not front_url:
            logger.warning(f"  No front photo URL, skipping")
            skipped += 1
            continue

        front_path = tmp_dir / f"{scan_id}_front.png"
        side_path = tmp_dir / f"{scan_id}_side.png"

        # Download photos
        if not download_with_retry(front_url, front_path, f"front {scan_id[:8]}"):
            logger.error(f"  Failed to download front photo")
            failed += 1
            continue

        side_url = scan.get('photo_side_url')
        if side_url:
            download_with_retry(side_url, side_path, f"side {scan_id[:8]}")

        # Run HMR extraction
        smpl_params, joints3d = extract_smpl_from_photos(
            front_path,
            float(scan.get('height', 170)),
            scan.get('gender', 'male'),
            side_path if side_path.exists() else None,
        )

        # Update database
        if smpl_params:
            if update_scan_in_db(supabase, scan_id, smpl_params, joints3d):
                shape = smpl_params.get('shape', [])
                logger.info(f"  ✅ Updated: {len(shape)} shape dims, "
                            f"{len(joints3d) if joints3d else 0} joints")
                processed += 1
            else:
                logger.error(f"  ❌ DB update failed")
                failed += 1
        else:
            logger.warning(f"  ❌ No SMPL params extracted")
            failed += 1

        # Cleanup temp files
        for p in [front_path, side_path]:
            if p.exists():
                p.unlink()

        # Rate limit to avoid OOM on t3.micro
        time.sleep(SLEEP_BETWEEN_SCANS)

    logger.info("=" * 60)
    logger.info(f"Backfill complete: {processed} processed, {failed} failed, {skipped} skipped")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
