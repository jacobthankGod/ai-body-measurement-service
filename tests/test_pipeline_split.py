"""
Split Tests: HMR + MediaPipe Fusion Pipeline
============================================
Verifies the hybrid fusion architecture where both HMR and MediaPipe
run concurrently and their outputs are fused via ANSUR II imputation.
No fallback path — all sources contribute to a unified result.
"""
import pytest
import numpy as np
from api.services.imputation_service import imputation_service
from api.services.measurement_engine import extract_measurements_from_dual_photos
from api.services.mediapipe_measurement_engine import (
    extract_measurements_from_dual_photos as mp_extract,
    compute_elliptical_circumference,
    _extract_proportional_measurements,
)


# ──────────────────────────────────────────────
# SPLIT TEST A: HMR PATH (Primary)
# ──────────────────────────────────────────────
def test_hmr_fallback_ratios_produce_valid_output():
    """Verify that extract_measurements_from_hmr returns valid data
    even when TF is unavailable (uses fallback ratios)."""
    from api.services.extract_measurements import extract_measurements_from_hmr
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_hmr(image, 175.0, 'male', side_image=image)
    measurements = result[0]
    assert measurements is not None
    assert len(measurements) > 0
    assert isinstance(measurements, dict)


def test_hmr_measurement_keys_male():
    """HMR fallback produces male-specific measurement keys."""
    from api.services.extract_measurements import extract_measurements_from_hmr
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_hmr(image, 175.0, 'male', side_image=image)
    measurements = result[0]
    expected_keys = {'Chest Round', 'Waist Round', 'Shoulder', 'Hip Round'}
    assert expected_keys.issubset(measurements.keys()), f"Missing keys in {measurements.keys()}"


def test_hmr_measurement_keys_female():
    """HMR fallback produces female-specific measurement keys."""
    from api.services.extract_measurements import extract_measurements_from_hmr
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_hmr(image, 160.0, 'female', side_image=image)
    measurements = result[0]
    expected_keys = {'Bust Round', 'Waist Round', 'Hip Round'}
    assert expected_keys.issubset(measurements.keys()), f"Missing keys in {measurements.keys()}"


# ──────────────────────────────────────────────
# SPLIT TEST B: MEDIAPIPE PATH (Complementary)
# ──────────────────────────────────────────────
def test_mediapipe_proportional_measurements_male():
    """MediaPipe proportional measurements for male are height-scaled correctly."""
    result = _extract_proportional_measurements(180.0, 'male')
    assert result['Shoulder'] == pytest.approx(47.7, 0.1)
    assert result['Chest Round'] == pytest.approx(105.8, 0.1)
    assert result['Waist Round'] == pytest.approx(84.8, 0.1)
    assert result['Neck Round'] == pytest.approx(40.3, 0.1)


def test_mediapipe_proportional_measurements_female():
    """MediaPipe proportional measurements for female are height-scaled correctly."""
    result = _extract_proportional_measurements(165.0, 'female')
    assert result['Shoulder'] == pytest.approx(38.0, 0.1)
    assert result['Waist Round'] == pytest.approx(66.0, 0.1)
    assert result['Hip Round'] == pytest.approx(94.1, 0.1)
    assert result['Bust Round'] == pytest.approx(86.0, 0.1)


def test_elliptical_circumference_math():
    """Verify the elliptical circumference formula is computed correctly."""
    circ = compute_elliptical_circumference(40.0, 20.0)
    assert circ == pytest.approx(97.4, 0.1)
    circ_sym = compute_elliptical_circumference(40.0, 40.0)
    assert circ_sym == pytest.approx(125.7, 0.1)


# ──────────────────────────────────────────────
# SPLIT TEST C: ANSUR IMPUTATION FUSION
# ──────────────────────────────────────────────
def test_imputation_service_fuse_with_both_sources():
    """Imputation fuse with both HMR and MP data produces complete output."""
    hmr_data = {'Chest Round': 100.0, 'Waist Round': 85.0}
    mp_data = {'Shoulder': 45.0, 'Hip Round': 95.0, 'Neck Round': 38.0}
    result = imputation_service.fuse_measurements(
        gender='male',
        hmr_measurements=hmr_data,
        mp_measurements=mp_data,
        user_height_cm=175.0,
        hmr_confidence=0.85,
        mp_confidence=0.65
    )
    assert result is not None
    assert result['fusion_hmr_available'] is True
    assert result['fusion_mp_available'] is True
    assert result['height'] == 175.0
    assert result['chest_round'] == pytest.approx(100.0, 0.5)
    assert result['shoulder'] == pytest.approx(45.0, 0.5)


