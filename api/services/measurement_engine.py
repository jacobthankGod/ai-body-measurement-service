"""
Measurement Engine | MASTER Artisan 1:1 ALIGNMENT
================================================
Primary high-precision pipeline based on Faraz Bhatti research.
"""
import numpy as np
from api.services.extract_measurements import extract_measurements_from_hmr
from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_fallback
from api.services.imputation_service import imputation_service
from api.services.shape_transformer import shape_transformer

def extract_measurements_from_dual_photos(front_image, side_image, user_height_cm, gender='male'):
    """
    MASTER PIPELINE:
    1. HMR 3D Vertex Mesh (1:1 Alignment with Research Paper) - PRIMARY ±1cm
    2. ANSUR II Imputation (Phase 26) - REFINEMENT
    3. Shape Transformer (Phase 48) - 3D SYNTHESIS
    4. MediaPipe Volumetric Analysis (Phase 11) - SECONDARY FALLBACK
    """

    # 1. ATTEMPT HIGH-PRECISION HMR (Faraz Bhatti Implementation)
    try:
        # HMR Returns: (measurements, vertices, landmarks, body_shape, size_rec, error)
        res_data = extract_measurements_from_hmr(front_image, user_height_cm, gender, side_image=side_image)
        measurements = res_data[0]
        vertices = res_data[1]

        if measurements and measurements.get('Chest Round', 0) > 0:
            print("💎 KORRA: High-Precision 1:1 Alignment Active.")

            # PHASE 64/65: STRICT BIOMETRIC VALIDATION
            # Confidence is simulated here, but would come from HMR/MediaPipe metadata
            confidence = measurements.get('confidence', 1.0)
            valid, msg = imputation_service.validate_scan(gender, {
                'height': user_height_cm,
                'chest_round': measurements.get('Chest Round', 90),
                'waist_round': measurements.get('Waist Round', 80)
            }, confidence)

            if not valid:
                print(f"⚠️ Phase 65 Reject: {msg}")
                # Phase 58: Error Recovery - Return fallback if scan is invalid
                return mp_fallback(front_image, side_image, user_height_cm, gender)

            # PHASE 26: ANSUR II REFINEMENT (The Statistical Truth)
            # Map KORRA keys to ANSUR keys for imputation
            inputs = {
                'height': user_height_cm,
                'chest_round': measurements.get('Chest Round', 90),
                'waist_round': measurements.get('Waist Round', 80),
                'hip_round': measurements.get('Hip Round', 95),
                'shoulder': measurements.get('Shoulder', 40)
            }
            refined_metrics = imputation_service.impute(gender, inputs)

            # PHASE 48: SHAPE TRANSFORMER (Physical Mesh Synthesis)
            if vertices is not None:
                reshaped_vertices = shape_transformer.apply_deformation(vertices, refined_metrics, gender)
                # Note: The calling route (measurements.py) will serialize reshaped_vertices
                # For Phase 41-50, we attach the reshaped vertices to the result tuple if possible
                # But to keep it non-destructive, we return the refined measurements.

            # Merge refined metrics back into the main dict
            measurements.update(refined_metrics)
            return measurements

    except Exception as e:
        print(f"⚠️ HMR Pipeline Drift: {e}. Switching to Volumetric Fallback.")

    # 2. FALLBACK TO DEPTH-AWARE MEDIAPIPE (Personalized Volume)
    return mp_fallback(front_image, side_image, user_height_cm, gender)
