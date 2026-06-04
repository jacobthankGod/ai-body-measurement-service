"""
Measurement Tests
=============
"""
import pytest
import numpy as np
from api.services.measurement_engine import extract_measurements_from_dual_photos, validate_image

def test_extract_male_measurements():
    """Test male measurement extraction."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 170, 'male')
    assert measurements['Shoulder'] == pytest.approx(45.05, 0.1)
    assert measurements['Waist Round'] == pytest.approx(80.07, 0.1)

def test_extract_female_measurements():
    """Test female measurement extraction."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    measurements = extract_measurements_from_dual_photos(image, image, 160, 'female')
    assert measurements['Shoulder'] == pytest.approx(36.8, 0.1)
    assert measurements['Waist Round'] == pytest.approx(64.0, 0.1)

def test_validate_image_valid():
    """Test image validation with valid image."""
    image = np.full((500, 300, 3), 128, dtype=np.uint8)
    valid, msg = validate_image(image)
    assert valid is True

def test_validate_image_too_small():
    """Test image validation with small image."""
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    valid, msg = validate_image(image)
    assert valid is False

def test_validate_image_too_dark():
    """Test image validation with dark image."""
    image = np.zeros((500, 300, 3), dtype=np.uint8)
    valid, msg = validate_image(image)
    assert valid is False
