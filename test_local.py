#!/usr/bin/env python3
"""
Test script for AI Body Scan SaaS API
- Creates test images
- Starts the server
- Tests the measurement endpoint
"""
import os
import sys
import json
import subprocess
import time
import requests
from PIL import Image
import numpy as np

# Add project to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_test_images():
    """Create dummy test images (solid color for testing)."""
    print("Creating test images...")
    
    # Create test images directory
    test_dir = os.path.join(PROJECT_DIR, "data", "test")
    os.makedirs(test_dir, exist_ok=True)
    
# Create two simple test images (640x480 RGB)
    # Front view - blue-ish
    front_img = np.zeros((480, 640, 3), dtype=np.uint8)
    front_img[100:380, :] = [100, 150, 200]  # Body shape
    
    # Side view - green-ish  
    side_img = np.zeros((480, 640, 3), dtype=np.uint8)
    side_img[100:380, :] = [100, 200, 150]  # Body shape
    
    # Save as PNG
    front_path = os.path.join(test_dir, "front.png")
    side_path = os.path.join(test_dir, "side.png")
    
    Image.fromarray(front_img).save(front_path)
    Image.fromarray(side_img).save(side_path)
    
    print(f"  Created: {front_path}")
    print(f"  Created: {side_path}")
    return front_path, side_path


def create_test_api_key():
    """Create a test API key for development."""
    print("Creating test API key...")
    
    api_keys_file = os.path.join(PROJECT_DIR, "data", "api_keys.json")
    
    # Create test key
    test_key = "dev_test_key_12345"
    key_data = {
        test_key: {
            "key": test_key,
            "user_id": "test_user",
            "subscription": "tailor_basic",
            "quota": 0,
            "used": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": None
        }
    }
    
    with open(api_keys_file, 'w') as f:
        json.dump(key_data, f, indent=2)
    
    print(f"  Created test key: {test_key}")
    return test_key


def start_server():
    """Start the FastAPI server in background."""
    print("Starting FastAPI server...")
    
    # Check if requirements are installed
    req_file = os.path.join(PROJECT_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"ERROR: requirements.txt not found at {req_file}")
        return None
    
    # Try to start server
    server_script = os.path.join(PROJECT_DIR, "api", "main.py")
    if os.path.exists(server_script):
        proc = subprocess.Popen(
            [sys.executable, server_script],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"  Server started (PID: {proc.pid})")
        return proc
    else:
        # Try uvicorn
        proc = subprocess.Popen(
            ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5001"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"  Server started (PID: {proc.pid})")
        return proc


def test_health_endpoint(base_url="http://localhost:5001"):
    """Test health endpoint."""
    print("\n--- Testing Health Endpoint ---")
    
    try:
        response = requests.get(f"{base_url}/api/v2/health", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_measurements_endpoint(base_url, api_key, front_image, side_image, height_cm=170, gender="male"):
    """Test measurements endpoint."""
    print("\n--- Testing Measurements Endpoint ---")
    print(f"  Front: {front_image}")
    print(f"  Side: {side_image}")
    print(f"  Height: {height_cm}cm, Gender: {gender}")
    
    try:
        with open(front_image, 'rb') as f_front, open(side_image, 'rb') as f_side:
            files = {
                'front': ('front.png', f_front, 'image/png'),
                'side': ('side.png', f_side, 'image/png'),
            }
            data = {
                'height': str(height_cm),
                'gender': gender,
            }
            headers = {
                'X-API-Key': api_key
            }
            
            response = requests.post(
                f"{base_url}/api/v2/measurements/extract",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  ✅ SUCCESS!")
            print(f"\n  Measurements:")
            for key, value in sorted(result.get('measurements', {}).items()):
                print(f"    {key}: {value}cm")
            print(f"\n  Metadata:")
            print(f"    Accuracy: {result.get('accuracy', {}).get('estimated_cm', 'N/A')}")
            print(f"    Mode: {result.get('accuracy', {}).get('mode', 'N/A')}")
            return True
        else:
            print(f"  ❌ ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    print("="*60)
    print("AI Body Scan SaaS - Local Test")
    print("="*60)
    
    base_url = "http://localhost:5001"
    
    # Step 1: Create test API key
    api_key = create_test_api_key()
    
    # Step 2: Create test images
    front_image, side_image = create_test_images()
    
    # Step 3: Test health endpoint (may need server running)
    test_health_endpoint(base_url)
    
    print("\n" + "="*60)
    print("INSTRUCTIONS TO RUN MANUALLY:")
    print("="*60)
    print("""
1. Start the server:
   cd /Users/mac/desby_app/../ai-body-scan-saas
   uvicorn api.main:app --host 0.0.0.0 --port 5001 --reload

2. In another terminal, test with curl:
   curl -X POST "http://localhost:5001/api/v2/measurements/extract" \\
        -H "X-API-Key: dev_test_key_12345" \\
        -F "front=@data/test/front.png" \\
        -F "side=@data/test/side.png" \\
        -F "height=170" \\
        -F "gender=male"
    
   Or test health:
   curl http://localhost:5001/api/v2/health
""")


if __name__ == "__main__":
    main()
