"""
Comprehensive Measurement Accuracy Evaluation
==============================================
Runs HMR on all images from all available datasets using a persistent TF
pipeline (~1.2s/subject) and compares ALL HMR measurements against GT.

Usage:
    python scripts/comprehensive_evaluation.py [--max N] [--datasets d1 ...]
"""
import argparse
import csv
import gc
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "api" / "services"))


# =========================================================================
# PERSISTENT HMR PIPELINE (single TF session for all images)
# =========================================================================

def create_hmr_pipeline():
    """Create persistent HMR TF pipeline (model loaded once)."""
    from extract_measurements import setup_tf_bridge, HMRMasterEngine
    tf1 = setup_tf_bridge()
    engine = HMRMasterEngine()

    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)

    if not hasattr(np, 'bool'):
        np.bool = bool; np.int = int; np.float = float
        np.complex = complex; np.object = object; np.str = str; np.unicode = str

    graph = tf1.Graph()
    with graph.as_default():
        config = tf1.ConfigProto()
        config.gpu_options.allow_growth = True
        config.intra_op_parallelism_threads = 1
        config.inter_op_parallelism_threads = 1
        sess = tf1.Session(config=config, graph=graph)

        from src.RunModel import RunModel
        model = RunModel(sess=sess)
        model.prepare()

    return engine, model, sess, graph


def run_hmr(image_bgr, height_cm, engine, model, sess, gender='male'):
    """Run HMR on one image using persistent pipeline. Returns full measurements dict."""
    import cv2
    h, w = image_bgr.shape[:2]
    if max(h, w) > 800:
        scale_f = 800 / max(h, w)
        image_bgr = cv2.resize(image_bgr, (int(w * scale_f), int(h * scale_f)))
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_normalized = 2 * ((img_resized / 255.0) - 0.5)
    img_batch = np.expand_dims(img_normalized, 0)

    results = model.predict_dict(img_batch)
    vertices = results['verts'][0]

    # T-pose reconstruction
    theta = results['theta'][0]
    shapes = np.array(theta[75:85], dtype=np.float64).reshape(10)
    v_measure = engine._v_template + (engine._shapedirs @ shapes).reshape(-1, 3)

    # ALL measurements (not gender-filtered)
    all_meas = engine._calculate_from_indices(v_measure, height_cm, gender)
    return all_meas, v_measure


# =========================================================================
# GT LOADING & COMPARISON
# =========================================================================
RESULTS = []


def load_ground_truth(csv_path: str) -> Dict[str, dict]:
    gt = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row['subject_id']
            gt[sid] = dict(row)
            for k, v in row.items():
                if k in ('subject_id', 'gender'):
                    continue
                try:
                    gt[sid][k] = float(v) if v else 0.0
                except ValueError:
                    pass
    return gt


def record(dataset, image, subject, gender, height, meas, pred, gt_val):
    if pred <= 0 or gt_val <= 0:
        return
    err = abs(pred - gt_val)
    pct = err / gt_val * 100
    RESULTS.append({
        'dataset': dataset, 'image': image, 'subject': subject,
        'gender': gender, 'height': height, 'measurement': meas,
        'predicted': round(pred, 2), 'ground_truth': round(gt_val, 2),
        'absolute_error': round(err, 2), 'percent_error': round(pct, 1),
    })


def compare(pred: Dict, gt_row: dict, gt_map: Dict[str, list],
            dataset, image, subject, gender, height):
    for gt_col, hmr_keys in gt_map.items():
        gt_val = gt_row.get(gt_col, 0)
        if not gt_val or gt_val <= 0:
            continue
        for hmr_key in hmr_keys:
            pred_val = pred.get(hmr_key, 0)
            if pred_val > 0:
                record(dataset, image, subject, gender, height,
                       hmr_key, pred_val, gt_val)


# =========================================================================
# DATASET PER-DATASET GT MAPPINGS
# =========================================================================
# Each dataset has different GT columns for the same HMR measurements

