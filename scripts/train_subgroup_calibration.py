#!/usr/bin/env python3
"""
Per-Subgroup Calibration Training
==================================
Learns cluster-specific calibration factors (alpha, beta) per measurement
using KMeans on (shape + gender + height) space. At inference time, the
nearest cluster's calibration is applied.

Extends the current per-measurement-per-gender ridge regression with
per-subgroup factors for better accuracy on diverse body types.

Usage:
    python scripts/train_subgroup_calibration.py \
        --dataset-dir data/training_dataset/v1 \
        --ground-truth data/unidata/ground_truth.csv \
        --output-dir api/models/priors \
        --version 1
"""
import json
import csv
import argparse
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SUBGROUP_CALIBRATION")

MEASUREMENT_KEYS = [
    'Chest Round', 'Waist Round', 'Hip Round', 'Thigh Round',
    'Calf Round', 'Shoulder', 'Neck Round', 'Stomach Round',
]


def load_ground_truth(csv_path: Path) -> Dict[str, Dict]:
    """Load ground truth measurements from CSV."""
    gt = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject_id = row.get('subject_id', '').strip()
            if not subject_id:
                continue
            measurements = {}
            for key in MEASUREMENT_KEYS:
                val = row.get(key, '').strip()
                if val:
                    measurements[key] = float(val)
            if measurements:
                gt[subject_id] = {
                    'measurements': measurements,
                    'gender': row.get('gender', 'male').strip().lower(),
                    'height': float(row.get('height', 170)),
                }
    logger.info(f"Loaded {len(gt)} ground truth subjects from {csv_path}")
    return gt


def load_smpl_from_dataset(dataset_dir: Path) -> Dict[str, Dict]:
    """Load SMPL params + predicted measurements from dataset metadata."""
    subjects = {}
    for scan_dir in sorted(dataset_dir.glob("scan_*")):
        meta_path = scan_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
            smpl = meta.get('smpl_params')
            if smpl and len(smpl.get('shape', [])) == 10:
                subjects[meta['scan_id']] = {
                    'shape': np.array(smpl['shape'], dtype=np.float64),
                    'gender': meta.get('gender', 'male'),
                    'height': meta.get('height_cm', 170),
                    'measurements': meta.get('measurements', {}),
                }
        except Exception as e:
            logger.warning(f"Error: {e}")
    logger.info(f"Loaded {len(subjects)} subjects from dataset")
    return subjects


def train_subgroup_calibration(
    gt_data: Dict, smpl_data: Dict, n_clusters: int = 5
) -> Dict:
    """Train per-subgroup calibration factors.

    Returns calibration model with:
    - clusterer: KMeans trained on (shape + gender_encoded + height)
    - scaler: StandardScaler
    - per_cluster_factors: list of {measurement: {alpha, beta}}
    """
    feature_vectors = []
    subject_ids = []

    for sid, data in smpl_data.items():
        gender_enc = 1.0 if data['gender'] == 'male' else 0.0
        feat = np.concatenate([data['shape'], [gender_enc], [data['height'] / 200.0]])
        feature_vectors.append(feat)
        subject_ids.append(sid)

    X = np.array(feature_vectors)
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    clusterer = KMeans(n_clusters=min(n_clusters, len(X)), random_state=42)
    labels = clusterer.fit_predict(X_std)
    logger.info(f"Clustered {len(X)} subjects into {clusterer.n_clusters} groups")
    for i in range(clusterer.n_clusters):
        logger.info(f"  Cluster {i}: {int(np.sum(labels == i))} subjects")

    per_cluster_factors = []
    for cluster_idx in range(clusterer.n_clusters):
        cluster_ids = [subject_ids[i] for i in range(len(subject_ids)) if labels[i] == cluster_idx]
        factors = {}
        for key in MEASUREMENT_KEYS:
            smpl_vals = []
            gt_vals = []
            for sid in cluster_ids:
                smpl_data_point = smpl_data.get(sid)
                gt_data_point = gt_data.get(sid.split('_')[0] if '_' in sid else sid)
                if not smpl_data_point or not gt_data_point:
                    continue
                pred = smpl_data_point['measurements'].get(key, 0)
                actual = gt_data_point['measurements'].get(key, 0)
                if pred > 0 and actual > 0:
                    smpl_vals.append(pred)
                    gt_vals.append(actual)
            if len(smpl_vals) >= 3:
                X_local = np.array(smpl_vals).reshape(-1, 1)
                y_local = np.array(gt_vals)
                ridge = Ridge(alpha=1.0, fit_intercept=True)
                ridge.fit(X_local, y_local)
                factors[key] = {
                    'alpha': float(ridge.coef_[0]),
                    'beta': float(ridge.intercept_),
                    'n_samples': len(smpl_vals),
                }
                logger.info(f"  Cluster {cluster_idx}, {key}: alpha={factors[key]['alpha']:.3f}, "
                           f"beta={factors[key]['beta']:.1f} (n={len(smpl_vals)})")
            else:
                factors[key] = {'alpha': 1.0, 'beta': 0.0, 'n_samples': 0}
        per_cluster_factors.append(factors)

    return {
        'clusterer': clusterer,
        'scaler': scaler,
        'per_cluster_factors': per_cluster_factors,
        'n_clusters': clusterer.n_clusters,
        'feature_names': [f'beta{i}' for i in range(10)] + ['gender_enc', 'height_norm'],
    }


def main():
    parser = argparse.ArgumentParser(description="Train per-subgroup calibration")
    parser.add_argument('--dataset-dir', type=str, required=True)
    parser.add_argument('--ground-truth', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='api/models/priors')
    parser.add_argument('--n-clusters', type=int, default=5)
    parser.add_argument('--version', type=int, default=1)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gt_data = load_ground_truth(Path(args.ground_truth))
    smpl_data = load_smpl_from_dataset(Path(args.dataset_dir))
    model = train_subgroup_calibration(gt_data, smpl_data, args.n_clusters)
    model['version'] = args.version

    model_path = output_dir / "subgroup_calibration.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Subgroup calibration saved to {model_path}")

    summary = {}
    for ci, factors in enumerate(model['per_cluster_factors']):
        summary[f'cluster_{ci}'] = factors
    (output_dir / "subgroup_calibration.json").write_text(
        json.dumps(summary, indent=2))
    logger.info("Done")


if __name__ == "__main__":
    main()
