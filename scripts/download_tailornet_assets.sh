#!/bin/bash
# Download TailorNet trained weights + SMPL model files + dataset files
# Usage: bash scripts/download_tailornet_assets.sh [garment_gender...]
#   e.g., bash scripts/download_tailornet_assets.sh t-shirt_male shirt_female
#   Default: t-shirt_male (2.0 GB)

set -euo pipefail

DATA_DIR="api/services/tailornet_data"
WEIGHTS_DIR="$DATA_DIR/model_weights"
SMPL_DIR="$DATA_DIR/smpl"
URL_BASE="https://datasets.d2.mpi-inf.mpg.de/tailornet"

mkdir -p "$WEIGHTS_DIR" "$SMPL_DIR"

# Weight URLs from README
declare -A WEIGHT_URLS
WEIGHT_URLS[old-t-shirt_female]="$URL_BASE/old-t-shirt_female_weights.zip"
WEIGHT_URLS[t-shirt_male]="$URL_BASE/t-shirt_male_weights.zip"
WEIGHT_URLS[t-shirt_female]="$URL_BASE/t-shirt_female_weights.zip"
WEIGHT_URLS[shirt_female]="$URL_BASE/shirt_female_weights.zip"
WEIGHT_URLS[shirt_male]="$URL_BASE/shirt_male_weights.zip"

# Nextcloud link for pant / short-pant / skirt (all in one)
NEXTCLOUD_URL="https://nextcloud.mpi-klsb.mpg.de/index.php/s/LTWJPcRt7gsgoss/download"

download_weights() {
    local key="$1"
    local url="${WEIGHT_URLS[$key]:-}"
    if [ -z "$url" ]; then
        echo "⚠ Unknown garment_gender combo: $key"
        echo "   Available: ${!WEIGHT_URLS[*]}"
        echo "   Others (pant, short-pant, skirt) via Nextcloud: $NEXTCLOUD_URL"
        return 1
    fi
    local out_zip="$WEIGHTS_DIR/${key}_weights.zip"
    if [ -d "$WEIGHTS_DIR/${key}_weights" ]; then
        echo "✓ $key weights already extracted, skipping"
        return 0
    fi
    if [ ! -f "$out_zip" ]; then
        echo "⬇ Downloading $key weights ($url)..."
        curl -L -o "$out_zip" "$url"
    fi
    echo "📦 Extracting $key weights..."
    unzip -q -o "$out_zip" -d "$WEIGHTS_DIR"
    echo "✓ $key weights ready"
}

# Default: download t-shirt_male if nothing specified
if [ $# -eq 0 ]; then
    set -- "t-shirt_male"
fi

for arg in "$@"; do
    download_weights "$arg"
done

echo ""
echo "============================================"
echo " TailorNet Assets Setup"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Download SMPL model files (.pkl) from https://smpl.is.tue.mpg.de"
echo "   Place them at:"
echo "     $SMPL_DIR/basicModel_neutral_lbs_10_207_0_v1.0.0.pkl"
echo "     $SMPL_DIR/male/model.pkl"
echo "     $SMPL_DIR/female/model.pkl"
echo ""
echo "2. Download TailorNet dataset from https://github.com/zycliao/TailorNet_dataset"
echo "   Place garment_class_info.pkl at:"
echo "     $DATA_DIR/garment_class_info.pkl"
echo ""
echo "3. Run: python -c \"from api.services.tailornet_bridge import run_tailornet; print(run_tailornet('t-shirt', 'male'))\""
echo ""
