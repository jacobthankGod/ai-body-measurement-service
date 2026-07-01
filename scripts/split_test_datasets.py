"""
Split Tests on Real Dataset Images
====================================
Runs HMR, MediaPipe, and Fusion paths on qualified images from
SSP-3D (tight sportswear), HBW (SMPL-X), and UniData (front+side pairs).

Compares each path's output and validates against ground truth.

Usage:
    python scripts/split_test_datasets.py --max 3
"""
import argparse
import csv
import gc
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
if not hasattr(np, 'bool'):
    np.bool = bool; np.int = int; np.float = float; np.complex = complex; np.object = object; np.str = str; np.unicode = str
import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS = []  # Global accumulator


def load_ground_truth(csv_path: str) -> Dict[str, dict]:
    """Load ground_truth.csv into {subject_id: {measurement: value}}."""
    gt = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row['subject_id']
            gt[sid] = dict(row)
            # Convert numeric fields
            for k, v in row.items():
                if k in ('subject_id', 'gender'):
                    continue
                try:
                    gt[sid][k] = float(v) if v else 0.0
                except ValueError:
                    pass
    return gt


def compare_vs_gt(pred: Dict[str, float], gt: Dict[str, dict],
                  subject_id: str, height_cm: float,
                  gender: str, source: str, image_name: str) -> None:
    """Compare predictions against ground truth and accumulate results."""
    gt_meas = gt.get(subject_id, {})
    for meas_key, pred_val in pred.items():
        # Map prediction keys to ground truth keys
        gt_key_map = {
            'Chest Round': 'chest_cm', 'Bust Round': 'chest_cm',
            'Waist Round': 'waist_cm', 'Hip Round': 'hip_cm',
            'Shoulder': 'shoulder_cm', 'Neck Round': 'neck_cm',
            'Thigh Round': 'thigh_cm', 'Calf Round': 'calf_cm',
            'Bicep Round': 'bicep_cm',
        }
        gt_key = gt_key_map.get(meas_key)
        if gt_key and gt_key in gt_meas:
            gt_val = float(gt_meas[gt_key])
            if gt_val > 0 and pred_val > 0:
                err = abs(pred_val - gt_val)
                RESULTS.append({
                    'dataset': Path(image_name).parent.name,
                    'image': image_name,
                    'source': source,
                    'subject': subject_id,
                    'gender': gender,
                    'height': height_cm,
                    'measurement': meas_key,
                    'predicted': round(pred_val, 2),
                    'ground_truth': round(gt_val, 2),
                    'absolute_error': round(err, 2),
                    'percent_error': round(err / gt_val * 100, 1),
                })


def run_ssp3d_tests(max_subjects: int):
    """Run split tests on SSP-3D (tight sportswear — best case for HMR)."""
    print("\n" + "=" * 70)
    print("SSP-3D SPLIT TESTS (tight sportswear)")
    print("=" * 70)

    from api.services.extract_measurements import extract_measurements_from_hmr
    from api.services.measurement_engine import extract_measurements_from_dual_photos
    from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_extract

    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "ssp3d" / "ground_truth.csv"))
    images_dir = PROJECT_ROOT / "data" / "ssp3d" / "ssp_3d" / "images"
    image_files = sorted(images_dir.glob("*.png"))

    if not image_files:
        print("No SSP-3D images found")
        return

    # Select diverse subjects (one per person)
    seen_subjects = set()
    selected = []
    for img_path in image_files:
        parts = img_path.stem.split('_')
        # Subject key: sport_vid_clip_person
        subj_key = '_'.join(p for p in parts
                           if not p.startswith('frame'))
        if subj_key not in seen_subjects and len(selected) < max_subjects:
            seen_subjects.add(subj_key)
            selected.append(img_path)

    print(f"Selected {len(selected)} images from SSP-3D")

    for img_path in selected:
        print(f"\n  --- {img_path.name} ---")
        import cv2
        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            print(f"  SKIP: cannot read")
            continue
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Get height/gender from GT (use frame-level ID)
        frame_id = img_path.stem
        sid = frame_id  # SSP-3D uses frame names as IDs
        gt_row = gt.get(sid, {})
        height_cm = float(gt_row.get('height_cm', 175))
        gender = str(gt_row.get('gender', 'male'))

        # Path A: HMR
        try:
            hmr_result = extract_measurements_from_hmr(
                image_rgb, height_cm, gender)
            hmr_meas = hmr_result[0]
            hmr_error = hmr_result[5]
            if hmr_error:
                print(f"  HMR FAILED: {hmr_error}")
            elif hmr_meas:
                print(f"  HMR: ", {k: f"{v:.1f}" for k, v in
                      hmr_meas.items() if v > 0})
                compare_vs_gt(hmr_meas, gt, sid, height_cm, gender,
                             'HMR', f"ssp3d/{img_path.name}")
        except Exception as e:
            print(f"  HMR ERROR: {e}")

        # Path B: MediaPipe
        try:
            mp_meas, mp_err = mp_extract(image_rgb, image_rgb,
                                          height_cm, gender)
            if mp_meas:
                print(f"  MP:   ", {k: f"{v:.1f}" for k, v in
                      mp_meas.items() if v > 0})
                compare_vs_gt(mp_meas, gt, sid, height_cm, gender,
                             'MediaPipe', f"ssp3d/{img_path.name}")
        except Exception as e:
            print(f"  MP ERROR: {e}")

        # Path C: Fusion
        try:
            fusion_result = extract_measurements_from_dual_photos(
                image_rgb, image_rgb, height_cm, gender)
            if fusion_result:
                # Extract relevant measurement keys
                fusion_meas = {}
                meas_map = {
                    'chest_round': 'Chest Round',
                    'waist_round': 'Waist Round',
                    'hip_round': 'Hip Round',
                    'shoulder': 'Shoulder',
                    'neck_round': 'Neck Round',
                    'thigh_round': 'Thigh Round',
                    'calf_round': 'Calf Round',
                    'bicep_round': 'Bicep Round',
                }
                for fk, mk in meas_map.items():
                    if fk in fusion_result:
                        fusion_meas[mk] = float(fusion_result[fk])
                print(f"  Fusion:", {k: f"{v:.1f}" for k, v in
                      fusion_meas.items() if v > 0})
                compare_vs_gt(fusion_meas, gt, sid, height_cm, gender,
                             'Fusion', f"ssp3d/{img_path.name}")
        except Exception as e:
            print(f"  Fusion ERROR: {e}")

        gc.collect()


