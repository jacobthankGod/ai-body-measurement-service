"""
PVE-T-SC Analysis for SSP-3D Dataset
======================================
Computes Per-Vertex Error with Scale Correction (PVE-T-SC) between HMR-predicted
and ground truth SMPL meshes from the SSP-3D dataset.

Processes all images in a single TF session for efficiency.

Usage:
    python scripts/compute_pve.py --max-subjects 50 --output ./data/ssp3d/pve_results.csv
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

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "api" / "services"))

# Ground truth SMPL template for T-pose reconstruction
V_TEMPLATE_PATH = PROJECT_ROOT / "models" / "v_template.npy"
SHAPEDIRS_PATH = PROJECT_ROOT / "models" / "shapedirs.npy"

# SSP-3D dataset paths
SSP3D_DIR = PROJECT_ROOT / "data" / "ssp3d" / "ssp_3d"
LABELS_PATH = SSP3D_DIR / "labels.npz"
IMAGES_DIR = SSP3D_DIR / "images"


def load_smpl_template():
    v_template = np.load(str(V_TEMPLATE_PATH))
    shapedirs = np.load(str(SHAPEDIRS_PATH))
    return v_template, shapedirs


def reconstruct_tpose(betas: np.ndarray, v_template: np.ndarray,
                       shapedirs: np.ndarray) -> np.ndarray:
    return v_template + (shapedirs @ betas).reshape(-1, 3)


def scale_and_translation_transform(P: np.ndarray, T: np.ndarray) -> np.ndarray:
    P_mean = np.mean(P, axis=0, keepdims=True)
    P_trans = P - P_mean
    P_scale = np.sqrt(np.sum(P_trans ** 2) / P.shape[0])
    P_normalised = P_trans / P_scale if P_scale > 1e-10 else P_trans
    T_mean = np.mean(T, axis=0, keepdims=True)
    T_scale = np.sqrt(np.sum((T - T_mean) ** 2) / T.shape[0])
    return P_normalised * T_scale + T_mean


def compute_pve(pred_verts: np.ndarray, gt_verts: np.ndarray) -> float:
    errors = np.linalg.norm(pred_verts - gt_verts, axis=-1)
    return float(np.mean(errors) * 100)


def compute_pve_sc(pred_verts: np.ndarray, gt_verts: np.ndarray) -> float:
    pred_aligned = scale_and_translation_transform(pred_verts, gt_verts)
    errors = np.linalg.norm(pred_aligned - gt_verts, axis=-1)
    return float(np.mean(errors) * 100)


def create_hmr_pipeline():
    """Create a persistent HMR TF pipeline (model loaded once)."""
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


def run_single(image_bgr: np.ndarray, height_cm: float,
               engine, model, sess) -> Tuple[Optional[Dict], Optional[np.ndarray]]:
    """Run HMR on one image using a persistent pipeline."""
    import cv2
    h, w = image_bgr.shape[:2]
    if max(h, w) > 800:
        scale_f = 800 / max(h, w)
        image_bgr = cv2.resize(image_bgr, (int(w * scale_f), int(h * scale_f)))
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_normalized = 2 * ((img_resized / 255.0) - 0.5)
    img_batch = np.expand_dims(img_normalized, 0)

    feed_dict = {model.images: img_batch}
    results = sess.run(model.outputs, feed_dict=feed_dict)
    theta = results['theta'][0]
    vertices = results['verts'][0]

    # T-pose reconstruction
    shapes = np.array(theta[75:85], dtype=np.float64).reshape(10)
    v_measure = engine._v_template + (engine._shapedirs @ shapes).reshape(-1, 3)

    # Measurements
    measurements_3d = engine._calculate_from_indices(v_measure, height_cm, 'male')
    gender_key = MALE_KEYS
    final_measurements = {key: measurements_3d.get(key, 0.0) for key in gender_key}

    return final_measurements, v_measure


def main():
    parser = argparse.ArgumentParser(description='PVE-T-SC analysis on SSP-3D')
    parser.add_argument('--max-subjects', type=int, default=50,
                        help='Number of subjects to process')
    parser.add_argument('--output', default=None,
                        help='Output CSV path for PVE results')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for subject selection')
    parser.add_argument('--no-batch', action='store_true',
                        help='Use per-image TF init (slower but more isolated)')
    args = parser.parse_args()

    # Load SMPL template
    print("Loading SMPL template...")
    v_template, shapedirs = load_smpl_template()

    # Load SSP-3D labels
    print(f"Loading SSP-3D labels from {LABELS_PATH}...")
    labels = np.load(str(LABELS_PATH))
    n_subjects = len(labels['shapes'])
    print(f"Found {n_subjects} subjects")

    # Select subset
    rng = np.random.RandomState(args.seed)
    indices = rng.choice(n_subjects, min(args.max_subjects, n_subjects), replace=False)
    indices = sorted(indices)
    n = len(indices)
    print(f"Processing {n} subjects...")

    # Import needed constants
    from extract_measurements import MALE_KEYS, FEMALE_KEYS, extract_measurements_from_hmr

    # Build persistent pipeline (saves ~5x on 311 subjects)
    engine, model, sess, graph = None, None, None, None
    if not args.no_batch and n > 5:
        print("Creating persistent HMR pipeline...")
        engine, model, sess, graph = create_hmr_pipeline()
        print("Pipeline ready.")
    else:
        print("Using per-image TF init.")

    print(f"\n{'#':>4} | {'Subject':<50} | {'Ht':>4} | {'PVE':>7} | {'PVE-SC':>7} | {'Time':>6}")
    print("-" * 90)

    results = []
    start_total = time.time()

    for idx, subject_idx in enumerate(indices):
        fname = str(labels['fnames'][subject_idx])
        gt_betas = labels['shapes'][subject_idx]
        gt_gender_str = str(labels['genders'][subject_idx])
        gt_gender = 'female' if gt_gender_str == 'f' else 'male'

        # Reconstruct GT T-pose mesh
        gt_mesh = reconstruct_tpose(gt_betas, v_template, shapedirs)
        gt_height_m = gt_mesh[:, 1].max() - gt_mesh[:, 1].min()
        gt_height_cm = gt_height_m * 100

        # Skip if image doesn't exist
        img_path = IMAGES_DIR / fname
        if not img_path.exists():
            print(f"{idx+1:>4} | {fname:<50} | SKIP (no image)")
            continue

        start = time.time()

        if engine is not None and model is not None:
            # Persistent pipeline
            import cv2
            try:
                image_bgr = cv2.imread(str(img_path))
                if image_bgr is None:
                    print(f"{idx+1:>4} | {fname:<50} | ERROR: cannot read")
                    continue

                h, w = image_bgr.shape[:2]
                if max(h, w) > 800:
                    scale_f = 800 / max(h, w)
                    image_bgr = cv2.resize(image_bgr, (int(w * scale_f), int(h * scale_f)))
                img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
                img_resized = cv2.resize(img_rgb, (224, 224))
                img_normalized = 2 * ((img_resized / 255.0) - 0.5)
                img_batch = np.expand_dims(img_normalized, 0)

                with graph.as_default():
                    out = model.predict_dict(img_batch)

                theta = out['theta'][0]
                verts = out['verts'][0]

                shapes_param = np.array(theta[75:85], dtype=np.float64).reshape(10)
                pred_mesh = engine._v_template + (engine._shapedirs @ shapes_param).reshape(-1, 3)

            except Exception as e:
                print(f"{idx+1:>4} | {fname:<50} | ERROR: {e}")
                continue
        else:
            # Per-image TF init (fallback)
            import cv2
            image_bgr = cv2.imread(str(img_path))
            if image_bgr is None:
                print(f"{idx+1:>4} | {fname:<50} | ERROR: cannot read")
                continue
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            meas, _, _, _, _, error, pred_mesh = extract_measurements_from_hmr(
                image_rgb, gt_height_cm, gt_gender)
            if error or pred_mesh is None:
                print(f"{idx+1:>4} | {fname:<50} | ERROR: {error}")
                continue

        elapsed = time.time() - start

        # Compute PVE
        pve = compute_pve(pred_mesh, gt_mesh)
        pve_sc = compute_pve_sc(pred_mesh, gt_mesh)

        print(f"{idx+1:>4} | {fname:<50} | {gt_height_cm:>4.0f} | "
              f"{pve:>6.2f} | {pve_sc:>6.2f} | {elapsed:>5.1f}s")

        results.append({
            'subject': fname,
            'height_cm': round(gt_height_cm, 1),
            'gender': gt_gender,
            'pve_cm': round(pve, 2),
            'pve_sc_cm': round(pve_sc, 2),
            'pve_mm': round(pve * 10, 2),
            'pve_sc_mm': round(pve_sc * 10, 2),
        })

        gc.collect()

        # Write incremental results
        if args.output and (idx + 1) % 25 == 0:
            out_path = Path(args.output)
            with open(out_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'subject', 'height_cm', 'gender', 'pve_cm', 'pve_sc_cm',
                    'pve_mm', 'pve_sc_mm'])
                writer.writeheader()
                writer.writerows(results)

    total_elapsed = time.time() - start_total

    # Cleanup
    if sess is not None:
        sess.close()
    del model, sess, graph
    gc.collect()

    # Summary
    if results:
        pve_vals = [r['pve_cm'] for r in results]
        pve_sc_vals = [r['pve_sc_cm'] for r in results]
        print(f"\n{'=' * 60}")
        print(f"Processed {len(results)}/{n} subjects in {total_elapsed:.1f}s")
        print(f"Mean PVE:    {np.mean(pve_vals):.2f} cm  (SD={np.std(pve_vals):.2f})")
        print(f"Mean PVE-SC: {np.mean(pve_sc_vals):.2f} cm  (SD={np.std(pve_sc_vals):.2f})")
        print(f"Min PVE-SC:  {np.min(pve_sc_vals):.2f} cm")
        print(f"Max PVE-SC:  {np.max(pve_sc_vals):.2f} cm")

        if args.output:
            out_path = Path(args.output)
            with open(out_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'subject', 'height_cm', 'gender', 'pve_cm', 'pve_sc_cm',
                    'pve_mm', 'pve_sc_mm'])
                writer.writeheader()
                writer.writerows(results)
            print(f"Results written to: {out_path}")

    print("Done.")


if __name__ == '__main__':
    main()
