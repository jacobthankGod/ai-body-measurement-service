#!/bin/bash
# Test script for AI Body Scan SaaS API
# Run this from ai-body-scan-saas directory

echo "=========================================="
echo "AI Body Scan SaaS - Local Test"
echo "=========================================="

# Configuration
API_URL="http://localhost:5001"
API_KEY="dev_test_key_12345"

# Create test API key if not exists
if [ ! -f "data/api_keys.json" ]; then
    echo "Creating test API key..."
    mkdir -p data
    cat > data/api_keys.json << EOF
{
  "dev_test_key_12345": {
    "key": "dev_test_key_12345",
    "user_id": "test_user",
    "subscription": "tailor_basic",
    "quota": 0,
    "used": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": null
  }
}
EOF
fi

# Create test images if not exists
if [ ! -d "data/test" ]; then
    echo "Creating test images..."
    mkdir -p data/test
    # Try with Python
    python3 -c "
from PIL import Image
import numpy as np

# Create simple test images (640x480)
front = np.zeros((480, 640, 3), dtype=np.uint8)
front[100:380, :] = [100, 150, 200]
Image.fromarray(front).save('data/test/front.png')

side = np.zeros((480, 640, 3), dtype=np.uint8)
side[100:380, :] = [100, 200, 150]
Image.fromarray(side).save('data/test/side.png')
"
fi

echo ""
echo "1. Starting server..."
echo "   Run in another terminal:"
echo "   uvicorn api.main:app --host 0.0.0.0 --port 5001 --reload"
echo ""
read -p "Press Enter when server is running..."

# Test health
echo ""
echo "=========================================="
echo "Testing HEALTH endpoint..."
echo "=========================================="
curl -s "$API_URL/api/v2/health" | python3 -m json.tool

# Test measurements
echo ""
echo "=========================================="
echo "Testing MEASUREMENTS endpoint..."
echo "=========================================="
echo "Height: 170cm, Gender: male"
echo ""

curl -s -X POST "$API_URL/api/v2/measurements/extract" \
  -H "X-API-Key: $API_KEY" \
  -F "front=@data/test/front.png" \
  -F "side=@data/test/side.png" \
  -F "height=170" \
  -F "gender=male" | python3 -m json.tool

echo ""
echo "Done!"