UNIDATA_GT_MAP = {
    'chest_cm':     ['Chest Round', 'Bust Round'],
    'waist_cm':     ['Waist Round'],
    'hip_cm':       ['Hip Round'],
    'thigh_cm':     ['Thigh Round'],
    'bicep_cm':     ['Bicep Round'],
    'calf_cm':      ['Calf Round'],
    'stomach_cm':   ['Stomach Round'],
    'underbust_cm': ['Under Bust'],
}

SSP3D_GT_MAP = {
    'chest_cm':     ['Chest Round'],
    'waist_cm':     ['Waist Round'],
    'hip_cm':       ['Hip Round'],
    'shoulder_cm':  ['Shoulder'],
    'neck_cm':      ['Neck Round'],
    'thigh_cm':     ['Thigh Round'],
    'calf_cm':      ['Calf Round'],
    'bicep_cm':     ['Bicep Round'],
}

HBW_GT_MAP = {
    'chest_cm':     ['Chest Round'],
    'waist_cm':     ['Waist Round'],
    'hip_cm':       ['Hip Round'],
    'shoulder_cm':  ['Shoulder'],
    'neck_cm':      ['Neck Round'],
    'thigh_cm':     ['Thigh Round'],
    'calf_cm':      ['Calf Round'],
    'bicep_cm':     ['Bicep Round'],
}

MODELAGENCY_GT_MAP = {
    'chest_cm':     ['Chest Round', 'Bust Round'],
    'waist_cm':     ['Waist Round'],
    'hip_cm':       ['Hip Round'],
}


# =========================================================================
# DATASET RUNNERS
# =========================================================================

def run_unidata(engine, model, sess, max_subjects=6):
    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "unidata" / "ground_truth.csv"))
    data_dir = PROJECT_ROOT / "data" / "unidata"
    subjects = list(gt.keys())[:max_subjects]

    import cv2
    for subj_id in subjects:
        front_path = data_dir / f"{subj_id}_front.jpg"
        if not front_path.exists():
            front_path = data_dir / f"{subj_id}_front.png"
        if not front_path.exists():
            print(f"  SKIP {subj_id}: no image")
            continue

        gt_row = gt.get(subj_id, {})
        height_cm = float(gt_row.get('height_cm', 175))
        gender = gt_row.get('gender', 'male')

        image_bgr = cv2.imread(str(front_path))
        if image_bgr is None:
            print(f"  SKIP {subj_id}: unreadable")
            continue

        try:
            all_meas, _ = run_hmr(image_bgr, height_cm, engine, model, sess, gender)
            compare(all_meas, gt_row, UNIDATA_GT_MAP,
                    'unidata', f"{subj_id}_front.jpg", subj_id, gender, height_cm)
        except Exception as e:
            print(f"  ERROR {subj_id}: {e}")
        gc.collect()

    n = sum(1 for r in RESULTS if r['dataset'] == 'unidata')
    print(f"  UniData: {len(subjects)} subjects, {n} comparisons")


def run_ssp3d(engine, model, sess, max_subjects=311):
    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "ssp3d" / "ground_truth.csv"))
    images_dir = PROJECT_ROOT / "data" / "ssp3d" / "ssp_3d" / "images"
    image_files = sorted(images_dir.glob("*.png"))

    if not image_files:
        print("  No SSP-3D images")
        return

    import cv2
    count = 0
    for img_path in image_files:
        if count >= max_subjects:
            break
        frame_id = img_path.stem
        gt_row = gt.get(frame_id, {})
        if not gt_row:
            continue

        height_cm = float(gt_row.get('height_cm', 175))
        gender = gt_row.get('gender', 'male')

        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            continue

        try:
            all_meas, _ = run_hmr(image_bgr, height_cm, engine, model, sess, gender)
            compare(all_meas, gt_row, SSP3D_GT_MAP,
                    'ssp3d', img_path.name, frame_id, gender, height_cm)
            count += 1
            if count % 50 == 0:
                print(f"  SSP-3D: {count}/{min(max_subjects, len(image_files))}")
        except Exception:
            continue
        gc.collect()

    n = sum(1 for r in RESULTS if r['dataset'] == 'ssp3d')
    print(f"  SSP-3D: {count} subjects, {n} comparisons")


