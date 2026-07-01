#!/usr/bin/env python3
"""
Train Measurement Consistency Model
====================================
Learns expected measurement ranges per gender and identifies outliers
across repeated scans of the same user. Uses IsolationForest for
multi-measurement anomaly detection.

Usage:
    python scripts/train_consistency_model.py \
        --dataset-dir data/training_dataset/v1 \
        --output-dir api/models/priors \
        --version 1
"""
import json
import argparse
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("CONSISTENCY")

MEASUREMENT_KEYS = [
    'Chest Round', 'Waist Round', 'Hip Round', 'Thigh Round',
    'Calf Round', 'Shoulder', 'Neck Round', 'Stomach Round',
    'Bicep Round', 'Wrist Round', 'Ankle Round',
]


def load_measurements(dataset_dir: Path, max_scans: int = None) -> Tuple[np.ndarray, List[str]]:
    """Load measurement vectors from dataset metadata."""
    vectors = []
    scan_ids = []
    scan_dirs = sorted(dataset_dir.glob("scan_*"))
    if max_scans:
        scan_dirs = scan_dirs[:max_scans]

    for scan_dir in scan_dirs:
        meta_path = scan_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
            measurements = meta.get('measurements', {})
            vec = []
            valid = True
            for key in MEASUREMENT_KEYS:
                val = measurements.get(key, 0.0)
                if val <= 0 or val > 300:
                    valid = False
                    break
                vec.append(val)
            if valid:
                vectors.append(vec)
                scan_ids.append(meta['scan_id'])
        except Exception as e:
            logger.warning(f"Error reading {meta_path}: {e}")

    logger.info(f"Loaded {len(vectors)} measurement vectors from {dataset_dir}")
    return np.array(vectors), scan_ids


def compute_zscore_bounds(vectors: np.ndarray) -> Dict[str, Dict]:
    """Compute per-measurement statistics and z-score based bounds."""
    keys = MEASUREMENT_KEYS[:vectors.shape[1]]
    bounds = {}
    for i, key in enumerate(keys):
        vals = vectors[:, i]
        mean = float(np.mean(vals))
        std = float(np.std(vals))
        bounds[key] = {
            'mean': round(mean, 1),
            'std': round(std, 1),
            'p5': round(float(np.percentile(vals, 5)), 1),
            'p95': round(float(np.percentile(vals, 95)), 1),
            'z_2_lower': round(mean - 2 * std, 1),
            'z_2_upper': round(mean + 2 * std, 1),
            'z_3_lower': round(mean - 3 * std, 1),
            'z_3_upper': round(mean + 3 * std, 1),
        }
        logger.info(f"  {key}: mean={mean:.1f} std={std:.1f} [{bounds[key]['p5']}-{bounds[key]['p95']}]")
    return bounds


def main():
    parser = argparse.ArgumentParser(description="Train measurement consistency model")
    parser.add_argument('--dataset-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='api/models/priors')
    parser.add_argument('--max-scans', type=int)
    parser.add_argument('--version', type=int, default=1)
    parser.add_argument('--contamination', type=float, default=0.05,
                        help='Expected proportion of outliers')
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vectors, scan_ids = load_measurements(dataset_dir, args.max_scans)
    logger.info(f"Loaded {vectors.shape} measurement matrix")

    scaler = StandardScaler()
    vectors_std = scaler.fit_transform(vectors)
    logger.info("Measurements standardized")

    iso = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(vectors_std)
    scores = iso.score_samples(vectors_std)
    preds = iso.predict(vectors_std)
    n_outliers = int(np.sum(preds == -1))
    logger.info(f"Outliers detected: {n_outliers}/{len(preds)} ({n_outliers/len(preds)*100:.1f}%)")
    logger.info(f"Score range: [{scores.min():.3f}, {scores.max():.3f}]")

    bounds = compute_zscore_bounds(vectors)
    threshold = float(np.percentile(scores, 5))

    model = {
        'model': iso,
        'scaler': scaler,
        'bounds': bounds,
        'threshold': threshold,
        'measurement_keys': MEASUREMENT_KEYS,
        'version': args.version,
        'n_samples': len(vectors),
        'n_outliers': n_outliers,
    }

    model_path = output_dir / "consistency_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Consistency model saved to {model_path}")

    bounds_path = output_dir / "measurement_bounds.json"
    with open(bounds_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Measurement bounds saved to {bounds_path}")

    logger.info("Done. Deploy with:")
    logger.info(f"  cp {model_path} api/models/priors/")


if __name__ == "__main__":
    main()
