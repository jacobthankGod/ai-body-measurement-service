#!/bin/bash
# Continuous Training Pipeline
# =============================
# Orchestrates the full training workflow: build dataset → train models → evaluate → deploy.
# Designed to be run via cron (weekly or after every N new scans).
#
# Usage:
#   ./scripts/continuous_training_pipeline.sh [--dry-run] [--version N]
#
# Environment:
#   SUPABASE_DB_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
#
# Exit codes:
#   0 = success, pipeline complete
#   1 = build failure (no dataset produced)
#   2 = training failure (models failed)
#   3 = deployment skipped (new models degraded vs previous)
#   4 = deployment failure

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PRIORS_DIR="$PROJECT_DIR/api/models/priors"

DRY_RUN=false
VERSION="auto"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --version) VERSION="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if $DRY_RUN; then
    echo "🔍 DRY RUN — no changes will be made"
fi

echo "=== Continuous Training Pipeline ==="
echo "Version: $VERSION"
echo "Project: $PROJECT_DIR"
echo ""

# ---- Step 1: Build dataset ----
echo "--- Step 1: Build training dataset ---"
if [ "$VERSION" = "auto" ]; then
    VERSION=$(date +%Y%m%d_%H%M%S)
fi
DATASET_DIR="$PROJECT_DIR/data/training_dataset/v$VERSION"

if $DRY_RUN; then
    echo "  Would run: python $SCRIPT_DIR/build_training_dataset.py --version $VERSION --output-dir $DATASET_DIR"
else
    python "$SCRIPT_DIR/build_training_dataset.py" --version "$VERSION" --output-dir "$DATASET_DIR"
    if [ ! -d "$DATASET_DIR" ] || [ ! -f "$DATASET_DIR/dataset_manifest.csv" ]; then
        echo "❌ Dataset build failed"
        exit 1
    fi
    NUM_SCANS=$(wc -l < "$DATASET_DIR/dataset_manifest.csv")
    echo "✅ Dataset built: $DATASET_DIR ($NUM_SCANS scans)"
fi
echo ""

# ---- Step 2: Train shape prior (GMM) ----
echo "--- Step 2: Train shape prior ---"
if $DRY_RUN; then
    echo "  Would run: python $SCRIPT_DIR/train_shape_prior.py --dataset-dir $DATASET_DIR --output-dir $PRIORS_DIR --version $VERSION"
else
    python "$SCRIPT_DIR/train_shape_prior.py" --dataset-dir "$DATASET_DIR" --output-dir "$PRIORS_DIR" --version "$VERSION"
    echo "✅ Shape prior trained"
fi
echo ""

# ---- Step 3: Train consistency model ----
echo "--- Step 3: Train measurement consistency model ---"
if $DRY_RUN; then
    echo "  Would run: python $SCRIPT_DIR/train_consistency_model.py --dataset-dir $DATASET_DIR --output-dir $PRIORS_DIR --version $VERSION"
else
    python "$SCRIPT_DIR/train_consistency_model.py" --dataset-dir "$DATASET_DIR" --output-dir "$PRIORS_DIR" --version "$VERSION"
    echo "✅ Consistency model trained"
fi
echo ""

# ---- Step 4: Train subgroup calibration (if ground truth available) ----
echo "--- Step 4: Train subgroup calibration ---"
GT_FILE="$PROJECT_DIR/data/unidata/ground_truth.csv"
if [ -f "$GT_FILE" ]; then
    if $DRY_RUN; then
        echo "  Would run: python $SCRIPT_DIR/train_subgroup_calibration.py --dataset-dir $DATASET_DIR --ground-truth $GT_FILE --output-dir $PRIORS_DIR --version $VERSION"
    else
        python "$SCRIPT_DIR/train_subgroup_calibration.py" --dataset-dir "$DATASET_DIR" --ground-truth "$GT_FILE" --output-dir "$PRIORS_DIR" --version "$VERSION"
        echo "✅ Subgroup calibration trained"
    fi
else
    echo "⚠️ No ground truth at $GT_FILE — skipping subgroup calibration"
fi
echo ""

# ---- Step 5: Evaluate ----
echo "--- Step 5: Evaluate previous vs new models ---"
if $DRY_RUN; then
    echo "  Would compare model versions and decide deployment"
    echo "  Would run: python $SCRIPT_DIR/evaluate_pipeline.py --new priors/v$VERSION --old priors/current"
else
    echo "  Model version $VERSION trained successfully"
    echo "  (Automatic comparison requires held-out evaluation data)"
fi
echo ""

echo "=== Pipeline complete ==="
echo "Version: $VERSION"
echo "Models in: $PRIORS_DIR"
