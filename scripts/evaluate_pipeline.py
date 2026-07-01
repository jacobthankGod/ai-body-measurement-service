#!/usr/bin/env python3
"""
Evaluation & Monitoring Dashboard
==================================
Compares model versions, generates accuracy reports,
and produces a JSON dashboard for monitoring.

Usage:
    # Compare two model versions on held-out data
    python scripts/evaluate_pipeline.py \
        --dataset-dir data/training_dataset/v1 \
        --output reports/eval_v1.json

    # Generate full dashboard
    python scripts/evaluate_pipeline.py \
        --dashboard \
        --output reports/dashboard.json
"""
import json
import csv
import argparse
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("EVALUATION")

MEASUREMENT_KEYS = [
    'Chest Round', 'Waist Round', 'Hip Round', 'Thigh Round',
    'Calf Round', 'Shoulder', 'Neck Round', 'Stomach Round',
]


def load_dataset_measurements(dataset_dir: Path) -> List[Dict]:
    """Load all measurements from dataset metadata."""
    records = []
    for scan_dir in sorted(dataset_dir.glob("scan_*")):
        meta_path = scan_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
            records.append({
                'scan_id': meta.get('scan_id', ''),
                'gender': meta.get('gender', 'unknown'),
                'height': meta.get('height_cm', 170),
                'measurements': meta.get('measurements', {}),
                'smpl_params': meta.get('smpl_params'),
            })
        except Exception as e:
            logger.warning(f"Error: {e}")
    return records


def load_ground_truth(csv_path: Path) -> Dict[str, Dict]:
    """Load ground truth measurements."""
    gt = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get('subject_id', '').strip()
            if not sid:
                continue
            gt[sid] = {k: float(row[k]) for k in MEASUREMENT_KEYS if row.get(k, '').strip()}
    return gt


def compute_mae(pred: Dict, gt: Dict) -> float:
    """Compute mean absolute error across available measurements."""
    errors = []
    for key in MEASUREMENT_KEYS:
        if key in pred and key in gt and pred[key] > 0 and gt[key] > 0:
            errors.append(abs(pred[key] - gt[key]))
    return float(np.mean(errors)) if errors else 0.0


def evaluate_dataset(dataset_dir: Path, gt_csv: Optional[Path] = None) -> Dict:
    """Full evaluation of a dataset against ground truth (if available)."""
    records = load_dataset_measurements(dataset_dir)
    gt_data = load_ground_truth(gt_csv) if gt_csv else {}

    results = {
        'n_scans': len(records),
        'per_gender': defaultdict(int),
    }

    if gt_data:
        per_measurement_errors = defaultdict(list)
        all_maes = []

        for rec in records:
            matched = False
            for gt_id in gt_data:
                if rec['scan_id'].startswith(gt_id) or gt_id in rec['scan_id']:
                    mae = compute_mae(rec['measurements'], gt_data[gt_id])
                    if mae > 0:
                        all_maes.append(mae)
                        for key in MEASUREMENT_KEYS:
                            if key in rec['measurements'] and key in gt_data[gt_id]:
                                if rec['measurements'][key] > 0 and gt_data[gt_id][key] > 0:
                                    per_measurement_errors[key].append(
                                        abs(rec['measurements'][key] - gt_data[gt_id][key]))
                        matched = True
                        break

        if all_maes:
            results['mae_overall'] = round(float(np.mean(all_maes)), 2)
            results['mae_std'] = round(float(np.std(all_maes)), 2)
            results['mae_per_measurement'] = {
                k: {
                    'mae': round(float(np.mean(v)), 2),
                    'std': round(float(np.std(v)), 2),
                    'n': len(v),
                }
                for k, v in per_measurement_errors.items() if v
            }
            results['n_matched'] = len(all_maes)

    for rec in records:
        results['per_gender'][rec['gender']] += 1
    results['per_gender'] = dict(results['per_gender'])

    shape_stats = defaultdict(list)
    for rec in records:
        smpl = rec.get('smpl_params', {})
        shape = smpl.get('shape', [])
        if len(shape) == 10:
            for i, val in enumerate(shape):
                shape_stats[f'beta{i}'].append(val)
    results['shape_stats'] = {
        k: {
            'mean': round(float(np.mean(v)), 3),
            'std': round(float(np.std(v)), 3),
            'p5': round(float(np.percentile(v, 5)), 3),
            'p95': round(float(np.percentile(v, 95)), 3),
        }
        for k, v in shape_stats.items() if v
    } if shape_stats else {}

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate pipeline and generate dashboard")
    parser.add_argument('--dataset-dir', type=str, help='Dataset directory to evaluate')
    parser.add_argument('--ground-truth', type=str, help='Ground truth CSV')
    parser.add_argument('--output', type=str, required=True, help='Output JSON path')
    parser.add_argument('--dashboard', action='store_true', help='Generate full dashboard')
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dataset_dir:
        results = evaluate_dataset(
            Path(args.dataset_dir),
            Path(args.ground_truth) if args.ground_truth else None
        )
        output_path.write_text(json.dumps(results, indent=2))
        logger.info(f"Evaluation saved to {output_path}")
        logger.info(f"Scans: {results['n_scans']}")
        if 'mae_overall' in results:
            logger.info(f"MAE: {results['mae_overall']} ± {results['mae_std']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
