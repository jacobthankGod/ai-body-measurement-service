#!/usr/bin/env python3
"""
Upload garment reconstruction weights to Kaggle Dataset.

Creates a Kaggle Dataset mirror at jacobthankgod/korra-garment-weights
so notebooks can download from GCP-local storage (fast, no Xet cold cache).

Usage:
    # First-time: create dataset
    python scripts/upload_garment_weights_to_kaggle.py

    # Update existing dataset with newer weights
    python scripts/upload_garment_weights_to_kaggle.py --update

Prerequisites:
    pip install kagglehub huggingface_hub requests
    Kaggle API key configured (see ~/.kaggle/kaggle.json or env vars)
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Files to mirror (relative paths within the dataset)
FILES = {
    "mrf_0.1_shading_0.1_pca64_ep100_bth0.pth": {
        "url": "https://huggingface.co/jacobthankgod4/smpl-model-garmentrec/resolve/main/mrf_0.1_shading_0.1_pca64_ep100_bth0.pth?download=1",
        "desc": "GarmentRec model weights (~1.16 GB)",
        "expected_mb": 1100,
    },
    "neutral_smpl_with_cocoplus_reg.txt": {
        "url": "https://huggingface.co/jacobthankgod4/smpl-model-garmentrec/resolve/main/neutral_smpl_with_cocoplus_reg.txt",
        "desc": "SMPL model file",
        "expected_mb": None,
    },
}

DATASET_SLUG = "korra-garment-weights"
DATASET_OWNER = "jacobthankgod"
DATASET_HANDLE = f"{DATASET_OWNER}/{DATASET_SLUG}"


def robust_download(url: str, dest: Path, desc: str = "", expected_mb: int | None = None) -> bool:
    """Download with wget -> requests fallback (same logic as notebook)."""
    import requests as req
    import time

    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            if desc:
                print(f"  {desc}: attempt {attempt+1}/3...")
            cmd = [
                "wget", "-c", "--show-progress",
                "--timeout=30", "--tries=3", "--retry-connrefused",
                "-O", str(dest), url,
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            if r.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
                size_mb = dest.stat().st_size / (1024 * 1024)
                if expected_mb is None or size_mb >= expected_mb * 0.9:
                    if desc:
                        print(f"  {desc}: {size_mb:.0f} MB")
                    return True
            # Fallback: requests
            if desc:
                print(f"  {desc}: wget failed, trying requests...")
            with req.get(url, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            if dest.exists() and dest.stat().st_size > 0:
                size_mb = dest.stat().st_size / (1024 * 1024)
                if expected_mb is None or size_mb >= expected_mb * 0.9:
                    if desc:
                        print(f"  {desc}: {size_mb:.0f} MB")
                    return True
        except Exception as e:
            if desc:
                print(f"  {desc}: attempt {attempt+1} failed: {e}")
        if attempt < 2:
            time.sleep(5 * (attempt + 1))
    if desc:
        print(f"  *** {desc}: FAILED ***")
    return False


def create_dataset_metadata(
    dataset_dir: Path,
    title: str = "Korra Garment Weights",
    description: str = (
        "Pretrained weights for GarmentRec + SMPL model used by Korra's "
        "garment reconstruction pipeline. Mirrors HF Hub for fast GCP-local access."
    ),
    license: str = "MIT",
):
    metadata = {
        "title": title,
        "id": DATASET_HANDLE,
        "description": description,
        "licenses": [{"name": license}],
    }
    meta_path = dataset_dir / "dataset-metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Created {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="Upload garment weights to Kaggle Dataset")
    parser.add_argument("--update", action="store_true", help="Update existing dataset")
    parser.add_argument("--weights-dir", type=Path, default=None,
                        help="Use existing weights directory instead of downloading")
    args = parser.parse_args()

    # Check Kaggle credentials
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    has_creds = kaggle_json.exists() and kaggle_json.stat().st_size > 10
    if not has_creds:
        print("Kaggle credentials not found at ~/.kaggle/kaggle.json")
        print("Please create this file with:")
        print('  {"username":"jacobthankgod","key":"KGAT_4ada61fb7668048f325fa249acbf744e"}')
        print("Then set permissions: chmod 600 ~/.kaggle/kaggle.json")
        sys.exit(1)

    # Create staging directory
    staging = Path(tempfile.mkdtemp(prefix="kaggle_dataset_"))
    print(f"Staging directory: {staging}")

    if args.weights_dir and args.weights_dir.exists():
        # Copy from existing local directory
        print(f"Copying weights from {args.weights_dir}...")
        for fname in FILES:
            src = args.weights_dir / fname
            if src.exists():
                shutil.copy2(src, staging / fname)
                size_mb = src.stat().st_size / (1024 * 1024)
                print(f"  {fname}: {size_mb:.0f} MB (from {args.weights_dir})")
            else:
                print(f"  {fname}: NOT FOUND in {args.weights_dir}")
    else:
        # Download each file
        for fname, info in FILES.items():
            dest = staging / fname
            print(f"\nDownloading {info['desc']}...")
            ok = robust_download(
                url=info["url"],
                dest=dest,
                desc=fname,
                expected_mb=info["expected_mb"],
            )
            if not ok:
                print(f"  *** Failed to download {fname}! ***")
                sys.exit(1)

    # Compute checksums
    print("\nComputing SHA256 checksums...")
    for fname in FILES:
        fpath = staging / fname
        if fpath.exists():
            sha = hashlib.sha256()
            with open(fpath, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    sha.update(chunk)
            print(f"  {fname}: {sha.hexdigest()}")

    # Create dataset-metadata.json
    create_dataset_metadata(staging)

    # List files
    print(f"\nDataset contents ({DATASET_HANDLE}):")
    for f in sorted(staging.iterdir()):
        if f.is_file() and f.name != "dataset-metadata.json":
            print(f"  {f.name}: {f.stat().st_size / (1024*1024):.0f} MB")

    # Upload via kaggle CLI
    print(f"\nUploading to Kaggle Dataset '{DATASET_HANDLE}'...")
    action = "create" if not args.update else "version"
    cmd = ["kaggle", "datasets", action, "-p", str(staging), "--dir-mode", "tar", "-m", "Updated garment weights"]
    if args.update:
        cmd += ["--version-note", f"Update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  SUCCESS: Dataset '{DATASET_HANDLE}' uploaded!")
        print(f"  {result.stdout[:500] if result.stdout else ''}")
    else:
        print(f"  FAILED (exit code {result.returncode})")
        print(f"  stderr: {result.stderr[:1000]}")
        print(f"\n  Alternative: Create dataset manually at")
        print(f"  https://www.kaggle.com/datasets/{DATASET_HANDLE}/create")
        print(f"  and upload the files from {staging}/")

    # Cleanup
    print(f"\nStaging directory preserved at: {staging}")
    print("(delete manually after verifying upload)")


if __name__ == "__main__":
    main()
