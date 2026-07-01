#!/usr/bin/env python3
"""
Silhouette Consistency Measurement
===================================
Computes IoU (Intersection over Union) between the HMR-projected SMPL
silhouette and the input image mask (or estimated foreground).

Used for:
1. Evaluating HMR fit quality at scan time
2. Flagging scans with poor silhouette alignment for retake
3. (Future) Shape optimization signal

Usage:
    python scripts/compute_silhouette_consistency.py \
        --image data/training_dataset/v1/scan_0001/front.jpg \
        --smpl-params '{"shape": [...], "pose": [...], "camera": [...]}' \
        [--mask data/training_dataset/v1/scan_0001/mask.png]

    # Batch evaluation on a dataset directory:
    python scripts/compute_silhouette_consistency.py \
        --dataset-dir data/training_dataset/v1 \
        --output reports/silhouette_scores.json
"""
import json
import argparse
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SILHOUETTE")


def project_smpl(vertices: np.ndarray, camera: np.ndarray,
                 img_shape: Tuple[int, int]) -> np.ndarray:
    """Project SMPL vertices to 2D image plane using weak-perspective camera.
    Returns binary silhouette mask (H, W).
    """
    from skimage.draw import polygon
    s, tx, ty = camera  # scale, translation x, translation y
    h, w = img_shape[:2]
    points_2d = vertices[:, :2].copy()
    points_2d[:, 0] = (points_2d[:, 0] * s + tx) * w / 2 + w / 2
    points_2d[:, 1] = (points_2d[:, 1] * s + ty) * h / 2 + h / 2
    return points_2d.astype(np.int32)


def compute_iou(mask_pred: np.ndarray, mask_gt: np.ndarray) -> float:
    """Compute IoU between predicted and ground-truth binary masks."""
    intersection = np.logical_and(mask_pred, mask_gt).sum()
    union = np.logical_or(mask_pred, mask_gt).sum()
    if union == 0:
        return 1.0
    return float(intersection / union)


def silhouette_consistency_from_meta(meta_path: Path) -> Optional[Dict]:
    """Compute silhouette consistency from a dataset scan's metadata + files."""
    try:
        meta = json.loads(meta_path.read_text())
        img_path = meta_path.parent / "front.jpg"
        src_img_path = img_path
        if not src_img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            return None

        smpl = meta.get('smpl_params')
        if not smpl or 'shape' not in smpl or 'pose' not in smpl or 'camera' not in smpl:
            logger.warning(f"No SMPL params in {meta_path}")
            return None

        shape = np.array(smpl['shape'], dtype=np.float64)
        pose = np.array(smpl['pose'], dtype=np.float64)
        camera = np.array(smpl['camera'], dtype=np.float64)

        from skimage.io import imread
        img = imread(str(src_img_path))
        if img.ndim == 3:
            img = img[:, :, 0] if img.shape[2] == 4 else img.mean(axis=2)

        mask_gt = img > 30  # simple threshold
        if mask_gt.sum() < 100:
            logger.warning(f"Foreground too small in {src_img_path}")
            return None

        from api.services.extract_measurements import HMRMasterEngine
        engine = HMRMasterEngine()
        if engine._v_template is None or engine._shapedirs is None:
            logger.warning("SMPL template not loaded")
            return None
        v_shaped = engine._v_template + (engine._shapedirs @ shape).reshape(-1, 3)
        points_2d = project_smpl(v_shaped, camera, img.shape[:2])

        from skimage.draw import polygon
        h, w = img.shape[:2]
        mask_pred = np.zeros((h, w), dtype=bool)
        try:
            rr, cc = polygon(points_2d[:, 1], points_2d[:, 0], (h, w))
            mask_pred[rr, cc] = True
        except Exception as e:
            logger.warning(f"Polygon fill failed: {e}")
            return None

        iou = compute_iou(mask_pred, mask_gt)
        overlap = np.logical_and(mask_pred, mask_gt).sum() / max(mask_gt.sum(), 1)
        return {
            'scan_id': meta['scan_id'],
            'iou': round(iou, 4),
            'overlap': round(overlap, 4),
            'foreground_pixels': int(mask_gt.sum()),
            'silhouette_pixels': int(mask_pred.sum()),
        }
    except Exception as e:
        logger.warning(f"Error processing {meta_path}: {e}")
        return None


def batch_evaluate(dataset_dir: Path, output_path: Path):
    """Run silhouette consistency across an entire dataset."""
    results = []
    scan_dirs = sorted(dataset_dir.glob("scan_*"))
    logger.info(f"Evaluating silhouette consistency on {len(scan_dirs)} scans...")
    for scan_dir in scan_dirs:
        meta_path = scan_dir / "metadata.json"
        if not meta_path.exists():
            continue
        result = silhouette_consistency_from_meta(meta_path)
        if result:
            results.append(result)

    if results:
        ious = [r['iou'] for r in results]
        logger.info(f"\nResults ({len(results)} scans):")
        logger.info(f"  Mean IoU: {np.mean(ious):.4f}")
        logger.info(f"  Median IoU: {np.median(ious):.4f}")
        logger.info(f"  Std IoU: {np.std(ious):.4f}")
        logger.info(f"  Min IoU: {np.min(ious):.4f}")
        logger.info(f"  Max IoU: {np.max(ious):.4f}")
        logger.info(f"  IoU < 0.5: {sum(1 for i in ious if i < 0.5)} scans")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        logger.info(f"Results saved to {output_path}")
    else:
        logger.warning("No results collected")


def main():
    parser = argparse.ArgumentParser(description="Compute silhouette consistency")
    parser.add_argument('--image', type=str, help='Single input image path')
    parser.add_argument('--smpl-params', type=str, help='SMPL params JSON string')
    parser.add_argument('--mask', type=str, help='Ground truth mask path')
    parser.add_argument('--dataset-dir', type=str, help='Dataset directory for batch eval')
    parser.add_argument('--output', type=str, default='reports/silhouette_scores.json')
    args = parser.parse_args()

    if args.dataset_dir:
        batch_evaluate(Path(args.dataset_dir), Path(args.output))
    elif args.image and args.smpl_params:
        from skimage.io import imread
        img = imread(args.image)
        smpl = json.loads(args.smpl_params)
        shape = np.array(smpl['shape'], dtype=np.float64)
        camera = np.array(smpl['camera'], dtype=np.float64)
        from api.services.extract_measurements import HMRMasterEngine
        engine = HMRMasterEngine()
        if engine._v_template is not None and engine._shapedirs is not None:
            v_shaped = engine._v_template + (engine._shapedirs @ shape).reshape(-1, 3)
            points_2d = project_smpl(v_shaped, camera, img.shape[:2])
            h, w = img.shape[:2]
            mask_pred = np.zeros((h, w), dtype=bool)
            rr, cc = polygon(points_2d[:, 1], points_2d[:, 0], (h, w))
            mask_pred[rr, cc] = True
            mask_gt = imread(args.mask) > 30 if args.mask else (img > 30)
            iou = compute_iou(mask_pred, mask_gt)
            print(json.dumps({'iou': round(iou, 4)}))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
