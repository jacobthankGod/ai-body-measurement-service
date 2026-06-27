"""
Convert HBW (Human Bodies in the Wild) dataset to batch_evaluation format.

HBW has photos of 35 subjects with ground-truth 3D body scans (SMPL-X).
Validation set (10 subjects, 781 images) has public GT.
Test set (25 subjects, 1,762 images) has images but GT not public.

Source: data/hbw/HBW_low_resolution/
  - images/val_small_resolution/{subject_id}/{Photos_Lab,Pictures_in_the_Wild}/*.png
  - images/test_small_resolution/{subject_id}/.../*.png
  - smplx/val/{subject_id}.npy (SMPL-X params)
  - smplx/val/{subject_id}.obj (SMPL-X mesh)

We process the validation set: generate measurements from GT SMPL-X meshes,
organize images, and create ground_truth.csv for batch evaluation.

Output: data/hbw/
  - {subject_id}_{photo_id}.png
  - ground_truth.csv
"""
import csv
import sys
import gc
import shutil
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "api" / "services"))

SRC_DIR = PROJECT_ROOT / "data" / "hbw" / "HBW_low_resolution"
OUT_DIR = PROJECT_ROOT / "data" / "hbw"

GT_COLUMNS = [
    "subject_id", "height_cm", "gender",
    "chest_cm", "waist_cm", "hip_cm",
    "shoulder_cm", "neck_cm", "thigh_cm",
    "calf_cm", "bicep_cm",
]





def mesh_to_measurements(vertices, height_cm):
    """Compute body measurements from an SMPL-X mesh (10,475 vertices).
    Uses SmplxMeasurementEngine for the SMPL-X measurement pipeline.
    """
    from smplx_measurement_engine import SmplxMeasurementEngine
    engine = SmplxMeasurementEngine()
    try:
        m = engine.compute_measurements(vertices, height_cm, "neutral")
        return m
    finally:
        del engine
        gc.collect()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    val_smplx_dir = SRC_DIR / "smplx" / "val"
    val_img_dir = SRC_DIR / "images" / "val_small_resolution"

    subject_ids = sorted([p.stem for p in val_smplx_dir.glob("*.npy")])
    print(f"Found {len(subject_ids)} validation subjects")

    # Known subject heights from HBW dataset metadata
    KNOWN_HEIGHTS = {
        '012': 172, '017': 165, '018': 188, '020': 178,
        '022': 173, '023': 178, '026': 182, '027': 170,
        '029': 175, '033': 175,
    }

    gt_rows = []
    total_images = 0
    for sid in subject_ids:
        print(f"\nProcessing subject {sid}...")

        gt_npy = val_smplx_dir / f"{sid}.npy"
        if not gt_npy.exists():
            print(f"  SKIP {sid}: no .npy found")
            continue

        # HBW .npy files are SMPL-X vertex positions directly (10475, 3)
        vertices = np.load(str(gt_npy)).astype(np.float64)
        if len(vertices) < 100:
            print(f"  SKIP {sid}: invalid mesh ({len(vertices)} verts)")
            continue

        # Heuristic: check if the subject number suggests gender
        # (actual gender info requires smplx model which we don't have)
        gender = "neutral"

        height_cm = KNOWN_HEIGHTS.get(sid, float((vertices[:, 1].max() - vertices[:, 1].min()) * 100))
        m = mesh_to_measurements(vertices, height_cm)

        row = {
            "subject_id": sid,
            "height_cm": round(height_cm, 1),
            "gender": gender,
            "chest_cm": round(m.get("chest_cm", 0), 1),
            "waist_cm": round(m.get("waist_cm", 0), 1),
            "hip_cm": round(m.get("hip_cm", 0), 1),
            "shoulder_cm": round(m.get("shoulder_cm", 0), 1),
            "neck_cm": round(m.get("neck_cm", 0), 1),
            "thigh_cm": round(m.get("thigh_cm", 0), 1),
            "calf_cm": round(m.get("calf_cm", 0), 1),
            "bicep_cm": round(m.get("bicep_cm", 0), 1),
        }
        gt_rows.append(row)

        # Copy images
        img_dirs = list(val_img_dir.glob(f"{sid}*/**/*.png"))
        for img_path in img_dirs:
            photo_id = img_path.stem
            dst = OUT_DIR / f"{sid}_{photo_id}.png"
            if not dst.exists():
                shutil.copy2(img_path, dst)
            total_images += 1

        print(f"  Copied {len(img_dirs)} images for {sid}")
        print(f"  Height={row['height_cm']:.0f}cm Chest={row['chest_cm']:.0f} Waist={row['waist_cm']:.0f} Hip={row['hip_cm']:.0f}")

    if gt_rows:
        gt_path = OUT_DIR / "ground_truth.csv"
        with open(gt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GT_COLUMNS)
            writer.writeheader()
            writer.writerows(gt_rows)
        print(f"\nWrote {len(gt_rows)} subjects to {gt_path}")

    print(f"Total images in output: {total_images}")


if __name__ == "__main__":
    main()
