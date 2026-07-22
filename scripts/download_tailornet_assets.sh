#!/bin/bash
# Download TailorNet trained weights
# Usage: bash scripts/download_tailornet_assets.sh [garment_gender...]
#   e.g., bash scripts/download_tailornet_assets.sh t-shirt_male shirt_female

set -euo pipefail

DATA_DIR="api/services/tailornet_data"
WEIGHTS_DIR="$DATA_DIR/model_weights"
URL_BASE="https://datasets.d2.mpi-inf.mpg.de/tailornet"

mkdir -p "$WEIGHTS_DIR"

download_weights() {
    local key="$1"
    local url="$URL_BASE/${key}_weights.zip"
    local out_zip="$WEIGHTS_DIR/${key}_weights.zip"
    if [ -d "$WEIGHTS_DIR/${key}_weights" ]; then
        echo "OK: $key weights already extracted, skipping"
        return 0
    fi
    if [ ! -f "$out_zip" ]; then
        echo "Downloading $key weights ($url)..."
        curl -L -o "$out_zip" "$url"
    fi
    echo "Extracting $key weights..."
    unzip -q -o "$out_zip" -d "$WEIGHTS_DIR"
    echo "OK: $key weights ready"
}

if [ $# -eq 0 ]; then
    echo "Usage: bash scripts/download_tailornet_assets.sh [garment_gender...]"
    echo "  Available from MPI: t-shirt_male t-shirt_female shirt_male shirt_female"
    echo "  Example: bash scripts/download_tailornet_assets.sh t-shirt_female shirt_male shirt_female"
    exit 1
fi

for arg in "$@"; do
    download_weights "$arg"
done

echo ""
echo "Done. Weights ready at: $WEIGHTS_DIR"
