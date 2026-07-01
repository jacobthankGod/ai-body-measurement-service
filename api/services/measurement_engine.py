"""
Measurement Engine | HYBRID FUSION ARCHITECTURE
================================================
Combines HMR 3D mesh (primary) with MediaPipe volumetric analysis (complementary)
via ANSUR II statistical imputation for maximum clinical accuracy.
"""
import numpy as np
from api.services.extract_measurements import extract_measurements_from_hmr
from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_extract
from api.services.imputation_service import imputation_service
from api.services.shape_transformer import shape_transformer
from api.services.mesh_validator import mesh_validator
from api.services.measurement_calibration import calibrator as measurement_calibrator

def extract_measurements_from_dual_photos(front_image, side_image, user_height_cm, gender='male'):
    """
    HYBRID FUSION PIPELINE:
    1. HMR 3D Vertex Mesh (primary, ±1cm) - Faraz Bhatti research implementation
    2. MediaPipe Volumetric Analysis (complementary, ±3cm) - anatomical landmarks
    3. ANSUR II Imputation (Phase 26) - statistical fusion of both sources
    4. Shape Transformer (Phase 48) - 3D mesh deformation
    5. Clinical Parity Check (Phase 91-105) - mesh validation
    Both HMR and MediaPipe run concurrently; ANSUR statistically fuses the results.
    """
    hmr_measurements = None
    hmr_vertices = None
    hmr_confidence = 0.0
    mp_measurements = None
    mp_confidence = 0.0
    landmarks = {}

    # 1A. HMR PRIMARY (High precision 3D mesh)
    hmr_smpl_params = None
    try:
        res_data = extract_measurements_from_hmr(front_image, user_height_cm, gender, side_image=side_image)
        measurements = res_data[0]
        vertices = res_data[1]
        hmr_smpl_params = res_data[7] if len(res_data) > 7 else None

        if measurements:
            # Check for valid primary measurement based on gender
            primary_key = 'Chest Round' if gender == 'male' else 'Bust Round'
            if measurements.get(primary_key, 0) > 0:
                hmr_measurements = measurements
                hmr_vertices = vertices
                hmr_confidence = 0.95
                print("💎 KORRA: HMR 3D Mesh Extracted Successfully.")
    except Exception as e:
        print(f"⚠️ HMR Processing Note: {e}")

    # 1B. MEDIAPIPE COMPLEMENTARY (Anatomical landmarks)
    mp_mask = None
    try:
        mp_result, mp_landmarks, mp_mask = mp_extract(front_image, side_image, user_height_cm, gender)
        if mp_result and mp_result.get('Shoulder', 0) > 0:
            mp_measurements = mp_result
            landmarks = mp_landmarks
            mp_confidence = 0.15
            print("✅ MediaPipe Volumetric Analysis Complete.")
    except Exception as e:
        print(f"⚠️ MediaPipe Processing Note: {e}")

    # 2. HYBRID FUSION via ANSUR II Imputation
    fused_metrics = imputation_service.fuse_measurements(
        gender=gender,
        hmr_measurements=hmr_measurements,
        mp_measurements=mp_measurements,
        user_height_cm=user_height_cm,
        hmr_confidence=hmr_confidence,
        mp_confidence=mp_confidence
    )

    # 3. SHAPE TRANSFORMER (3D mesh deformation)
    # PILLAR 3: Silhouette-Based Shape Optimization (Iterative Refinement)
    if hmr_smpl_params and mp_mask is not None:
        try:
            from api.services.silhouette_optimizer import get_optimizer
            optimizer = get_optimizer()
            if optimizer:
                initial_betas = np.array(hmr_smpl_params.get('shape', [0]*10))
                camera = np.array(hmr_smpl_params.get('camera', [1, 0, 0]))

                # Refine betas to match image mask
                optimized_betas = optimizer.optimize(initial_betas, camera, mp_mask, max_iter=20)

                # Recalculate HMR measurements with optimized shape
                from api.services.extract_measurements import ENGINE
                v_shaped = ENGINE._v_template + np.tensordot(optimizer.shapedirs, optimized_betas, axes=([2], [0]))
                refined_hmr = ENGINE._calculate_from_indices(v_shaped, user_height_cm, gender)

                # Update hmr_measurements and smpl_params
                hmr_measurements.update(refined_hmr)
                hmr_smpl_params['shape'] = optimized_betas.tolist()
                hmr_smpl_params['silhouette_optimized'] = True
                print(f"✨ Pillar 3: Silhouette Optimization applied. Refined shape coefficients.")
        except Exception as e:
            print(f"⚠️ Silhouette Optimization skipped: {e}")
    if hmr_vertices is not None:
        try:
            reshaped_vertices = shape_transformer.apply_deformation(hmr_vertices, fused_metrics, gender)

            # 4. CLINICAL PARITY VALIDATION
            if reshaped_vertices is not None:
                mesh_metrics = mesh_validator.calculate_mesh_measurements(
                    reshaped_vertices, shape_transformer.partitions
                )
                realism_score = mesh_validator.calculate_realism_index(fused_metrics, mesh_metrics)
                fused_metrics['clinical_realism_index'] = realism_score
                fused_metrics['accuracy_certificate'] = mesh_validator.generate_accuracy_certificate(
                    realism_score, fused_metrics
                )
        except Exception as e:
            print(f"⚠️ Shape Transformer Note: {e}")

    # 5. BUILD FINAL OUTPUT
    if hmr_measurements:
        fused_metrics.update((k, v) for k, v in hmr_measurements.items()
                            if k not in fused_metrics)
        # Phase 0: Explicitly populate __smpl_params for calibrator/subgroup logic
        if hmr_smpl_params:
            fused_metrics['__smpl_params'] = hmr_smpl_params

    if mp_measurements:
        fused_metrics.update((k, v) for k, v in mp_measurements.items()
                            if k not in fused_metrics)
        # Preserve pose metrics for calibration
        if 'pose_metrics' in mp_measurements:
            fused_metrics['pose_metrics'] = mp_measurements['pose_metrics']

    # Phase 0: Consistency Monitor (Height Delta Logging)
    if hmr_measurements and 'Height' in hmr_measurements:
        hmr_h = hmr_measurements['Height']
        h_delta = abs(hmr_h - user_height_cm)
        print(f"📊 Consistency Monitor: HMR Height={hmr_h:.1f}, User Height={user_height_cm:.1f}, Delta={h_delta:.1f}cm")
        fused_metrics['height_consistency_delta'] = round(h_delta, 2)
        if h_delta > 10.0:
            print("⚠️ WARNING: Significant height mismatch detected (>10cm). Results may be unreliable.")

    # Apply SMPL-to-real-world calibration for core measurements
    # (Calibrator now uses __smpl_params and pose_metrics for subgroup/pose logic)
    measurement_calibrator.calibrate(fused_metrics, gender)

    fused_metrics['fusion_sources'] = {
        'hmr': hmr_measurements is not None,
        'mediapipe': mp_measurements is not None,
    }

    print(f"✅ Fusion Complete: HMR={hmr_measurements is not None}, MediaPipe={mp_measurements is not None}")
    return fused_metrics