def run_hbw(engine, model, sess, max_subjects=10):
    gt = load_ground_truth(str(PROJECT_ROOT / "data" / "hbw" / "ground_truth.csv"))
    # Images in flat directory: 012_00000.png etc.
    images_dir = PROJECT_ROOT / "data" / "hbw"
    image_files = sorted(images_dir.glob("*.png"))
    if not image_files:
        images_dir = PROJECT_ROOT / "data" / "hbw" / "images" / "val"
        image_files = sorted(images_dir.glob("*.*"))
    if not image_files:
        print("  No HBW images")
        return

    import cv2
    subjects_seen = set()
    count = 0
    for img_path in image_files:
        parts = img_path.stem.split('_')
        subj_id = parts[0] if parts else img_path.stem
        if subj_id not in subjects_seen and len(subjects_seen) >= max_subjects:
            continue
        if subj_id in subjects_seen and count >= max_subjects * 20:
            continue

        gt_row = gt.get(subj_id, {})
        if not gt_row:
            continue
        height_cm = float(gt_row.get('height_cm', 175))
        gender = gt_row.get('gender', 'male')

        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            continue

        try:
            all_meas, _ = run_hmr(image_bgr, height_cm, engine, model, sess, gender)
            compare(all_meas, gt_row, HBW_GT_MAP,
                    'hbw', img_path.name, subj_id, gender, height_cm)
            subjects_seen.add(subj_id)
            count += 1
            if count % 100 == 0:
                print(f"  HBW: {count} images")
        except Exception:
            continue
        gc.collect()

    n = sum(1 for r in RESULTS if r['dataset'] == 'hbw')
    print(f"  HBW: {count} images, {len(subjects_seen)} subjects, {n} comparisons")


def run_modelagency(engine, model, sess, max_subjects=130):
    """Model Agency: 130 models, 980 downloaded images, bust/waist/hips GT."""
    DATA_DIR = PROJECT_ROOT / "data" / "modelagency"
    gt_path = DATA_DIR / "ground_truth_downloaded.csv"
    if not gt_path.exists():
        print("  No Model Agency GT found")
        return

    gt = load_ground_truth(str(gt_path))
    download_dir = DATA_DIR / "downloaded"

    import cv2
    subjects = sorted(gt.keys())[:max_subjects]
    count = 0
    for subj_id in subjects:
        subj_dir = download_dir / subj_id
        if not subj_dir.exists():
            continue
        images = sorted(subj_dir.glob("*.jpg"))
        if not images:
            continue

        gt_row = gt.get(subj_id, {})
        height_cm = float(gt_row.get('height_cm', 175))
        gender = gt_row.get('gender', 'male')

        # Use first image
        image_bgr = cv2.imread(str(images[0]))
        if image_bgr is None:
            continue

        try:
            all_meas, _ = run_hmr(image_bgr, height_cm, engine, model, sess, gender)
            compare(all_meas, gt_row, MODELAGENCY_GT_MAP,
                    'modelagency', images[0].name, subj_id, gender, height_cm)
            count += 1
            if count % 25 == 0:
                print(f"  Model Agency: {count}/{max_subjects}")
        except Exception:
            continue
        gc.collect()

    n = sum(1 for r in RESULTS if r['dataset'] == 'modelagency')
    print(f"  Model Agency: {count} subjects, {n} comparisons")


# =========================================================================
# REPORTING
# =========================================================================
ALL_HMR_KEYS = [
    'Shoulder', 'Neck Round', 'Chest Round', 'Bust Round', 'High Bust',
    'Under Bust', 'Stomach Round', 'Waist Round', 'Hip Round',
    'Half Length', 'Full Top Length', 'Across Back', 'Across Chest',
    'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round',
    'Trouser Waist', 'Trouser Length', 'Inseam', 'Crotch Depth',
    'Bust Point', 'Shoulder to Bust Point', 'Shoulder to Under Bust',
    'Shoulder to Waist', 'Front Waist Length', 'Back Waist Length',
    'Waist to Hip', 'Upper Hip', 'Armhole Round', 'Sleeve Length',
    'Bicep Round', 'Elbow Round', 'Wrist Round',
]


