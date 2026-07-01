#!/usr/bin/env python3
"""
Build Training Dataset from Production Scan Data
=================================================
Aggregates scans with SMPL params, downloads photos/meshes, generates metadata,
computes statistics, and produces stratified train/val/test splits.

Output structure:
    data/training_dataset/v{version}/
        VERSION.json               — build metadata
        manifest.csv               — scan-level summary
        shape_statistics.json      — SMPL shape param distributions
        measurement_statistics.json— measurement distributions per subgroup
        splits/
            train.txt              — scan IDs for training
            val.txt                — scan IDs for validation
            test.txt               — scan IDs for testing
        scan_{id}/
            front.png              — front photo
            side.png               — side photo (if available)
            mesh_posed.obj         — posed mesh (if available)
            mesh_tpose.obj         — T-pose mesh (if available)
            metadata.json          — full scan metadata

Usage:
    # Full build
    python scripts/build_training_dataset.py --version 1

    # Incremental build (only new scans since last checkpoint)
    python scripts/build_training_dataset.py --version 2 --incremental auto

    # High-quality subset
    python scripts/build_training_dataset.py --version 3 --min-quality 70 --require-tpose

    # Dry run (stats only)
    python scripts/build_training_dataset.py --version 4 --dry-run

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY env vars
"""
import os
import sys
import json
import csv
import time
import hashlib
import argparse
import logging
import gc
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DATASET_BUILDER")

# Constants
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3
CHECKPOINT_FILE = ".dataset_checkpoint"
DEFAULT_MAX_WORKERS = 4
DEFAULT_BASE_DIR = "data/training_dataset"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    h.update(file_path.read_bytes())
    return h.hexdigest()


def download_with_retry(url: str, dest: Path, desc: str = "") -> bool:
    """Download a file with retry and exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.get(url, timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
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


def get_supabase_client():
    """Create Supabase client with service role key."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(url, key)


def load_checkpoint() -> Optional[str]:
    """Return the ISO timestamp of the last successful build."""
    if os.path.exists(CHECKPOINT_FILE):
        return Path(CHECKPOINT_FILE).read_text().strip()
    return None


def save_checkpoint(timestamp: str):
    """Save the current timestamp for next incremental build."""
    Path(CHECKPOINT_FILE).write_text(timestamp)
    logger.info(f"Checkpoint saved: {timestamp}")


def get_latest_dataset_version(base_dir: Path) -> Optional[int]:
    """Find the highest version number in the dataset directory."""
    if not base_dir.exists():
        return None
    versions = []
    for d in base_dir.iterdir():
        if d.is_dir() and d.name.startswith('v'):
            try:
                versions.append(int(d.name[1:]))
            except ValueError:
                pass
    return max(versions) if versions else None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_scans_with_smpl(supabase, limit: Optional[int] = None,
                           offset: int = 0,
                           incremental_since: Optional[str] = None) -> List[Dict]:
    """Query measurements with SMPL params, ordered by created_at."""
    query = supabase.table("measurements") \
        .select("id, height, gender, body_shape, size_recommendation, "
                "biometrics, clinical_realism_index, "
                "photo_front_url, photo_side_url, "
                "mesh_storage_url, tpose_mesh_url, "
                "created_at, smpl_params_version") \
        .not_.is_("smpl_params", "null") \
        .order("created_at") \
        .offset(offset)

    if limit:
        query = query.limit(limit)
    if incremental_since:
        query = query.gte("created_at", incremental_since)

    response = query.execute()
    return response.data


# ---------------------------------------------------------------------------
# Quality filtering
# ---------------------------------------------------------------------------

def is_extreme_shape(biometrics: dict) -> bool:
    """Check if SMPL shape params contain extreme values (beyond +/- 3.5)."""
    smpl = biometrics.get('__smpl_params', {})
    shape = smpl.get('shape', [])
    if len(shape) != 10:
        return False
    return any(abs(s) > 3.5 for s in shape)


