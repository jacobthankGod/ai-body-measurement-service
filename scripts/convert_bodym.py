"""
Convert BodyM dataset measurements to batch_evaluation ground_truth.csv format.

Reads measurements_train.csv / testA.csv / testB.csv from data/bodym/
and outputs a merged ground_truth.csv with standardized column names.

BodyM columns (from 3D scan):
  subject_id, ankle, arm-length, bicep, calf, chest, forearm,
  height, hip, leg-length, shoulder-breadth, shoulder-to-crotch,
  thigh, waist, wrist

Our batch_evaluation columns:
  subject_id, height_cm, gender, chest_cm, waist_cm, hip_cm,
  shoulder_cm, neck_cm, thigh_cm, ankle_cm, bicep_cm, inseam_cm,
  calf_cm, knee_cm, stomach_cm

Note: BodyM does not have real photos (only silhouettes) so the
output CSV can't be used directly with HMR. But it's useful for
validating the mesh-level measurement pipeline if SMPL meshes
are generated independently.
"""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "bodym"
SOURCES = [
    "measurements_train.csv",
    "measurements_testA.csv",
    "measurements_testB.csv",
]

COLUMN_MAP = {
    "chest": "chest_cm",
    "waist": "waist_cm",
    "hip": "hip_cm",
    "shoulder-breadth": "shoulder_cm",
    "thigh": "thigh_cm",
    "ankle": "ankle_cm",
    "bicep": "bicep_cm",
    "calf": "calf_cm",
    "arm-length": "arm_length_cm",
    "forearm": "forearm_cm",
    "leg-length": "leg_length_cm",
    "shoulder-to-crotch": "shoulder_to_crotch_cm",
    "wrist": "wrist_cm",
    "height": "height_cm",
}


def main():
    all_rows = []
    for src in SOURCES:
        path = DATA_DIR / src
        if not path.exists():
            print(f"  SKIP {path} (not found)")
            continue
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                gt = {"subject_id": row["subject_id"]}
                for src_col, dst_col in COLUMN_MAP.items():
                    val = row.get(src_col, "")
                    try:
                        val = round(float(val), 1)
                    except (ValueError, TypeError):
                        val = ""
                    gt[dst_col] = val
                all_rows.append(gt)

    out_path = DATA_DIR / "ground_truth.csv"
    if not all_rows:
        print("No rows to write.")
        return

    fieldnames = list(all_rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} subjects to {out_path}")


if __name__ == "__main__":
    main()