def print_summary():
    if not RESULTS:
        print("\nNo results.")
        return

    import pandas as pd
    df = pd.DataFrame(RESULTS)

    print("\n" + "=" * 80)
    print("COMPREHENSIVE HMR MEASUREMENT ACCURACY REPORT")
    print("=" * 80)
    print(f"Total comparisons: {len(df)}")
    print(f"Overall MAE: {df['absolute_error'].mean():.1f}cm")
    print(f"Overall MAPE: {df['percent_error'].mean():.1f}%")

    # Per dataset
    print("\n" + "-" * 80)
    print("PER DATASET")
    print("-" * 80)
    for ds in sorted(df['dataset'].unique()):
        sub = df[df['dataset'] == ds]
        print(f"\n  {ds.upper()} ({len(sub)} comparisons):")
        print(f"    MAE={sub['absolute_error'].mean():.1f}cm  "
              f"MAPE={sub['percent_error'].mean():.1f}%  "
              f"Subjects={sub['subject'].nunique()}  "
              f"Measurements={sub['measurement'].nunique()}")

    # Per measurement (all datasets)
    print("\n" + "-" * 80)
    print("PER MEASUREMENT (ALL DATASETS)")
    print("-" * 80)
    for meas in ALL_HMR_KEYS:
        sub = df[df['measurement'] == meas]
        if len(sub) == 0:
            continue
        print(f"  {meas:25s}: n={len(sub):4d}  "
              f"MAE={sub['absolute_error'].mean():6.1f}cm  "
              f"MAPE={sub['percent_error'].mean():5.1f}%")

    # Per measurement x dataset
    print("\n" + "-" * 80)
    print("PER MEASUREMENT × PER DATASET")
    print("-" * 80)
    for ds in sorted(df['dataset'].unique()):
        print(f"\n  --- {ds.upper()} ---")
        sub = df[df['dataset'] == ds]
        for meas in ALL_HMR_KEYS:
            ms = sub[sub['measurement'] == meas]
            if len(ms) == 0:
                continue
            print(f"    {meas:25s}: n={len(ms):3d}  "
                  f"MAE={ms['absolute_error'].mean():6.1f}cm  "
                  f"MAPE={ms['percent_error'].mean():5.1f}%")

    out = PROJECT_ROOT / "data" / "comprehensive_eval_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved to: {out}")


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None)
    parser.add_argument('--datasets', nargs='+',
                        default=['unidata', 'ssp3d', 'hbw'])
    args = parser.parse_args()

    print("=" * 80)
    print("COMPREHENSIVE HMR MEASUREMENT ACCURACY EVALUATION")
    print("Persistent TF pipeline: ~1.2s/subject")
    print("=" * 80)

    # Create persistent TF pipeline
    print("\nInitializing HMR pipeline...")
    t_init = time.time()
    engine, model, sess, graph = create_hmr_pipeline()
    print(f"  Initialized in {time.time() - t_init:.0f}s")

    # Run datasets sequentially
    for ds_name in args.datasets:
        print(f"\n{'=' * 80}")
        print(f"EVALUATING: {ds_name.upper()}")
        print(f"{'=' * 80}")
        t0 = time.time()

        if ds_name == 'unidata':
            run_unidata(engine, model, sess, max_subjects=args.max or 6)
        elif ds_name == 'ssp3d':
            run_ssp3d(engine, model, sess, max_subjects=args.max or 311)
        elif ds_name == 'hbw':
            run_hbw(engine, model, sess, max_subjects=args.max or 10)
        elif ds_name == 'modelagency':
            run_modelagency(engine, model, sess, max_subjects=args.max or 130)
        else:
            print(f"  Unknown: {ds_name}")

        print(f"  Time: {time.time() - t0:.0f}s")

    # Close session
    sess.close()
    del model, sess, graph

    print_summary()


if __name__ == '__main__':
    main()