def apply_quality_filters(scans: List[Dict], min_quality: float = 0.0,
                           require_tpose: bool = False,
                           require_side: bool = False,
                           filter_unknown_shape: bool = False,
                           filter_shape_outliers: bool = False) -> Tuple[List[Dict], Dict[str, int]]:
    """Apply quality filters. Returns (filtered, reasons_count)."""
    reasons = {
        'low_quality': 0,
        'missing_tpose': 0,
        'missing_side': 0,
        'unknown_body_shape': 0,
        'extreme_shape': 0,
    }
    filtered = []

    for scan in scans:
        skip = False

        cri = scan.get('clinical_realism_index') or 0
        if cri < min_quality:
            reasons['low_quality'] += 1
            skip = True

        if require_tpose and not scan.get('tpose_mesh_url'):
            reasons['missing_tpose'] += 1
            skip = True

        if require_side and not scan.get('photo_side_url'):
            reasons['missing_side'] += 1
            skip = True

        if filter_unknown_shape and (not scan.get('body_shape') or scan['body_shape'] == 'Unknown'):
            reasons['unknown_body_shape'] += 1
            skip = True

        if filter_shape_outliers and is_extreme_shape(scan.get('biometrics', {})):
            reasons['extreme_shape'] += 1
            skip = True

        if not skip:
            filtered.append(scan)

    return filtered, reasons


# ---------------------------------------------------------------------------
# Per-scan processing
# ---------------------------------------------------------------------------

def process_scan(scan: Dict, output_dir: Path) -> Optional[Dict]:
    """
    Download all assets for a single scan and write metadata.
    Returns metadata dict, or None if critical assets missing.
    """
    scan_id = scan['id']
    scan_dir = output_dir / f"scan_{scan_id}"
    scan_dir.mkdir(parents=True, exist_ok=True)

    # Download front photo (critical)
    front_path = scan_dir / "front.png"
    if scan.get('photo_front_url'):
        if not download_with_retry(scan['photo_front_url'], front_path, f"front {scan_id[:8]}"):
            logger.warning(f"Front photo download failed for {scan_id}, skipping")
            _cleanup_scan_dir(scan_dir)
            return None
    else:
        logger.warning(f"No front photo URL for {scan_id}, skipping")
        _cleanup_scan_dir(scan_dir)
        return None

    # Download side photo (optional)
    side_path = scan_dir / "side.png"
    if scan.get('photo_side_url'):
        download_with_retry(scan['photo_side_url'], side_path, f"side {scan_id[:8]}")

    # Download posed mesh (optional)
    mesh_path = scan_dir / "mesh_posed.obj"
    if scan.get('mesh_storage_url'):
        download_with_retry(scan['mesh_storage_url'], mesh_path, f"posed mesh {scan_id[:8]}")

    # Download T-pose mesh (optional)
    tpose_path = scan_dir / "mesh_tpose.obj"
    if scan.get('tpose_mesh_url'):
        download_with_retry(scan['tpose_mesh_url'], tpose_path, f"T-pose mesh {scan_id[:8]}")

    # Extract SMPL params and joints from biometrics JSONB
    biometrics = scan.get('biometrics', {}).copy() if scan.get('biometrics') else {}
    smpl_params = biometrics.pop('__smpl_params', None)
    joints3d = biometrics.pop('__joints3d', None)

    # Write metadata
    metadata = {
        'scan_id': scan_id,
        'height_cm': scan['height'],
        'gender': scan['gender'],
        'body_shape': scan.get('body_shape', 'Unknown'),
        'size_recommendation': scan.get('size_recommendation', 'M'),
        'clinical_realism_index': scan.get('clinical_realism_index'),
        'measurements': biometrics,
        'smpl_params': smpl_params,
        'joints3d': joints3d,
        'smpl_params_version': scan.get('smpl_params_version', 1),
        'created_at': scan.get('created_at'),
        'files': {
            'front.png': front_path.exists(),
            'side.png': side_path.exists(),
            'mesh_posed.obj': mesh_path.exists(),
            'mesh_tpose.obj': tpose_path.exists(),
        },
        'hashes': {},
    }

    for fname, fpath in [('front.png', front_path), ('side.png', side_path),
                          ('mesh_posed.obj', mesh_path), ('mesh_tpose.obj', tpose_path)]:
        if fpath.exists():
            metadata['hashes'][fname] = compute_sha256(fpath)

    meta_path = scan_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    return metadata


