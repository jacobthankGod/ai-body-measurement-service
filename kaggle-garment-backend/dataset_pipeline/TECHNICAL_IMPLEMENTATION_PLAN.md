# Technical Implementation Plan: Non-Destructive Dataset Ingestion and Labeling Pipeline

## Objective

Create a safe, repo-local workflow for ingesting external garment datasets into a standardized format without modifying the original source data. The pipeline should:

- ingest images from one or more input directories,
- copy them into a curated workspace under the repo,
- generate a master manifest,
- create a label-template CSV for human review,
- support lightweight heuristics-based labeling,
- remain fully reversible and non-destructive.

---

## Scope

This implementation is intentionally narrow and robust. It is designed for:

- African attire and dress datasets,
- fabric and wax-pattern datasets,
- image-based garment understanding and segmentation experiments,
- future integration with reconstruction and pattern-generation models.

It does not attempt to perform full 3D reconstruction or model training yet. Its purpose is to create a stable data foundation.

---

## Design Principles

1. Non-destructive by default
   - never move or delete source files
   - copy into a curated output directory
   - preserve input paths in the manifest

2. Reproducible
   - output should be deterministically generated from input paths
   - manifest and CSV should be versioned and reviewable

3. Minimal dependency footprint
   - use only the Python standard library
   - avoid requiring PyTorch, OpenCV, or heavy packages for the first pass

4. Human-in-the-loop friendly
   - generate a CSV template that can be filled by reviewers
   - keep labels explicit and editable

5. Repo-safe
   - place all generated outputs in a dedicated subfolder under the garment backend directory
   - avoid overwriting existing project files

---

## Proposed Repository Structure

```text
kaggle-garment-backend/
  dataset_pipeline/
    TECHNICAL_IMPLEMENTATION_PLAN.md
    ingest_label_data.py
    README.md
    outputs/
      manifests/
      labels/
      curated_images/
```

This keeps all pipeline logic self-contained and separate from the existing model notebook and server code.

---

## Pipeline Stages

### Stage 1: Discover input datasets
The script will scan a user-specified input root for image files.

Supported image extensions:
- .jpg
- .jpeg
- .png
- .webp
- .bmp

The scan should be recursive and should preserve relative directory structure.

### Stage 2: Copy into curated workspace
For each discovered image:
- compute a deterministic output path,
- copy the image into the curated output tree,
- record the original path and curated path in a manifest.

### Stage 3: Generate metadata manifest
The manifest will include:
- image_id
- source_dataset
- original_path
- curated_path
- relative_path
- file_extension
- heuristic_label
- split
- quality_score
- notes

### Stage 4: Create label template
A CSV file will be generated with one row per image. Reviewers can fill in labels for:
- garment_type
- subtype
- silhouette
- sleeve_type
- neckline
- fabric_pattern
- color_family
- pose
- occlusion
- quality_score
- notes

### Stage 5: Optional heuristic labeling
If a dataset folder name suggests a likely category, the script can assign a default heuristic label. For example:
- african_dresses -> likely garment_type = dress
- african_attire -> likely garment_type = attire
- african_wax_patterns -> likely fabric_pattern = wax_print

These heuristics are intentionally conservative and should be treated as starting points.

---

## Suggested CLI Interface

The script should support:

```bash
python ingest_label_data.py \
  --input-root /path/to/raw/datasets \
  --output-root ./dataset_pipeline/outputs \
  --label-template ./dataset_pipeline/outputs/labels/labels_template.csv
```

Optional flags:
- --dry-run
- --overwrite-manifest
- --split-train 0.8
- --split-val 0.1
- --split-test 0.1

---

## Output Files

### 1. Curated image copy tree
```text
outputs/curated_images/<source_dataset>/<image_id>.<ext>
```

### 2. Master manifest
```text
outputs/manifests/dataset_manifest.json
```

### 3. Label template CSV
```text
outputs/labels/labels_template.csv
```

### 4. Optional summary JSON
```text
outputs/manifests/dataset_summary.json
```

---

## Label Schema

The label template should use a predictable schema such as:

```text
image_id
source_dataset
original_path
curated_path
garment_type
subtype
silhouette
sleeve_type
neckline
fabric_pattern
color_family
pose
occlusion
quality_score
notes
```

This schema is simple enough for manual review and compatible with training pipelines later.

---

## Recommended Review Workflow

1. Run the ingestion script.
2. Review the generated CSV in a spreadsheet editor.
3. Fill in labels for the first 200–500 samples.
4. Save the reviewed CSV as a new version.
5. Use that reviewed version as the seed for future training.

---

## Integration Notes for the Existing Repo

This pipeline should sit alongside the existing Kaggle notebook and backend work, not inside it. Its role is:

- to create a clean, labeled data foundation,
- to support future segmentation and classification experiments,
- to feed later model training modules.

It should remain independent so it can be reused for any future dataset import.

---

## Recommended Next Steps

1. Run the ingestion script on a small, high-quality subset first.
2. Manually review 200 images.
3. Use the reviewed subset to define the first label taxonomy.
4. Expand iteratively to the rest of the dataset.
5. Later connect the manifest and labels to model training scripts.

---

## Success Criteria

The implementation is successful when:

- the script runs without modifying the source dataset,
- image copies are created in the curated output tree,
- a manifest JSON is generated,
- a label CSV is generated,
- the workflow can be repeated safely across multiple runs.
t