def run_hbw_tests(max_subjects: int):
    """Run split tests on HBW (SMPL-X ground truth)."""
    print("\n" + "=" * 70)
    print("HBW SPLIT TESTS (SMPL-X mesh validation)")
    print("=" * 70)

    from api.services.extract_measurements import extract_measurements_from_hmr

    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "hbw" / "ground_truth.csv"))
    images_dir = PROJECT_ROOT / "data" / "hbw" / "HBW_low_resolution" / "images" / "val_small_resolution"

    selected = []
    for subj_id in list(gt.keys())[:max_subjects]:
        subj_dir = images_dir / subj_id
        if subj_dir.exists():
            images = sorted(subj_dir.glob("*.png"))
            if images:
                selected.append((subj_id, images[0]))  # First frame per subject

    print(f"Selected {len(selected)} subjects from HBW")

    for subj_id, img_path in selected:
        print(f"\n  --- Subject {subj_id}: {img_path.name} ---")
        import cv2
        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            print(f"  SKIP: cannot read")
            continue
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        gt_row = gt.get(subj_id, {})
        height_cm = float(gt_row.get('height_cm', 175))
        gender = 'male'  # HBW labels are 'neutral'

        # HMR only (HBW has no MP/fusion ground truth comparison)
        try:
            hmr_result = extract_measurements_from_hmr(
                image_rgb, height_cm, gender)
            hmr_meas = hmr_result[0]
            hmr_error = hmr_result[5]
            if hmr_error:
                print(f"  HMR FAILED: {hmr_error}")
            elif hmr_meas:
                print(f"  HMR: ", {k: f"{v:.1f}" for k, v in
                      hmr_meas.items() if v > 0})
                compare_vs_gt(hmr_meas, gt, subj_id, height_cm, gender,
                             'HMR', f"hbw/{subj_id}/{img_path.name}")
        except Exception as e:
            print(f"  HMR ERROR: {e}")

        gc.collect()


