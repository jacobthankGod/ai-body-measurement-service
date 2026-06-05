#!/usr/bin/env python3
"""
Test Body Scan with Two Images and Height
=====================================
This script tests the AI body scan functionality using two images and height input.
"""
import os
import sys
import json
import numpy as np
from PIL import Image

# Add project to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from api.services.measurement_engine import extract_measurements_from_dual_photos


def create_body_test_images(width=640, height=480):
    """Create test images that simulate human body silhouettes."""
    print("=" * 60)
    print("Creating test images (body silhouette simulation)")
    print("=" * 60)
    
    # Create test directory
    test_dir = os.path.join(PROJECT_DIR, "data", "test")
    os.makedirs(test_dir, exist_ok=True)
    
    # Front view - roughly human body shape
    front_img = np.zeros((height, width, 3), dtype=np.uint8)
    # Head
    cv = height // 2
    ch = width // 2
    
    # Create vertical body shape (simple approximation)
    # Torso area
    front_img[100:350, 200:440] = [180, 160, 140]  # Light gray body
    
    # Side view - profile shape
    side_img = np.zeros((height, width, 3), dtype=np.uint8)
    side_img[100:350, 180:460] = [160, 180, 140]  # Slightly different gray
    
    # Save images
    front_path = os.path.join(test_dir, "front.png")
    side_path = os.path.join(test_dir, "side.png")
    
    Image.fromarray(front_img).save(front_path)
    Image.fromarray(side_img).save(side_path)
    
    print(f"  Created: {front_path}")
    print(f"  Created: {side_path}")
    
    return front_path, side_path


def test_measurement_extraction(front_image, side_image, height_cm, gender):
    """Test measurement extraction with given parameters."""
    print("\n" + "=" * 60)
    print(f"Testing: Height={height_cm}cm, Gender={gender}")
    print("=" * 60)
    
    # Create numpy arrays from images
    front_arr = np.array(Image.open(front_image))
    side_arr = np.array(Image.open(side_image))
    
    # Extract measurements
    measurements = extract_measurements_from_dual_photos(
        front_arr, side_arr, height_cm, gender
    )
    
    print(f"\n  Extracted {len(measurements)} measurements:")
    print("-" * 40)
    
    # Display measurements in organized format
    for key, value in sorted(measurements.items()):
        print(f"    {key:25s}: {value:7.1f} cm")
    
    return measurements


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("AI BODY SCAN TEST - Two Images and Height")
    print("=" * 60)
    
    # Test parameters
    test_cases = [
        {"height": 170, "gender": "male"},
        {"height": 165, "gender": "male"},
        {"height": 160, "gender": "female"},
        {"height": 155, "gender": "female"},
    ]
    
    # Create test images
    front_path, side_path = create_body_test_images()
    
    # Test each case
    results = []
    for tc in test_cases:
        measurements = test_measurement_extraction(
            front_path, side_path, 
            tc["height"], 
            tc["gender"]
        )
        results.append({
            "height": tc["height"],
            "gender": tc["gender"],
            "measurements": measurements,
            "count": len(measurements)
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for r in results:
        print(f"  Height {r['height']}cm ({r['gender']}): {r['count']} measurements")
    
    print("\n  All tests completed successfully!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
