"""
Batch Evaluation Script for HMR Body Measurement Pipeline.

Processes front/side photo pairs and compares against ground truth tape measurements.

Usage:
    # Process pairs with ground truth
    python scripts/batch_evaluation.py \
      --input-dir ./data/validation/ \
      --gt ./data/validation/ground_truth.csv \
      --output ./data/validation/results.csv

    # Process pairs without ground truth (measurement dump only)
    python scripts/batch_evaluation.py \
      --input-dir ./data/validation/ \
      --output ./data/validation/results.csv

File naming convention:
    {subject_id}_front.jpg   (or .png)
    {subject_id}_side.jpg    (or .png)
    e.g. S001_front.jpg, S001_side.jpg

Ground truth CSV format (header required):
    subject_id,height_cm,gender,chest_cm,waist_cm,hip_cm,shoulder_cm,neck_cm,thigh_cm,ankle_cm,bicep_cm,inseam_cm
    S001,175,male,96.5,81.0,93.0,44.0,37.5,54.0,23.0,32.0,78.0
"""
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "api" / "services"))

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
PAIR_PATTERN = re.compile(r'^(.+?)_(front|side)(\..+)$', re.IGNORECASE)

# Maps CSV column names to pipeline measurement keys
GT_TO_PRED = {
    'chest_cm': 'Chest Round',
    'waist_cm': 'Waist Round',
    'hip_cm': 'Hip Round',
    'shoulder_cm': 'Shoulder',
    'neck_cm': 'Neck Round',
    'thigh_cm': 'Thigh Round',
    'ankle_cm': 'Ankle Round',
    'bicep_cm': None,
    'inseam_cm': 'Inseam',
    'calf_cm': 'Calf Round',
    'knee_cm': 'Knee Round',
    'stomach_cm': 'Stomach Round',
}


def scan_pairs(input_dir: Path) -> List[Tuple[str, Path, Path]]:
    scans = {}
    for f in input_dir.iterdir():
        if f.suffix.lower() not in IMAGE_EXTS:
            continue
        m = PAIR_PATTERN.match(f.name)
        if not m:
            continue
        subject_id, view = m.group(1), m.group(2).lower()
        scans.setdefault(subject_id, {})[view] = f

    pairs = []
    for sid, views in sorted(scans.items()):
        front = views.get('front')
        side = views.get('side')
        if front and side:
            pairs.append((sid, front, side))
        else:
            missing = 'side' if not side else 'front'
            print(f"  WARNING: {sid} missing {missing} view, skipping")
    return pairs


def parse_ground_truth(csv_path: str) -> Dict[str, dict]:
    subjects = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row['subject_id']
            subjects[sid] = {
                k: (float(v) if v.strip() else None)
                for k, v in row.items()
                if k != 'subject_id'
            }
    return subjects


def run_measurement_pipeline(
    front_path: str,
    side_path: Optional[str],
    height_cm: float,
    gender: str = 'male',
) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    try:
        import cv2
        from extract_measurements import extract_measurements_from_hmr

        front = cv2.imread(front_path)
        if front is None:
            return None, f"Cannot read front image: {front_path}"
        front_rgb = cv2.cvtColor(front, cv2.COLOR_BGR2RGB)

        side_rgb = None
        if side_path:
            side = cv2.imread(side_path)
            if side is not None:
                side_rgb = cv2.cvtColor(side, cv2.COLOR_BGR2RGB)

        start = time.time()
        measurements, vertices, landmarks, body_shape, size_rec, error = \
            extract_measurements_from_hmr(front_rgb, height_cm, gender, side_image=side_rgb)
        elapsed = time.time() - start

        if error:
            return measurements, f"Pipeline error: {error}"

        chest = measurements.get('Chest Round', 0)
        waist = measurements.get('Waist Round', 0)
        hip = measurements.get('Hip Round', 0)
        shoulder = measurements.get('Shoulder', 0)
        print(f"  {elapsed:.1f}s | Chest={chest:.1f} Waist={waist:.1f} "
              f"Hip={hip:.1f} Shoulder={shoulder:.1f} Body={body_shape} Size={size_rec}")

        return measurements, None

    except ImportError as e:
        return None, f"Missing dependency: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def compute_statistics(
    predictions: Dict[str, Dict[str, float]],
    ground_truth: Dict[str, dict],
) -> Dict[str, dict]:
    stats = {}
    for gt_key in sorted(GT_TO_PRED.keys()):
        pred_key = GT_TO_PRED[gt_key]
        if pred_key is None:
            continue

        errors = []
        for sid, gt in ground_truth.items():
            gt_val = gt.get(gt_key)
            if gt_val is None:
                continue
            pred = predictions.get(sid, {}).get(pred_key)
            if pred is None or pred == 0:
                continue
            errors.append(abs(pred - gt_val))

        if errors:
            arr = np.array(errors)
            stats[gt_key] = {
                'count': len(errors),
                'mae': float(np.mean(arr)),
                'rmse': float(np.sqrt(np.mean(arr ** 2))),
                'max_error': float(np.max(arr)),
                'min_error': float(np.min(arr)),
                'std': float(np.std(arr)),
            }

    return stats


