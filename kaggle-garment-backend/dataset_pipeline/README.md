# Dataset Ingestion and Labeling Pipeline

This folder contains a non-destructive pipeline for preparing external garment datasets for future training and reconstruction workflows.

## What it does

- Scans a source directory recursively for image files
- Copies those images into a curated workspace under this repo
- Generates a JSON manifest describing each image and its source
- Generates a CSV label template for manual review
- Leaves the original source dataset untouched

## Usage

Run the script with a source directory containing images:

```bash
python kaggle-garment-backend/dataset_pipeline/ingest_label_data.py \
  --input-root /path/to/raw/datasets \
  --output-root ./kaggle-garment-backend/dataset_pipeline/outputs
```

## Outputs

- curated images under outputs/curated_images/
- manifest under outputs/manifests/dataset_manifest.json
- label template under outputs/labels/labels_template.csv

## Notes

- The script is intentionally simple and dependency-light.
- Heuristics are conservative and can be revised later.
- This is a data preparation scaffold, not a full training pipeline.
