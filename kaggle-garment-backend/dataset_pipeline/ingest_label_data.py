#!/usr/bin/env python3
"""
Non-destructive dataset ingestion and labeling scaffold.

This script scans a root directory for image files, copies them into a curated
workspace under the repo, generates a manifest JSON, and creates a label
template CSV for human review.

It does not modify or delete the original source data.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_images(input_root: Path) -> List[Path]:
    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")

    images = []
    for path in input_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(path)

    return sorted(images)


def infer_dataset_name(path: Path, input_root: Path) -> str:
    rel = path.relative_to(input_root)
    parts = rel.parts
    if not parts:
        return "unknown_dataset"
    return parts[0]


def build_curated_path(image_path: Path, output_root: Path, input_root: Path) -> Path:
    rel = image_path.relative_to(input_root)
    dataset_name = infer_dataset_name(image_path, input_root)
    curated_dir = output_root / "curated_images" / dataset_name
    curated_dir.mkdir(parents=True, exist_ok=True)
    suffix = image_path.suffix.lower()
    stem = image_path.stem
    unique_name = f"{stem}{suffix}"
    return curated_dir / unique_name


def copy_image(image_path: Path, curated_path: Path) -> None:
    curated_path.parent.mkdir(parents=True, exist_ok=True)
    if not curated_path.exists():
        shutil.copy2(image_path, curated_path)


def heuristic_label(dataset_name: str) -> Dict[str, str]:
    lower = dataset_name.lower()
    if "dress" in lower:
        return {"garment_type": "dress"}
    if "attire" in lower:
        return {"garment_type": "attire"}
    if "fabric" in lower:
        return {"fabric_pattern": "fabric"}
    if "wax" in lower or "pattern" in lower:
        return {"fabric_pattern": "wax_print"}
    return {"garment_type": "unknown"}


def write_manifest(records: List[Dict], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def write_label_template(records: List[Dict], label_csv_path: Path) -> None:
    label_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "image_id",
        "source_dataset",
        "original_path",
        "curated_path",
        "garment_type",
        "subtype",
        "silhouette",
        "sleeve_type",
        "neckline",
        "fabric_pattern",
        "color_family",
        "pose",
        "occlusion",
        "quality_score",
        "notes",
    ]
    with label_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k, "") for k in fieldnames})


def build_records(input_root: Path, output_root: Path) -> List[Dict]:
    images = discover_images(input_root)
    records = []

    for image_path in images:
        curated_path = build_curated_path(image_path, output_root, input_root)
        copy_image(image_path, curated_path)

        dataset_name = infer_dataset_name(image_path, input_root)
        heuristics = heuristic_label(dataset_name)
        record = {
            "image_id": curated_path.stem,
            "source_dataset": dataset_name,
            "original_path": str(image_path),
            "curated_path": str(curated_path),
            "relative_path": str(image_path.relative_to(input_root)),
            "file_extension": image_path.suffix.lower(),
            "sha256": sha256_file(image_path),
            "garment_type": heuristics.get("garment_type", ""),
            "subtype": "",
            "silhouette": "",
            "sleeve_type": "",
            "neckline": "",
            "fabric_pattern": heuristics.get("fabric_pattern", ""),
            "color_family": "",
            "pose": "",
            "occlusion": "",
            "quality_score": "",
            "notes": "",
            "split": "train",
        }
        records.append(record)

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest dataset images into a curated workspace")
    parser.add_argument("--input-root", required=True, help="Root directory containing source images")
    parser.add_argument("--output-root", default="./dataset_pipeline/outputs", help="Output directory")
    parser.add_argument("--manifest-name", default="dataset_manifest.json", help="Manifest filename")
    parser.add_argument("--label-csv-name", default="labels_template.csv", help="Labels CSV filename")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_root = Path(args.input_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    print(f"Scanning input root: {input_root}")
    records = build_records(input_root, output_root)

    manifest_path = output_root / "manifests" / args.manifest_name
    label_csv_path = output_root / "labels" / args.label_csv_name

    write_manifest(records, manifest_path)
    write_label_template(records, label_csv_path)

    print(f"Processed {len(records)} images")
    print(f"Manifest written to: {manifest_path}")
    print(f"Label template written to: {label_csv_path}")
    print("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
