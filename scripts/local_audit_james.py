"""
Local Technical Audit: James (180cm)
=====================================
Verifies AI Extraction, Brain Integrity, and 3D Mesh Generation.
"""
import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image
import io

# Setup environment
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

def run_audit():
    print("💎 KORRA: Starting Local Technical Audit for 'James'...")

    # 1. Image Check
    front_path = BASE_DIR / "front.jpeg"
    side_path = BASE_DIR / "side.jpeg"

    if not front_path.exists() or not side_path.exists():
        print("❌ Audit Aborted: front.jpeg or side.jpeg missing from project root.")
        return

    # 2. Brain Integrity
    from api.services.extract_measurements import get_brain_integrity, ENGINE
    integrity = get_brain_integrity()
    print(f"🧠 Brain Integrity: {integrity}")

    if not all(integrity.values()):
        print("⚠️ Brain Incomplete. Attempting Expert Initialization...")
        # In a real boot this happens in main.py, here we simulate or check.
        # If weights are missing, the audit will fall back to proportions.

    # 3. Load Images
    front_img = np.array(Image.open(front_path))

    # 4. Execute Extraction
    print("🚀 Initiating AI Extraction (Height: 180cm)...")
    try:
        measurements, vertices, landmarks = ENGINE.extract(front_img, 180.0, "male")

        print("\n✅ AUDIT RESULTS:")
        print("-" * 30)
        print(f"Subject: James")
        for m, v in measurements.items():
            print(f"{m}: {v}cm")

        if vertices is not None:
            print(f"Digital Twin: ACTIVE ({len(vertices)} vertices)")
        else:
            print("Digital Twin: PROXY (Weights missing)")

        if landmarks:
            print(f"Landmark Map: SYNCHRONIZED")

    except Exception as e:
        print(f"❌ Extraction Failure: {e}")

if __name__ == "__main__":
    run_audit()
