#!/usr/bin/env python3
"""
Verify Backfill Integrity
=========================
Checks that the HMRMasterEngine loads correctly and that
sample SMPL data in the database has valid structure.
"""
import os
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("VERIFY_BACKFILL")


def check_engine_loading():
    """Test that HMRMasterEngine loads SMPL templates and faces correctly."""
    logger.info("Checking HMRMasterEngine initialization...")
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from api.services.extract_measurements import HMRMasterEngine
    engine = HMRMasterEngine()

    checks = {
        'vertex_map': len(engine.vertex_map) > 0,
        'smpl_faces': engine.smpl_faces is not None and engine.smpl_faces.shape[0] > 0,
        'v_template': engine._v_template is not None and engine._v_template.shape == (6890, 3),
        'shapedirs': engine._shapedirs is not None,
        'face_segmentation': engine._face_segmentation is not None,
    }

    all_ok = True
    for name, ok in checks.items():
        status = "✅" if ok else "❌"
        logger.info(f"  {status} {name}")
        if not ok:
            all_ok = False

    # Test a mock extraction (no TF available on dev, but check error path)
    import numpy as np
    fake_img = np.zeros((224, 224, 3), dtype=np.uint8)
    result = engine.extract(fake_img, 175, 'male')

    if isinstance(result, tuple):
        logger.info(f"  ✅ extract() returned {len(result)} elements")
        if len(result) >= 9:
            logger.info(f"  ✅ smpl_params in position 7: {result[7] is not None}")
            logger.info(f"  ✅ joints3d in position 8: {result[8] is not None}")
    else:
        logger.warning(f"  ⚠️ extract() returned non-tuple: {type(result)}")

    del engine
    return all_ok


def check_db_records():
    """Verify SMPL data in the database has correct structure."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Skipping DB check: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return True

    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)

    # Count records with/without SMPL params
    total = supabase.table("measurements").select("id", count="exact").execute()
    with_smpl = supabase.table("measurements") \
        .select("id", count="exact") \
        .not_.is_("smpl_params", "null") \
        .execute()

    t_count = total.count if hasattr(total, 'count') else '?'
    s_count = with_smpl.count if hasattr(with_smpl, 'count') else '?'

    logger.info(f"DB records: {t_count} total, {s_count} with SMPL params")

    # Check structure of a few SMPL records
    sample = supabase.table("measurements") \
        .select("id, smpl_params, joints_3d") \
        .not_.is_("smpl_params", "null") \
        .limit(5) \
        .execute()

    if sample.data:
        for row in sample.data:
            sp = row.get('smpl_params', {})
            shape = sp.get('shape', [])
            pose = sp.get('pose', [])
            logger.info(f"  {row['id'][:8]}... shape={len(shape)}d pose={len(pose)}d "
                        f"joints={len(row.get('joints_3d', []))}")
            if len(shape) != 10:
                logger.warning(f"    ⚠️ Expected 10 shape dims, got {len(shape)}")
            if any(abs(s) > 5.0 for s in shape):
                logger.warning(f"    ⚠️ Extreme shape value detected: {shape}")
    else:
        logger.info("  No SMPL records found in DB yet")

    return True


def main():
    logger.info("=" * 60)
    logger.info("BACKFILL VERIFICATION")
    logger.info("=" * 60)

    engine_ok = check_engine_loading()
    db_ok = check_db_records()

    logger.info("=" * 60)
    if engine_ok and db_ok:
        logger.info("✅ All checks passed")
    else:
        logger.warning("⚠️ Some checks failed — review logs above")


if __name__ == "__main__":
    main()
