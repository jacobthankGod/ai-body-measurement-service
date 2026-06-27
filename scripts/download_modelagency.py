"""
Download and filter Model Agency dataset images
================================================
Samples models from agencies with still-live image hosts (curve-models,
the-models.de), downloads images, filters for front-facing full-body shots.

Usage:
    python scripts/download_modelagency.py --max-models 50 --max-images 3
"""
import argparse
import csv
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data" / "modelagency"
MODEL_DATA_PATH = DATA_DIR / "ModelAgencyData" / "cleaned_model_data.json"
DOWNLOAD_DIR = DATA_DIR / "downloaded"
GT_PATH = DATA_DIR / "ground_truth.csv"

SKIP_KEYWORDS = [
    'back', 'profile', 'side', 'detail', 'closeup', 'close-up',
    'makeup', 'hair', 'nails', 'hands', 'feet', 'eye', 'lips',
    'texture', 'accessory', 'bag', 'shoe', 'dress_detail',
    'backstage', 'behind',
]

MIN_FILE_SIZE = 20 * 1024
REQUEST_TIMEOUT = 10
MAX_WORKERS = 8  # parallel downloads


def is_frontal_candidate(url: str) -> bool:
    url_lower = url.lower()
    fname = Path(urlparse(url).path).stem.lower()
    for kw in SKIP_KEYWORDS:
        if kw in fname or kw in url_lower:
            return False
    return True


def download_one(args):
    url, save_path, model_id = args
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT,
                         headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            return None
        if int(r.headers.get('content-length', 0)) < MIN_FILE_SIZE:
            return None
        content_type = r.headers.get('content-type', '')
        if 'image' not in content_type:
            return None
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return model_id
    except Exception:
        return None


def load_models(json_path: Path, max_models: int, seed: int,
                only_agencies: list = None):
    with open(json_path) as f:
        data = json.load(f)

    models = []
    for agency, entry in data.items():
        if only_agencies and agency not in only_agencies:
            continue
        n = len(entry['model_name'])
        for i in range(n):
            models.append({
                'agency': agency,
                'idx': i,
                'name': str(entry['model_name'][i]),
                'gender': str(entry['gender'][i] or ''),
                'height_cm': entry['height_cm'][i] if i < len(entry.get('height_cm', [])) else None,
                'bust_cm': entry['bust_cm'][i] if i < len(entry.get('bust_cm', [])) else None,
                'waist_cm': entry['waist_cm'][i] if i < len(entry.get('waist_cm', [])) else None,
                'hips_cm': entry['hips_cm'][i] if i < len(entry.get('hips_cm', [])) else None,
                'image_urls': entry['image_urls'][i] if i < len(entry.get('image_urls', [])) else [],
            })

    valid = [m for m in models
             if m['waist_cm'] and m['image_urls'] and len(m['image_urls']) > 0]
    print(f"Total: {len(models)}, with measurements+images: {len(valid)}")
    if only_agencies:
        for a in only_agencies:
            n = sum(1 for m in valid if m['agency'] == a)
            print(f"  {a}: {n} valid models")

    rng = random.Random(seed)
    rng.shuffle(valid)
    sampled = valid[:max_models]
    return sampled


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-models', type=int, default=100)
    parser.add_argument('--max-images', type=int, default=3)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--agencies', nargs='+',
                        default=['curve-models', 'the-models'],
                        help='Agencies to download from')
    args = parser.parse_args()

    print("=" * 70)
    print("MODEL AGENCY DATASET DOWNLOADER")
    print("=" * 70)

    models = load_models(MODEL_DATA_PATH, args.max_models, args.seed, args.agencies)

    all_download_tasks = []
    for model in models:
        subj_id = f"{model['agency']}_{model['name'].replace(' ', '_')}"
        subj_dir = DOWNLOAD_DIR / subj_id
        for url_idx, url in enumerate(model['image_urls']):
            if url_idx >= args.max_images * 3:  # Try up to 3x to find good ones
                break
            if not is_frontal_candidate(url):
                continue
            fname = f"{url_idx:03d}.jpg"
            save_path = subj_dir / fname
            if save_path.exists() and args.resume:
                continue
            all_download_tasks.append((url, save_path, subj_id))

    print(f"Queued {len(all_download_tasks)} downloads from {len(models)} models")
    print(f"Using {MAX_WORKERS} parallel workers")

    success = set()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(download_one, t) for t in all_download_tasks]
        done = 0
        for f in as_completed(futures):
            done += 1
            result = f.result()
            if result:
                success.add(result)
            if done % 50 == 0:
                print(f"  Progress: {done}/{len(all_download_tasks)}")

    # Build GT
    downloaded_models = {}
    for model in models:
        subj_id = f"{model['agency']}_{model['name'].replace(' ', '_')}"
        subj_dir = DOWNLOAD_DIR / subj_id
        n_dl = len(list(subj_dir.glob('*.jpg'))) if subj_dir.exists() else 0
        if n_dl > 0:
            downloaded_models[subj_id] = {
                'subject_id': subj_id,
                'height_cm': model['height_cm'] or '',
                'gender': model['gender'],
                'chest_cm': model['bust_cm'] or '',
                'waist_cm': model['waist_cm'] or '',
                'hip_cm': model['hips_cm'] or '',
                'agency': model['agency'],
                'images_downloaded': n_dl,
            }

    print(f"\n{'=' * 70}")
    print(f"Models with ≥1 downloaded image: {len(downloaded_models)}")
    print(f"Total images: {sum(m['images_downloaded'] for m in downloaded_models.values())}")
    if len(success) > 0:
        print(f"Models with ≥1 successful new download: {len(success)}")

    if downloaded_models:
        out_path = DATA_DIR / "ground_truth_downloaded.csv"
        with open(out_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'subject_id', 'height_cm', 'gender', 'chest_cm',
                'waist_cm', 'hip_cm', 'agency', 'images_downloaded'])
            writer.writeheader()
            for sid in sorted(downloaded_models):
                writer.writerow(downloaded_models[sid])
        print(f"GT saved to: {out_path}")

    print("\nDone.")


if __name__ == '__main__':
    main()