def test_imputation_service_fuse_hmr_only():
    """Imputation fuse with only HMR data still produces valid output."""
    hmr_data = {'Chest Round': 100.0, 'Waist Round': 85.0, 'Shoulder': 44.0, 'Hip Round': 96.0}
    result = imputation_service.fuse_measurements(
        gender='male',
        hmr_measurements=hmr_data,
        mp_measurements=None,
        user_height_cm=175.0
    )
    assert result is not None
    assert result['fusion_hmr_available'] is True
    assert result['fusion_mp_available'] is False
    assert result['chest_round'] == 100.0
    assert result['shoulder'] == 44.0


def test_imputation_service_fuse_mp_only():
    """Imputation fuse with only MP data still produces valid output."""
    mp_data = {'Shoulder': 45.0, 'Hip Round': 95.0, 'Waist Round': 82.0}
    result = imputation_service.fuse_measurements(
        gender='male',
        hmr_measurements=None,
        mp_measurements=mp_data,
        user_height_cm=175.0
    )
    assert result is not None
    assert result['fusion_hmr_available'] is False
    assert result['fusion_mp_available'] is True
    assert result['shoulder'] == 45.0


def test_imputation_service_fuse_weighting():
    """HMR gets higher fusion weight than MediaPipe when both present."""
    hmr_data = {'Chest Round': 100.0}
    mp_data = {'Chest Round': 95.0}
    result = imputation_service.fuse_measurements(
        gender='male',
        hmr_measurements=hmr_data,
        mp_measurements=mp_data,
        user_height_cm=175.0,
        hmr_confidence=0.85,
        mp_confidence=0.65
    )
    assert result['fusion_weight_hmr'] > result['fusion_weight_mediapipe']
    assert result['fusion_weight_hmr'] == pytest.approx(0.57, 0.01)
    assert result['fusion_weight_mediapipe'] == pytest.approx(0.43, 0.01)


def test_imputation_service_fuse_fills_gaps():
    """MediaPipe fills in measurements that HMR doesn't provide."""
    hmr_data = {'Chest Round': 100.0}
    mp_data = {'Chest Round': 98.0, 'Neck Round': 40.0, 'Thigh Round': 55.0}
    result = imputation_service.fuse_measurements(
        gender='male',
        hmr_measurements=hmr_data,
        mp_measurements=mp_data,
        user_height_cm=175.0
    )
    # Chest from HMR (weighted)
    assert result['chest_round'] is not None
    # ANSUR imputation adds additional targets
    target_keys = [k for k in result.keys() if k.endswith('circumference')]
    assert len(target_keys) > 0, f"No ANSUR target keys found in {result.keys()}"


# ──────────────────────────────────────────────
# SPLIT TEST D: FUSION PIPELINE (measurement_engine)
# ──────────────────────────────────────────────
def test_measurement_engine_fusion_always_returns():
    """measurement_engine always returns a result (no fallback needed)."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 170.0, 'male')
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) > 0


def test_measurement_engine_fusion_sources_tracked():
    """measurement_engine tracks which sources contributed to the result."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 170.0, 'male')
    assert 'fusion_sources' in result
    assert isinstance(result['fusion_sources'], dict)
    assert 'hmr' in result['fusion_sources']
    assert 'mediapipe' in result['fusion_sources']


def test_measurement_engine_fusion_all_measurements_positive():
    """All body measurements in fusion output are positive numbers."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 160.0, 'female')
    skip_keys = {'height', 'fusion_weight_hmr', 'fusion_weight_mediapipe',
                  'clinical_realism_index', 'Bust Point'}
    for key, val in result.items():
        if isinstance(val, (int, float)) and key not in skip_keys:
            assert val >= 0, f"Measurement '{key}' is negative: {val}"


def test_measurement_engine_fusion_height_consistency():
    """Height input is preserved through the fusion pipeline."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 180.0, 'male')
    assert result.get('height') == 180.0


