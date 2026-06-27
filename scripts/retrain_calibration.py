"""
Retrain Measurement Calibration Factors
=========================================
Loads HMR predictions + ground truth from comprehensive evaluation results
and fits new per-measurement, per-gender linear calibration factors using
ridge regression.

Usage:
    python scripts/retrain_calibration.py --input data/comprehensive_eval_results.csv --output api/services/calibration_factors.json
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Measurements with known GT from our datasets
MEASUREMENTS = ['Chest Round', 'Waist Round', 'Hip Round', 'Shoulder',
                'Neck Round', 'Thigh Round', 'Calf Round', 'Bicep Round',
                'Bust Round', 'Stomach Round']


def load_evaluation(csv_path: str) -> Dict[str, Dict[str, List[Tuple[float, float]]]]:
    """
    Load evaluation results and group by (gender, measurement).
    Returns {gender: {measurement: [(smpl_pred, gt), ...]}}
    """
    data = defaultdict(lambda: defaultdict(list))
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            gender = row.get('gender', 'male').lower().strip()
            if gender not in ('male', 'female'):
                # Try to infer from subject or skip
                continue
            meas = row['measurement']
            if meas not in MEASUREMENTS:
                continue
            pred = float(row['predicted'])
            gt = float(row['ground_truth'])
            if pred > 0 and gt > 0:
                data[gender][meas].append((pred, gt))
    return dict(data)


def compute_factors(values: List[Tuple[float, float]],
                    ridge_alpha: float = 1.0) -> List[float]:
    """Ridge regression: real = alpha * smpl + beta"""
    if len(values) < 2:
        return [1.0, 0.0]
    X = np.array([v[0] for v in values])
    y = np.array([v[1] for v in values])
    n = len(X)
    X_design = np.column_stack([X, np.ones(n)])
    I = np.eye(2)
    coef = np.linalg.inv(X_design.T @ X_design + ridge_alpha * I) @ X_design.T @ y
    return [round(float(coef[0]), 4), round(float(coef[1]), 4)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(PROJECT_ROOT / "data" / "comprehensive_eval_results.csv"))
    parser.add_argument('--output', default=str(PROJECT_ROOT / "api" / "services" / "calibration_factors.json"))
    parser.add_argument('--ridge-alpha', type=float, default=0.5,
                        help='L2 regularization (lower = less shrinkage, min 0.01)')
    args = parser.parse_args()

    print("=" * 70)
    print("CALIBRATION FACTOR RETRAINING")
    print("=" * 70)

    # Load existing factors from measurement_calibration.py as baseline
    from api.services.measurement_calibration import _default_factors
    default_factors = _default_factors()
    print(f"\nExisting factors from: measurement_calibration.py (6 UniData subjects)")

    # Load evaluation results
    print(f"\nLoading evaluation from: {args.input}")
    data = load_evaluation(str(args.input))
    print(f"\nSubjects found:")
    for gender in ['male', 'female']:
        if gender in data:
            for meas in MEASUREMENTS:
                if meas in data[gender]:
                    print(f"  {gender:8s} {meas:15s}: {len(data[gender][meas]):4d} pairs")

    # Compute new factors per gender per measurement
    new_factors: Dict[str, Dict[str, List[float]]] = {'male': {}, 'female': {}}
    for gender in ['male', 'female']:
        gender_factors = data.get(gender, {})
        default_gender = default_factors.get(gender, {})
        all_meas = set(list(gender_factors.keys()) + list(default_gender.keys()))
        for meas in sorted(all_meas):
            if meas in gender_factors and len(gender_factors[meas]) >= 2:
                alpha, beta = compute_factors(gender_factors[meas], args.ridge_alpha)
                new_factors[gender][meas] = [alpha, beta]
                old = default_gender.get(meas, [1.0, 0.0])
                delta_alpha = alpha - old[0]
                delta_beta = beta - old[1]
                print(f"  {gender:8s} {meas:15s}: "
                      f"alpha={alpha:.4f} (Δ{delta_alpha:+.4f}), "
                      f"beta={beta:.4f} (Δ{delta_beta:+.4f})  "
                      f"[n={len(gender_factors[meas])}]")
            elif meas in default_gender:
                new_factors[gender][meas] = default_gender[meas]
                print(f"  {gender:8s} {meas:15s}: {default_gender[meas]} (unchanged, no new data)")

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(new_factors, f, indent=2)
    print(f"\nSaved new factors to: {output_path}")
    print(f"\nNew factors:")
    print(json.dumps(new_factors, indent=2))


if __name__ == '__main__':
    main()
