"""
Convert SSP-3D dataset to batch_evaluation format.

SSP-3D has 311 images of sportspersons in tight clothing,
with SMPL shape/pose parameters from multi-frame optimization.

Source: data/ssp3d/ssp_3d/
  - images/{fname}.png
  - labels.npz (fnames, shapes, poses, genders, etc.)

We generate ground truth measurements from the SMPL shape params
using our own _calculate_from_indices pipeline on a T-pose mesh.

Output: data/ssp3d/
  - {subject_id}_img.png  (where subject_id = fname without extension)
  - ground_truth.csv (subject_id, height_cm, gender, chest_cm, ...)
"""
import csv
import sys
import gc
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "api" / "services"))

SRC_DIR = PROJECT_ROOT / "data" / "ssp3d" / "ssp_3d"
OUT_DIR = PROJECT_ROOT / "data" / "ssp3d"

GT_COLUMNS = [
    "subject_id", "height_cm", "gender",
    "chest_cm", "waist_cm", "hip_cm",
    "shoulder_cm", "neck_cm", "thigh_cm",
    "calf_cm", "bicep_cm", "forearm_cm",
    "arm_length_cm", "leg_length_cm",
]


def smpl_beta_to_measurements(beta, gender):
    """Generate SMPL T-pose mesh from beta params and compute measurements."""
    from extract_measurements import HMRMasterEngine
    engine = HMRMasterEngine()
    try:
        v_shaped = engine._v_template + (engine._shapedirs @ beta).reshape(-1, 3)
        height_m = v_shaped[:, 1].max() - v_shaped[:, 1].min()
        height_cm = height_m * 100
        m = engine._calculate_from_indices(v_shaped, height_cm, gender)
        return m, height_cm
    finally:
        del engine
        gc.collect()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    labels = np.load(str(SRC_DIR / "labels.npz"), allow_pickle=True)
    fnames = labels["fnames"]
    shapes = labels["shapes"]
    genders = labels["genders"]

    print(f"Loaded {len(fnames)} SSP-3D samples")

    gt_rows = []
    for i in range(len(fnames)):
        fname = fnames[i]
        if isinstance(fname, bytes):
            fname = fname.decode()
        subject_id = Path(fname).stem.replace("/", "_").replace(" ", "_")

        beta = shapes[i].astype(np.float64)
        gender = "male" if genders[i].item() == "M" else "female"

        src_img = SRC_DIR / "images" / fname
        if not src_img.exists():
            print(f"  SKIP {subject_id}: image not found")
            continue

        dst_img = OUT_DIR / f"{subject_id}.png"
        if not dst_img.exists():
            import shutil
            shutil.copy2(src_img, dst_img)

        m, height_cm = smpl_beta_to_measurements(beta, gender)

        row = {
            "subject_id": subject_id,
            "height_cm": round(height_cm, 1),
            "gender": gender,
            "chest_cm": round(m.get("Chest Round", 0), 1),
            "waist_cm": round(m.get("Waist Round", 0), 1),
            "hip_cm": round(m.get("Hip Round", 0), 1),
            "shoulder_cm": round(m.get("Shoulder", 0), 1),
            "neck_cm": round(m.get("Neck Round", 0), 1),
            "thigh_cm": round(m.get("Thigh Round", 0), 1),
            "calf_cm": round(m.get("Calf Round", 0), 1),
            "bicep_cm": round(m.get("Bicep Round", 0), 1),
            "forearm_cm": round(m.get("Forearm", 0), 1),
            "arm_length_cm": round(m.get("Arm Length", 0), 1),
            "leg_length_cm": round(m.get("Leg Length", 0), 1),
        }
        gt_rows.append(row)

        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(fnames)}")

    if gt_rows:
        gt_path = OUT_DIR / "ground_truth.csv"
        with open(gt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GT_COLUMNS)
            writer.writeheader()
            writer.writerows(gt_rows)
        print(f"Wrote {len(gt_rows)} subjects to {gt_path}")

    # List images for reference
    img_count = len(list(OUT_DIR.glob("*.png")))
    print(f"Total images in output dir: {img_count}")


if __name__ == "__main__":
    main()
