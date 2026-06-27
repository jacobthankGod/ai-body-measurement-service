"""
Convert UniData (Kaggle) body-measurements-image-dataset to batch_evaluation format.

Source: ~/.cache/kagglehub/datasets/unidpro/body-measurements-image-dataset/versions/3/
Output: data/unidata/
  - S001_front.jpg, S001_side.jpg, ... S006_front.jpg, S006_side.jpg
  - ground_truth.csv
"""
import csv
import os
import shutil
from pathlib import Path

KAGGLE_CACHE = Path.home() / ".cache" / "kagglehub" / "datasets" / "unidpro" / "body-measurements-image-dataset" / "versions" / "3"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "unidata"

SUBJECTS = ["1", "2", "3", "4", "5", "6"]

CSV_MAP = {
    "chest_circumference_cm": "chest_cm",
    "waist_circumference_cm": "waist_cm",
    "hips_circumference_cm": "hip_cm",
    "thigh_circumference_cm": "thigh_cm",
    "arm_circumference_cm": "bicep_cm",
    "calf_circumference_cm": "calf_cm",
    "pelvis_circumference_cm": "stomach_cm",
    "under_chest_circumference_cm": "underbust_cm",
    "front_build_cm": "front_build_cm",
    "arm_length_cm": "arm_length_cm",
    "upper_arm_length_cm": "upper_arm_length_cm",
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = KAGGLE_CACHE / "Body Measurements Image Dataset.csv"
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = {r["set_id"]: r for r in reader}

    gt_rows = []
    for sid in SUBJECTS:
        subject_id = f"S{sid.zfill(3)}"
        subject_dir = KAGGLE_CACHE / sid

        front_src = subject_dir / "front_img.jpg"
        side_src = subject_dir / "side_img.jpg"

        if not front_src.exists():
            print(f"WARNING: {front_src} not found, skipping {subject_id}")
            continue
        if not side_src.exists():
            print(f"WARNING: {side_src} not found, skipping {subject_id}")
            continue

        shutil.copy2(front_src, OUTPUT_DIR / f"{subject_id}_front.jpg")
        shutil.copy2(side_src, OUTPUT_DIR / f"{subject_id}_side.jpg")
        print(f"  Copied {subject_id}: front_img.jpg + side_img.jpg")

        row = rows.get(sid, {})
        gt = {"subject_id": subject_id, "height_cm": row.get("height", ""), "gender": row.get("gender", "")}
        for src_col, dst_col in CSV_MAP.items():
            gt[dst_col] = row.get(src_col, "")
        gt_rows.append(gt)

    gt_path = OUTPUT_DIR / "ground_truth.csv"
    with open(gt_path, "w", newline="") as f:
        if gt_rows:
            writer = csv.DictWriter(f, fieldnames=gt_rows[0].keys())
            writer.writeheader()
            writer.writerows(gt_rows)

    print(f"\nWrote {len(gt_rows)} subjects to {gt_path}")


if __name__ == "__main__":
    main()