def _cleanup_scan_dir(scan_dir: Path):
    """Remove a scan directory if processing failed."""
    if scan_dir.exists():
        shutil.rmtree(scan_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

def generate_manifest(metadatas: List[Optional[Dict]], output_dir: Path) -> Path:
    """Generate manifest CSV with scan-level metadata."""
    manifest_path = output_dir / "manifest.csv"
    fieldnames = [
        'scan_id', 'gender', 'height_cm', 'body_shape',
        'has_front', 'has_side', 'has_mesh_posed', 'has_mesh_tpose',
        'has_smpl_params', 'n_measurements', 'clinical_realism_index',
        'sha256_front', 'sha256_side',
    ]

    with open(manifest_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for meta in metadatas:
            if meta is None:
                continue
            writer.writerow({
                'scan_id': meta['scan_id'],
                'gender': meta['gender'],
                'height_cm': meta['height_cm'],
                'body_shape': meta.get('body_shape', 'Unknown'),
                'has_front': meta['files'].get('front.png', False),
                'has_side': meta['files'].get('side.png', False),
                'has_mesh_posed': meta['files'].get('mesh_posed.obj', False),
                'has_mesh_tpose': meta['files'].get('mesh_tpose.obj', False),
                'has_smpl_params': meta['smpl_params'] is not None,
                'n_measurements': len(meta.get('measurements', {})),
                'clinical_realism_index': meta.get('clinical_realism_index', 0),
                'sha256_front': meta['hashes'].get('front.png', ''),
                'sha256_side': meta['hashes'].get('side.png', ''),
            })

    logger.info(f"Manifest written: {manifest_path} ({sum(1 for m in metadatas if m)} scans)")
    return manifest_path


# ---------------------------------------------------------------------------
# Splits generation
# ---------------------------------------------------------------------------

def generate_splits(metadatas: List[Optional[Dict]], output_dir: Path,
                     val_ratio: float = 0.05, test_ratio: float = 0.05):
    """Generate train/val/test splits stratified by gender."""
    valid = [m for m in metadatas if m is not None]

    male_scans = [m for m in valid if m['gender'] == 'male']
    female_scans = [m for m in valid if m['gender'] == 'female']

    splits_dir = output_dir / "splits"
    splits_dir.mkdir(exist_ok=True)

    def _write_split(scans, name):
        path = splits_dir / f"{name}.txt"
        path.write_text('\n'.join([m['scan_id'] for m in scans]))

    def _split_group(scans, label):
        n = len(scans)
        if n == 0:
            return [], [], []
        if n < 10:
            return scans, [], []
        from sklearn.model_selection import train_test_split
        train, temp = train_test_split(scans, test_size=val_ratio + test_ratio, random_state=42)
        if len(temp) < 2:
            return train + temp, [], []
        val, test = train_test_split(temp, test_size=test_ratio / (val_ratio + test_ratio), random_state=42)
        return train, val, test

    male_train, male_val, male_test = _split_group(male_scans, 'male')
    female_train, female_val, female_test = _split_group(female_scans, 'female')

    all_train = male_train + female_train
    all_val = male_val + female_val
    all_test = male_test + female_test

    _write_split(all_train, 'train')
    _write_split(all_val, 'val')
    _write_split(all_test, 'test')

    logger.info(f"Splits: {len(all_train)} train, {len(all_val)} val, {len(all_test)} test")
    logger.info(f"  Male: {len(male_train)}/{len(male_val)}/{len(male_test)}")
    logger.info(f"  Female: {len(female_train)}/{len(female_val)}/{len(female_test)}")

    return all_train, all_val, all_test


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_shape_statistics(metadatas: List[Optional[Dict]]) -> Dict:
    """Compute SMPL shape parameter statistics from dataset."""
    shape_vectors = []
    for meta in metadatas:
        if meta is None:
            continue
        sp = meta.get('smpl_params')
        if sp and sp.get('shape') and len(sp['shape']) == 10:
            shape_vectors.append(sp['shape'])

    if len(shape_vectors) < 5:
        logger.warning(f"Too few shape vectors ({len(shape_vectors)}) for statistics")
        return {}

    shapes = np.array(shape_vectors)
    mean = np.mean(shapes, axis=0)
    cov = np.cov(shapes, rowvar=False)
    std = np.std(shapes, axis=0)
    corr = np.corrcoef(shapes, rowvar=False)

    stats = {
        'n_scans': len(shape_vectors),
        'mean': mean.tolist(),
        'std': std.tolist(),
        'min': np.min(shapes, axis=0).tolist(),
        'max': np.max(shapes, axis=0).tolist(),
        'covariance': cov.tolist(),
        'correlation': corr.tolist(),
        'p5': np.percentile(shapes, 5, axis=0).tolist(),
        'p25': np.percentile(shapes, 25, axis=0).tolist(),
        'p50': np.percentile(shapes, 50, axis=0).tolist(),
        'p75': np.percentile(shapes, 75, axis=0).tolist(),
        'p95': np.percentile(shapes, 95, axis=0).tolist(),
    }

    logger.info(f"Shape statistics computed from {len(shape_vectors)} scans")
    for i in range(10):
        logger.info(f"  Beta {i}: mean={mean[i]:.4f}, std={std[i]:.4f}, "
                    f"range=[{stats['min'][i]:.4f}, {stats['max'][i]:.4f}]")

    return stats


def compute_measurement_statistics(metadatas: List[Optional[Dict]]) -> Dict:
    """Compute per-measurement statistics stratified by gender, height, body shape."""
    measurements_by_group: Dict[str, List[float]] = {}

    for meta in metadatas:
        if meta is None:
            continue
        gender = meta['gender']
        height = meta['height_cm']
        height_bin = f"{int(height // 5 * 5)}-{int(height // 5 * 5 + 5)}"
        body_shape = meta.get('body_shape', 'Unknown')

        for key, val in meta.get('measurements', {}).items():
            if not isinstance(val, (int, float)) or val <= 0:
                continue
            for group_key in [
                f"{gender}/all/{key}",
                f"{gender}/{height_bin}/{key}",
                f"{gender}/{body_shape}/{key}",
            ]:
                if group_key not in measurements_by_group:
                    measurements_by_group[group_key] = []
                measurements_by_group[group_key].append(val)

    stats = {}
    for group_key, values in measurements_by_group.items():
        if len(values) < 3:
            continue
        arr = np.array(values)
        stats[group_key] = {
            'n': len(values),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'p5': float(np.percentile(arr, 5)),
            'p25': float(np.percentile(arr, 25)),
            'p50': float(np.percentile(arr, 50)),
            'p75': float(np.percentile(arr, 75)),
            'p95': float(np.percentile(arr, 95)),
        }

    logger.info(f"Measurement statistics: {len(stats)} subgroup-measurement combinations")
    return stats


def compute_gender_shape_stats(metadatas: List[Optional[Dict]]) -> Dict:
    """Compute per-gender shape statistics."""
    male_shapes = []
    female_shapes = []

    for meta in metadatas:
        if meta is None:
            continue
        sp = meta.get('smpl_params')
        if sp and sp.get('shape') and len(sp['shape']) == 10:
            if meta['gender'] == 'male':
                male_shapes.append(sp['shape'])
            elif meta['gender'] == 'female':
                female_shapes.append(sp['shape'])

    stats = {}
    for gender, shapes_list in [('male', male_shapes), ('female', female_shapes)]:
        if len(shapes_list) >= 10:
            shapes_arr = np.array(shapes_list)
            stats[gender] = {
                'n': len(shapes_list),
                'mean': shapes_arr.mean(axis=0).tolist(),
                'std': shapes_arr.std(axis=0).tolist(),
                'p50': np.percentile(shapes_arr, 50, axis=0).tolist(),
            }

    return stats


# ---------------------------------------------------------------------------
# Print report
# ---------------------------------------------------------------------------

def print_statistics(metadatas: List[Optional[Dict]]):
    """Print comprehensive dataset statistics."""
    valid = [m for m in metadatas if m is not None]
    if not valid:
        logger.info("No valid scans to report")
        return

    heights = [m['height_cm'] for m in valid]
    genders: Dict[str, int] = {}
    body_shapes: Dict[str, int] = {}
    smpl_count = 0
    front_count = 0
    side_count = 0
    tpose_count = 0

    for m in valid:
        genders[m['gender']] = genders.get(m['gender'], 0) + 1
        bs = m.get('body_shape', 'Unknown')
        body_shapes[bs] = body_shapes.get(bs, 0) + 1
        if m.get('smpl_params'):
            smpl_count += 1
        if m['files'].get('front.png'):
            front_count += 1
        if m['files'].get('side.png'):
            side_count += 1
        if m['files'].get('mesh_tpose.obj'):
            tpose_count += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("DATASET STATISTICS")
    logger.info("=" * 60)
    logger.info(f"  Total scans:             {len(valid)}")
    logger.info(f"  Genders:                 {dict(genders)}")
    logger.info(f"  Body shapes:             {dict(body_shapes)}")
    logger.info(f"  Height range:            {min(heights):.0f} - {max(heights):.0f} cm "
                f"(mean {np.mean(heights):.0f})")
    logger.info(f"  With SMPL params:        {smpl_count}")
    logger.info(f"  With front photo:        {front_count}")
    logger.info(f"  With side photo:         {side_count}")
    logger.info(f"  With T-pose mesh:        {tpose_count}")
    logger.info(f"  Total measurement vals:  {sum(len(m.get('measurements', {})) for m in valid)}")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------

def validate_dataset(output_dir: Path) -> bool:
    """Validate dataset integrity: check all expected files exist."""
    errors = []

    manifest = output_dir / "manifest.csv"
    if not manifest.exists():
        errors.append("Manifest CSV missing")

    for split in ['train', 'val', 'test']:
        split_file = output_dir / "splits" / f"{split}.txt"
        if not split_file.exists():
            errors.append(f"Split {split} missing")

    scan_dirs = sorted(output_dir.glob("scan_*"))
    if not scan_dirs:
        errors.append("No scan directories found")
    else:
        for sd in scan_dirs:
            meta = sd / "metadata.json"
            if not meta.exists():
                errors.append(f"Metadata missing in {sd.name}")
                continue
            try:
                m = json.loads(meta.read_text())
                if not m.get('smpl_params'):
                    errors.append(f"SMPL params missing in {sd.name}")
                if not m['files'].get('front.png'):
                    errors.append(f"Front photo missing in {sd.name}")
            except Exception as e:
                errors.append(f"Invalid metadata in {sd.name}: {e}")

    if errors:
        logger.warning(f"Validation: {len(errors)} issues found")
        for e in errors[:20]:
            logger.warning(f"  - {e}")
        return False

    logger.info("Validation passed — all files OK")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build training dataset from production scan data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--version', type=int, required=True, help='Dataset version number')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_BASE_DIR,
                        help=f'Base output directory (default: {DEFAULT_BASE_DIR})')
    parser.add_argument('--limit', type=int, help='Max scans to process')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--incremental', type=str, nargs='?', const='auto',
                        help='Only process scans since last checkpoint (auto) or ISO timestamp')
    parser.add_argument('--dry-run', action='store_true', help='Stats only, no download')
    parser.add_argument('--clean', action='store_true', help='Remove existing dataset version first')
    parser.add_argument('--validate', action='store_true', help='Run integrity check on existing dataset')

    # Quality filters
    parser.add_argument('--min-quality', type=float, default=0.0,
                        help='Minimum clinical_realism_index (0.0 = no filter)')
    parser.add_argument('--require-tpose', action='store_true',
                        help='Only include scans with T-pose mesh')
    parser.add_argument('--require-side', action='store_true',
                        help='Only include scans with side photo')
    parser.add_argument('--filter-unknown-shape', action='store_true',
                        help='Exclude scans with Unknown body shape')
    parser.add_argument('--filter-shape-outliers', action='store_true',
                        help='Exclude scans with extreme SMPL shape params')
    parser.add_argument('--high-quality', action='store_true',
                        help='Shortcut for --min-quality 70 --require-tpose --filter-unknown-shape')

    # Performance
    parser.add_argument('--max-workers', type=int, default=DEFAULT_MAX_WORKERS,
                        help=f'Parallel download workers (default: {DEFAULT_MAX_WORKERS})')
    args = parser.parse_args()

    # Handle shorthand flags
    if args.high_quality:
        args.min_quality = max(args.min_quality, 70.0)
        args.require_tpose = True
        args.filter_unknown_shape = True

    base_dir = Path(args.output_dir)
    output_dir = base_dir / f"v{args.version}"

    # Validate mode
    if args.validate:
        if not output_dir.exists():
            logger.error(f"Dataset v{args.version} not found at {output_dir}")
            sys.exit(1)
        ok = validate_dataset(output_dir)
        sys.exit(0 if ok else 1)

    # Clean mode
    if args.clean and output_dir.exists():
        shutil.rmtree(output_dir)
        logger.info(f"Removed {output_dir} for clean rebuild")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Connect
    supabase = get_supabase_client()
    logger.info(f"Connected to Supabase: {os.environ.get('SUPABASE_URL', '?')[:30]}...")

    # Determine incremental timestamp
    incremental_since = None
    if args.incremental == 'auto':
        incremental_since = load_checkpoint()
        if incremental_since:
            logger.info(f"Incremental mode: processing scans since {incremental_since}")
        else:
            logger.info("No checkpoint found — running full build")
            incremental_since = None
    elif args.incremental:
        incremental_since = args.incremental
        logger.info(f"Incremental mode: processing scans since {incremental_since}")

    # Fetch scans
    scans = fetch_scans_with_smpl(supabase, limit=args.limit, offset=args.offset,
                                   incremental_since=incremental_since)
    logger.info(f"Fetched {len(scans)} scans with SMPL params from database")

    if not scans:
        logger.info("No scans to process. Dataset is up to date.")
        return

    # Quality filtering
    before_filter = len(scans)
    scans, reasons = apply_quality_filters(
        scans,
        min_quality=args.min_quality,
        require_tpose=args.require_tpose,
        require_side=args.require_side,
        filter_unknown_shape=args.filter_unknown_shape,
        filter_shape_outliers=args.filter_shape_outliers,
    )
    after_filter = len(scans)
    if before_filter > after_filter:
        logger.info(f"Quality filtering: {before_filter} -> {after_filter} scans")
        for reason, count in reasons.items():
            if count > 0:
                logger.info(f"  {reason}: {count}")

    if not scans:
        logger.warning("No scans passed quality filters")
        return

    # Dry run — print stats only
    if args.dry_run:
        print_statistics([{
            'scan_id': s['id'],
            'height_cm': s['height'],
            'gender': s['gender'],
            'body_shape': s.get('body_shape', 'Unknown'),
            'files': {'front.png': bool(s.get('photo_front_url')),
                       'side.png': bool(s.get('photo_side_url')),
                       'mesh_tpose.obj': bool(s.get('tpose_mesh_url'))},
            'measurements': {k: v for k, v in (s.get('biometrics') or {}).items()
                             if not k.startswith('__')},
            'smpl_params': True,
        } for s in scans])
        return

    # Process scans (parallel download)
    logger.info(f"Downloading assets for {len(scans)} scans ({args.max_workers} workers)...")
    metadatas = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(process_scan, scan, output_dir): scan['id']
                   for scan in scans}
        for future in as_completed(futures):
            scan_id = futures[future]
            try:
                meta = future.result()
                metadatas.append(meta)
                if meta is not None:
                    logger.debug(f"  ✅ {scan_id[:8]}")
            except Exception as e:
                logger.error(f"  ❌ {scan_id[:8]}: {e}")
                metadatas.append(None)

    # Report download stats
    succeeded = sum(1 for m in metadatas if m is not None)
    failed = sum(1 for m in metadatas if m is None)
    logger.info(f"Downloaded: {succeeded} succeeded, {failed} failed")

    if succeeded == 0:
        logger.error("No scans downloaded successfully — aborting")
        sys.exit(1)

    # Generate outputs
    generate_manifest(metadatas, output_dir)
    generate_splits(metadatas, output_dir)
    print_statistics(metadatas)

    # Save shape statistics
    shape_stats = compute_shape_statistics(metadatas)
    if shape_stats:
        (output_dir / "shape_statistics.json").write_text(json.dumps(shape_stats, indent=2))
        logger.info(f"Shape statistics saved ({shape_stats['n_scans']} scans)")

    # Save gender-specific shape stats
    gender_stats = compute_gender_shape_stats(metadatas)
    if gender_stats:
        (output_dir / "gender_shape_stats.json").write_text(json.dumps(gender_stats, indent=2))

    # Save measurement statistics
    meas_stats = compute_measurement_statistics(metadatas)
    if meas_stats:
        (output_dir / "measurement_statistics.json").write_text(json.dumps(meas_stats, indent=2))

    # Save VERSION.json
    version_info = {
        'version': args.version,
        'created_at': datetime.utcnow().isoformat(),
        'n_scans': succeeded,
        'n_male': sum(1 for m in metadatas if m and m['gender'] == 'male'),
        'n_female': sum(1 for m in metadatas if m and m['gender'] == 'female'),
        'height_min': float(np.min([m['height_cm'] for m in metadatas if m])),
        'height_max': float(np.max([m['height_cm'] for m in metadatas if m])),
        'failed_downloads': failed,
        'incremental': incremental_since is not None,
        'low_quality_filtered': reasons.get('low_quality', 0),
        'tpose_required': args.require_tpose,
    }
    (output_dir / "VERSION.json").write_text(json.dumps(version_info, indent=2))

    # Validate
    validate_dataset(output_dir)

    # Save checkpoint for incremental builds
    save_checkpoint(datetime.utcnow().isoformat())

    # Log completion
    logger.info(f"Dataset v{args.version} complete — {output_dir}")
    logger.info(f"Run next: python scripts/train_shape_prior.py --dataset-dir {output_dir}")


if __name__ == "__main__":
    main()
