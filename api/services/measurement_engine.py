"""
Measurement Engine | MASTER Artisan 1:1 ALIGNMENT
================================================
Primary high-precision pipeline based on Faraz Bhatti research.
"""
import numpy as np
from api.services.extract_measurements import extract_measurements_from_hmr
from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_fallback

def extract_measurements_from_dual_photos(front_image, side_image, user_height_cm, gender='male'):
    """
    MASTER PIPELINE:
    1. HMR 3D Vertex Mesh (1:1 Alignment with Research Paper) - PRIMARY ±1cm
    2. MediaPipe Volumetric Analysis (Phase 11) - SECONDARY FALLBACK
    """

    # 1. ATTEMPT HIGH-PRECISION HMR (Faraz Bhatti Implementation)
    try:
        # HMR Returns: (measurements, vertices, landmarks, body_shape, size_rec, error)
        hmr_res = extract_measurements_from_hmr(front_image, user_height_cm, gender, side_image=side_image)
        results = hmr_res[0] # Get the measurements dict
        if results and results.get('Chest Round', 0) > 0:
            print("💎 KORRA: High-Precision 1:1 Alignment Active.")
            return results
    except Exception as e:
        print(f"⚠️ HMR Pipeline Drift: {e}. Switching to Volumetric Fallback.")

    # 2. FALLBACK TO DEPTH-AWARE MEDIAPIPE (Personalized Volume)
    return mp_fallback(front_image, side_image, user_height_cm, gender)