# ──────────────────────────────────────────────
# SPLIT TEST E: NO FALLBACK VERIFICATION
# ──────────────────────────────────────────────
def test_no_fallback_on_validation_success():
    """Verify the pipeline does NOT degrade when primary source is valid."""
    from api.services.measurement_engine import extract_measurements_from_dual_photos as fusion_pipeline
    from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as mp_only

    image = np.full((500, 300, 3), 128, dtype=np.uint8)

    fusion_result = fusion_pipeline(image, image, 175.0, 'male')
    mp_result, _ = mp_only(image, image, 175.0, 'male')

    # Fusion should have MORE keys than MP alone (ANSUR adds targets)
    fusion_key_count = len([k for k in fusion_result.keys() if isinstance(fusion_result[k], (int, float))])
    mp_key_count = len([k for k in mp_result.keys() if isinstance(mp_result[k], (int, float))])
    assert fusion_key_count >= mp_key_count, (
        f"Fusion ({fusion_key_count}) has fewer measurements than MP alone ({mp_key_count})"
    )


# ──────────────────────────────────────────────
# SPLIT TEST F: COMPARISON BETWEEN PATHS
# ──────────────────────────────────────────────
def test_split_comparison_male_measurements():
    """Compare HMR, MP, and Fusion outputs for male."""
    from api.services.extract_measurements import extract_measurements_from_hmr

    image = np.zeros((500, 300, 3), dtype=np.uint8)
    height = 175.0
    gender = 'male'

    # Path A: HMR (primary)
    hmr_result = extract_measurements_from_hmr(image, height, gender, side_image=image)
    hmr_meas = hmr_result[0]

    # Path B: MediaPipe (complementary)
    mp_meas, _ = mp_extract(image, image, height, gender)

    # Path C: Fusion (combined via ANSUR)
    fusion_result = extract_measurements_from_dual_photos(image, image, height, gender)

    # All paths produce output
    assert hmr_meas is not None, "HMR path failed to produce output"
    assert mp_meas is not None, "MediaPipe path failed to produce output"
    assert fusion_result is not None, "Fusion path failed to produce output"

    # Fusion should have all keys from both paths plus ANSUR additions
    combined_keys = set(hmr_meas.keys()) | set(mp_meas.keys())
    fusion_keys = set(fusion_result.keys())
    assert combined_keys.issubset(fusion_keys), (
        f"Fusion missing keys: {combined_keys - fusion_keys}"
    )


def test_split_comparison_female_measurements():
    """Compare HMR, MP, and Fusion outputs for female."""
    from api.services.extract_measurements import extract_measurements_from_hmr

    image = np.zeros((500, 300, 3), dtype=np.uint8)
    height = 165.0
    gender = 'female'

    hmr_result = extract_measurements_from_hmr(image, height, gender, side_image=image)
    hmr_meas = hmr_result[0]
    mp_meas, _ = mp_extract(image, image, height, gender)
    fusion_result = extract_measurements_from_dual_photos(image, image, height, gender)

    assert hmr_meas is not None
    assert mp_meas is not None
    assert fusion_result is not None
    assert fusion_result.get('height') == height


# ──────────────────────────────────────────────
# SPLIT TEST G: SUBPROCESS INTEGRITY
# ──────────────────────────────────────────────
def test_subprocess_no_mediapipe_fallback():
    """Verify the route handler does NOT import mediapipe as a fallback."""
    import inspect
    from api.routes import measurements

    source = inspect.getsource(measurements.run_extraction_subprocess_cli)
    # The word 'mediapipe' should not appear in the subprocess worker
    assert 'mediapipe' not in source.lower(), (
        "Subprocess worker still contains MediaPipe fallback reference"
    )
    # Should return error status on failure, not fallback
    assert 'status\": \"failed\"' in source or '"status": "failed"' in source, (
        "Subprocess worker should return failed status on error"
    )


# ──────────────────────────────────────────────
# SPLIT TEST H: VALIDATION INTEGRITY
# ──────────────────────────────────────────────
def test_image_validation_from_mediapipe():
    """validate_image from MediaPipe works without crashing."""
    from api.services.mediapipe_measurement_engine import validate_image
    image = np.full((500, 300, 3), 128, dtype=np.uint8)
    valid, msg = validate_image(image)
    assert valid is True
    assert msg is not None
