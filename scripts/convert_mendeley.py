"""
Convert Mendeley Body Measurements Dataset to batch_evaluation format.

715 subjects (391 male, 324 female) with tape measurements in inches.
No photos — this is a reference statistics dataset.

Source: data/mendeley/measurements.csv
Columns: Gender,Age,HeadCircumference,ShoulderWidth,ChestWidth,Belly,Waist,
         Hips,ArmLength,ShoulderToWaist,WaistToKnee,LegLength,TotalHeight

Note: These are WIDTH measurements (not circumferences) in inches.
Useful for reference statistics, NOT direct comparison with our pipeline.

Output: data/mendeley/
  - ground_truth.csv (inches converted to cm)
"""
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data" / "mendeley"

SRC_CSV = DATA_DIR / "measurements.csv"

INCH_TO_CM = 2.54

COLUMN_MAP = {
    "TotalHeight": "height_cm",
    "ShoulderWidth": "shoulder_width_cm",
    "ChestWidth": "chest_width_cm",
    "Waist": "waist_cm",
    "Hips": "hip_cm",
    "Belly": "belly_cm",
    "ArmLength": "arm_length_cm",
    "LegLength": "leg_length_cm",
    "HeadCircumference": "head_circ_cm",
    "ShoulderToWaist": "shoulder_to_waist_cm",
    "WaistToKnee": "waist_to_knee_cm",
}


def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def main():
    with open(SRC_CSV) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} rows from {SRC_CSV}")

    gt_rows = []
    for i, row in enumerate(rows):
        gender = "male" if row.get("Gender") == "1" else "female" if row.get("Gender") == "2" else ""
        gt = {
            "subject_id": f"MDL_{i+1:04d}",
            "gender": gender,
        }
        for src_col, dst_col in COLUMN_MAP.items():
            val = safe_float(row.get(src_col, ""))
            if val is not None:
                gt[dst_col] = round(val * INCH_TO_CM, 1)
            else:
                gt[dst_col] = ""
        gt_rows.append(gt)

    out_path = DATA_DIR / "ground_truth.csv"
    if gt_rows:
        fieldnames = list(gt_rows[0].keys())
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(gt_rows)
        print(f"Written {len(gt_rows)} rows to {out_path}")

    # Print summary stats
    heights = [r["height_cm"] for r in gt_rows if r["height_cm"] != ""]
    if heights:
        print(f"Height range: {min(heights):.0f} - {max(heights):.0f} cm")
        print(f"Gender breakdown: {sum(1 for r in gt_rows if r['gender']=='male')}M / {sum(1 for r in gt_rows if r['gender']=='female')}F")


if __name__ == "__main__":
    main()
