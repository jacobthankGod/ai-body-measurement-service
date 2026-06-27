"""
Convert Model Agency dataset to batch_evaluation format.

Model Agency data has 5,121 models with height, bust, waist, hip measurements
and 145,995 image URLs from model agency websites.

Source: data/modelagency/ModelAgencyData/
  - cleaned_model_data.json

Since downloading 146K images from URLs is impractical for a single session,
this script:
1. Exports a ground_truth.csv with all measurements
2. Optionally downloads images for a random subset

Output: data/modelagency/
  - ground_truth.csv (all 5,121 models with measurements)
  - images/{model_name}_*.jpg (if --download flag used)
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data" / "modelagency"

GT_COLUMNS = [
    "subject_id", "height_cm", "gender",
    "chest_cm", "waist_cm", "hip_cm",
    "agency",
]


def download_image(url, dst_path, timeout=10):
    """Download a single image from URL."""
    import requests
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AcademicResearch/1.0)"
        })
        if r.status_code == 200:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_bytes(r.content)
            return True
    except Exception as e:
        pass
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", type=int, default=0,
                        help="Number of images to download per model (0 = skip download)")
    parser.add_argument("--max-models", type=int, default=None,
                        help="Max models to process")
    args = parser.parse_args()

    src = DATA_DIR / "ModelAgencyData" / "cleaned_model_data.json"
    with open(src) as f:
        data = json.load(f)

    gt_rows = []
    total_models = 0
    for agency, d in data.items():
        n = len(d["model_name"])
        for i in range(n):
            subject_id = f"{agency}_{d['model_name'][i]}"
            gender = d["gender"][i] if i < len(d["gender"]) else ""

            height = d["height_cm"][i] if i < len(d["height_cm"]) else None
            bust = d["bust_cm"][i] if i < len(d["bust_cm"]) else None
            waist = d["waist_cm"][i] if i < len(d["waist_cm"]) else None
            hips = d["hips_cm"][i] if i < len(d["hips_cm"]) else None

            # Convert height from cm list to float
            if isinstance(height, list):
                height = height[0] if height else None

            gt_rows.append({
                "subject_id": subject_id,
                "height_cm": round(float(height), 1) if height else "",
                "gender": "male" if gender == "M" else "female" if gender == "W" else "",
                "chest_cm": round(float(bust), 1) if bust else "",
                "waist_cm": round(float(waist), 1) if waist else "",
                "hip_cm": round(float(hips), 1) if hips else "",
                "agency": agency,
            })
            total_models += 1

            if args.max_models and total_models >= args.max_models:
                break
        if args.max_models and total_models >= args.max_models:
            break

    # Write ground truth CSV
    gt_path = DATA_DIR / "ground_truth.csv"
    with open(gt_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GT_COLUMNS)
        writer.writeheader()
        writer.writerows(gt_rows)
    print(f"Wrote {len(gt_rows)} models to {gt_path}")

    # Optionally download images
    if args.download > 0:
        img_dir = DATA_DIR / "images"
        downloaded = 0
        for row in gt_rows[:args.max_models or len(gt_rows)]:
            sid = row["subject_id"]
            agency = row["agency"]
            d = data.get(agency, {})
            urls_list = d.get("image_urls", [])
            # Find the right model index
            try:
                idx = d["model_name"].index(sid.replace(f"{agency}_", "", 1))
                urls = urls_list[idx] if idx < len(urls_list) else []
            except ValueError:
                urls = []
            for j, url in enumerate(urls[:args.download]):
                ext = Path(url.split("?")[0]).suffix or ".jpg"
                dst = img_dir / f"{sid}_{j}{ext}"
                if dst.exists():
                    downloaded += 1
                    continue
                if download_image(url, dst):
                    downloaded += 1
                if downloaded % 100 == 0:
                    print(f"  Downloaded {downloaded} images...")
                time.sleep(0.1)

        print(f"Downloaded {downloaded} images to {img_dir}")


if __name__ == "__main__":
    main()
