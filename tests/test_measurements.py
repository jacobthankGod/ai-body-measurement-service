"""
Measurement Tests
=============
"""
import pytest
import numpy as np
from api.services.measurement_engine import extract_measurements_from_dual_photos

def test_extract_male_measurements():
    """Test male measurement extraction produces valid output."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 170, 'male')
    assert isinstance(measurements, dict)
    assert len(measurements) > 5
    assert measurements.get('height') == 170.0

def test_extract_female_measurements():
    """Test female measurement extraction produces valid output."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 160, 'female')
    assert isinstance(measurements, dict)
    assert len(measurements) > 5
    assert measurements.get('height') == 160.0

def test_male_has_gender_specific_keys():
    """Male extraction includes key body measurements."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 175, 'male')
    measurement_keys = set(k for k, v in measurements.items() if isinstance(v, (int, float)))
    assert len(measurement_keys) >= 8, f"Too few measurement keys: {measurement_keys}"

def test_female_has_gender_specific_keys():
    """Female extraction includes key body measurements."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 165, 'female')
    measurement_keys = set(k for k, v in measurements.items() if isinstance(v, (int, float)))
    assert len(measurement_keys) >= 8, f"Too few measurement keys: {measurement_keys}"

def test_measurements_all_positive():
    """All numeric measurements are positive."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 170, 'male')
    skip_keys = {'height', 'fusion_weight_hmr', 'fusion_weight_mediapipe'}
    for key, val in result.items():
        if isinstance(val, (int, float)) and key not in skip_keys:
            assert val >= 0, f"Measurement '{key}' is negative: {val}"

def test_fusion_sources_tracked():
    """Fusion pipeline tracks which models contributed."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    result = extract_measurements_from_dual_photos(image, image, 170, 'male')
    assert 'fusion_sources' in result
    sources = result['fusion_sources']
    assert 'hmr' in sources
    assert 'mediapipe' in sources

def test_validate_image_valid():
    """Test image validation with valid image returns OK."""
    image = np.full((500, 300, 3), 128, dtype=np.uint8)
    from api.services.mediapipe_measurement_engine import validate_image
    valid, msg = validate_image(image)
    assert valid is True

def test_validate_image_too_small():
    """Test image validation rejects small images."""
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    from api.services.mediapipe_measurement_engine import validate_image
    valid, msg = validate_image(image)
    assert valid is False

def test_validate_image_too_dark():
    """Test image validation rejects dark images."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    from api.services.mediapipe_measurement_engine import validate_image
    valid, msg = validate_image(image)
    assert valid is False