def run_unidata_tests():
    """Run split tests on UniData (front+side pairs, most realistic)."""
    print("\n" + "=" * 70)
    print("UniData SPLIT TESTS (front+side photos)")
    print("=" * 70)

    from api.services.extract_measurements import extract_measurements_from_hmr
    from api.services.measurement_engine import extract_measurements_from_dual_photos
    from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_extract

    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "unidata" / "ground_truth.csv"))
    data_dir = PROJECT_ROOT / "data" / "unidata"

    for subj_id in ['S001', 'S002', 'S003', 'S004', 'S005', 'S006']:
        front_path = data_dir / f"{subj_id}_front.jpg"
        side_path = data_dir / f"{subj_id}_side.jpg"

        if not front_path.exists() or not side_path.exists():
            print(f"  {subj_id}: SKIP (missing images)")
            continue

        print(f"\n  --- {subj_id} ---")
        import cv2
        front_bgr = cv2.imread(str(front_path))
        side_bgr = cv2.imread(str(side_path))
        front_rgb = cv2.cvtColor(front_bgr, cv2.COLOR_BGR2RGB) if front_bgr is not None else None
        side_rgb = cv2.cvtColor(side_bgr, cv2.COLOR_BGR2RGB) if side_bgr is not None else None

        if front_rgb is None:
            print(f"  SKIP: cannot read front image")
            continue

        gt_row = gt.get(subj_id, {})
        height_cm = float(gt_row.get('height_cm', 170))
        gender = str(gt_row.get('gender', 'male'))

        # Path A: HMR (with side image)
        try:
            hmr_result = extract_measurements_from_hmr(
                front_rgb, height_cm, gender, side_image=side_rgb)
            hmr_meas = hmr_result[0]
            hmr_error = hmr_result[5]
            if hmr_error:
                print(f"  HMR FAILED: {hmr_error}")
            elif hmr_meas:
                print(f"  HMR: ", {k: f"{v:.1f}" for k, v in
                      hmr_meas.items() if v > 0})
                compare_vs_gt(hmr_meas, gt, subj_id, height_cm, gender,
                             'HMR', f"unidata/{subj_id}")
        except Exception as e:
            print(f"  HMR ERROR: {e}")

        # Path B: MediaPipe
        if side_rgb is not None:
            try:
                mp_meas, mp_err = mp_extract(front_rgb, side_rgb,
                                              height_cm, gender)
                if mp_meas:
                    print(f"  MP:   ", {k: f"{v:.1f}" for k, v in
                          mp_meas.items() if v > 0})
                    compare_vs_gt(mp_meas, gt, subj_id, height_cm, gender,
                                 'MediaPipe', f"unidata/{subj_id}")
            except Exception as e:
                print(f"  MP ERROR: {e}")

        # Path C: Fusion
        if side_rgb is not None:
            try:
                fusion_result = extract_measurements_from_dual_photos(
                    front_rgb, side_rgb, height_cm, gender)
                if fusion_result:
                    fusion_meas = {}
                    meas_map = {
                        'chest_round': 'Chest Round',
                        'waist_round': 'Waist Round',
                        'hip_round': 'Hip Round',
                        'shoulder': 'Shoulder',
                        'neck_round': 'Neck Round',
                        'thigh_round': 'Thigh Round',
                        'calf_round': 'Calf Round',
                        'bicep_round': 'Bicep Round',
                    }
                    for fk, mk in meas_map.items():
                        if fk in fusion_result:
                            fusion_meas[mk] = float(fusion_result[fk])
                    print(f"  Fusion:", {k: f"{v:.1f}" for k, v in
                          fusion_meas.items() if v > 0})
                    compare_vs_gt(fusion_meas, gt, subj_id, height_cm, gender,
                                 'Fusion', f"unidata/{subj_id}")
            except Exception as e:
                print(f"  Fusion ERROR: {e}")

        gc.collect()


def print_summary():
    """Print summary of all split test results."""
    if not RESULTS:
        print("\nNo results to summarize.")
        return

    import pandas as pd
    df = pd.DataFrame(RESULTS)

    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    # Per-source stats
    print("\n--- Per Pipeline Path ---")
    for source in ['HMR', 'MediaPipe', 'Fusion']:
        subset = df[df['source'] == source]
        if len(subset) == 0:
            continue
        mean_err = subset['absolute_error'].mean()
        median_err = subset['absolute_error'].median()
        count = len(subset)
        print(f"  {source:10s}: {count:3d} comparisons, "
              f"MAE={mean_err:5.1f}cm, MedAE={median_err:5.1f}cm")

    # Per-measurement stats
    print("\n--- Per Measurement (all paths) ---")
    for meas in ['Chest Round', 'Waist Round', 'Hip Round',
                  'Shoulder', 'Neck Round', 'Thigh Round',
                  'Calf Round', 'Bicep Round']:
        subset = df[df['measurement'] == meas]
        if len(subset) == 0:
            continue
        mean_err = subset['absolute_error'].mean()
        count = len(subset)
        print(f"  {meas:15s}: {count:3d} comparisons, MAE={mean_err:5.1f}cm")

    # Per-dataset stats
    print("\n--- Per Dataset ---")
    for ds in df['dataset'].unique():
        subset = df[df['dataset'] == ds]
        print(f"  {ds}: {len(subset)} comparisons, "
              f"MAE={subset['absolute_error'].mean():5.1f}cm")

    # HMR-only vs Fusion comparison
    print("\n--- HMR vs Fusion (same measurements) ---")
    hmr = df[df['source'] == 'HMR'].copy()
    fusion = df[df['source'] == 'Fusion'].copy()
    if len(hmr) > 0 and len(fusion) > 0:
        print(f"  HMR   MAE: {hmr['absolute_error'].mean():5.1f}cm "
              f"(n={len(hmr)})")
        print(f"  Fusion MAE: {fusion['absolute_error'].mean():5.1f}cm "
              f"(n={len(fusion)})")

    # Save detailed CSV
    out_path = Path(PROJECT_ROOT / "data" / "split_test_results.csv")
    df.to_csv(out_path, index=False)
    print(f"\nDetailed results saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Split tests on real dataset images')
    parser.add_argument('--max', type=int, default=3,
                        help='Max subjects per dataset (default: 3)')
    parser.add_argument('--datasets', nargs='+',
                        default=['ssp3d', 'hbw', 'unidata'],
                        help='Datasets to test (default: all)')
    args = parser.parse_args()

    print("=" * 70)
    print("SPLIT TESTS ON REAL DATASET IMAGES")
    print(f"Max subjects per dataset: {args.max}")
    print("=" * 70)

    if 'ssp3d' in args.datasets:
        run_ssp3d_tests(args.max)
    if 'hbw' in args.datasets:
        run_hbw_tests(args.max)
    if 'unidata' in args.datasets:
        run_unidata_tests()

    print_summary()
    print("\nDone.")


if __name__ == '__main__':
    main()