def write_details_csv(
    path: str,
    predictions: Dict[str, Dict[str, float]],
    ground_truth: Dict[str, dict],
):
    gt_keys = [k for k in GT_TO_PRED if GT_TO_PRED[k] is not None]
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['subject_id']
        for k in gt_keys:
            header += [f'{k}_pred', f'{k}_gt', f'{k}_error']
        writer.writerow(header)

        for sid in sorted(predictions.keys()):
            pred = predictions.get(sid, {})
            gt = ground_truth.get(sid, {})
            row = [sid]
            for k in gt_keys:
                p = pred.get(GT_TO_PRED[k], '')
                g = gt.get(k, '')
                e = round(abs(p - g), 1) if p != '' and g is not None and g != '' else ''
                row += [p, g, e]
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description='Batch evaluate HMR pipeline on front/side photo pairs')
    parser.add_argument('--input-dir', required=True,
                        help='Directory containing {id}_front.jpg + {id}_side.jpg pairs')
    parser.add_argument('--gt', default=None,
                        help='CSV with subject_id,height_cm,gender,chest_cm,...')
    parser.add_argument('--output', default=None,
                        help='Output CSV path for aggregate results')
    parser.add_argument('--details', default=None,
                        help='Output CSV path for per-subject detail (default: alongside --output)')
    parser.add_argument('--height', type=float, default=None,
                        help='Default height in cm (used if not in GT)')
    parser.add_argument('--gender', default='male', choices=['male', 'female'],
                        help='Default gender')
    parser.add_argument('--max-subjects', type=int, default=None,
                        help='Max subjects to process')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: input directory not found: {input_dir}")
        sys.exit(1)

    ground_truth = {}
    if args.gt:
        ground_truth = parse_ground_truth(args.gt)
        print(f"Loaded {len(ground_truth)} ground truth entries from {args.gt}")

    pairs = scan_pairs(input_dir)
    if not pairs:
        print("No front/side pairs found. Expected naming: {id}_front.jpg + {id}_side.jpg")
        sys.exit(1)

    if args.max_subjects:
        pairs = pairs[:args.max_subjects]

    print(f"Found {len(pairs)} subject(s) in {input_dir}")
    print()

    results = {}
    errors = []
    for i, (sid, front_path, side_path) in enumerate(pairs):
        gt_entry = ground_truth.get(sid, {})
        height = gt_entry.get('height_cm', args.height)
        gender = gt_entry.get('gender', args.gender)

        if not height:
            errors.append((sid, "No height specified"))
            print(f"[{i+1}/{len(pairs)}] {sid}: SKIP (no height)")
            continue

        print(f"[{i+1}/{len(pairs)}] {sid} (height={height}cm, {gender})")

        m, err = run_measurement_pipeline(str(front_path), str(side_path), height, gender)
        if err:
            errors.append((sid, err))
            print(f"  ERROR: {err}")
            continue

        results[sid] = m

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Processed: {len(results)}/{len(pairs)} subjects")
    if errors:
        print(f"Errors ({len(errors)}):")
        for sid, err in errors:
            print(f"  {sid}: {err}")

    # Write results CSV
    if results:
        all_keys = sorted({k for m in results.values() for k in m})
        out_path = args.output
        if out_path:
            fout = open(out_path, 'w', newline='')
        else:
            fout = sys.stdout

        writer = csv.writer(fout)
        writer.writerow(['subject_id'] + all_keys)
        for sid in sorted(results):
            writer.writerow([sid] + [results[sid].get(k, '') for k in all_keys])

        if out_path:
            fout.close()
            print(f"\nResults written to: {out_path}")

        # Per-subject detail
        if ground_truth and results:
            detail_path = args.details
            if not detail_path and out_path:
                p = Path(out_path)
                detail_path = str(p.parent / f"{p.stem}_details{p.suffix}")
            if detail_path:
                write_details_csv(detail_path, results, ground_truth)
                print(f"Per-subject details written to: {detail_path}")

    # Statistics
    if ground_truth and results:
        stats = compute_statistics(results, ground_truth)
        if stats:
            print(f"\n{'─' * 65}")
            print(f"  {'Measurement':<20} {'Count':<6} {'MAE(cm)':<10} "
                  f"{'RMSE(cm)':<10} {'Max(cm)':<10}")
            print(f"{'─' * 65}")
            for k in sorted(stats.keys()):
                s = stats[k]
                bar = '#' * max(1, int(s['mae'] * 10))
                print(f"  {k:<20} {s['count']:<6} {s['mae']:<10.2f} "
                      f"{s['rmse']:<10.2f} {s['max_error']:<10.2f}  {bar}")
            print(f"{'─' * 65}")

            overall_mae = np.mean([s['mae'] for s in stats.values()])
            print(f"  {'OVERALL':<20} {'':<6} {overall_mae:<10.2f}")
            print()

    print("Done.")


if __name__ == '__main__':
    main()
