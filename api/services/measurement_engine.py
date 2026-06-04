"""
Measurement Engine
================
Extracts body measurements from photos using MediaPipe pose detection.
Falls back to anthropometric ratios if MediaPipe fails.
"""
import numpy as np

# Try to import MediaPipe engine
try:
    from api.services.mediapipe_measurement_engine import (
        extract_measurements_from_dual_photos as mp_extract,
        validate_image as mp_validate,
    )
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    print("MediaPipe not available, using ratio-based extraction")

MALE_RATIOS = {
    'Shoulder': 0.265, 'Neck Round': 0.224, 'Chest Round': 0.588,
    'Stomach Round': 0.500, 'Waist Round': 0.471, 'Full Top Length': 0.441,
    'Across Back': 0.247, 'Across Chest': 0.259, 'Hip Round': 0.559,
    'Thigh Round': 0.324, 'Knee Round': 0.224, 'Calf Round': 0.212,
    'Ankle Round': 0.153, 'Trouser Waist': 0.482, 'Trouser Length': 0.588,
    'Inseam': 0.459, 'Crotch Depth': 0.165, 'Arm Length': 0.353,
}

FEMALE_RATIOS = {
    'Shoulder': 0.230, 'Neck Round': 0.206, 'Bust Round': 0.521,
    'High Bust': 0.460, 'Under Bust': 0.412, 'Waist Round': 0.400,
    'Half Length': 0.315, 'Waist to Hip': 0.109, 'Upper Hip': 0.521,
    'Hip Round': 0.570, 'Thigh Round': 0.315, 'Knee Round': 0.206,
    'Calf Round': 0.194, 'Ankle Round': 0.133, 'Arm Length': 0.333,
    'Sleeve Length': 0.333, 'Bicep Round': 0.170, 'Wrist Round': 0.109,
}

def extract_measurements_from_dual_photos(front_image, side_image, user_height_cm, gender='male'):
    """
    Extract body measurements using dual photos for improved accuracy.
    Uses MediaPipe for real pose detection when available.
    
    Args:
        front_image: OpenCV image (front view)
        side_image: OpenCV image (side view)
        user_height_cm: User height in cm
        gender: male/female
    
    Returns:
        dict: Measurements in centimeters
    """
    # Try MediaPipe first for actual pose detection
    if HAS_MEDIAPIPE:
        try:
            return mp_extract(front_image, side_image, user_height_cm, gender)
        except Exception as e:
            print(f"MediaPipe extraction failed: {e}, falling back to ratios")
    
    # Fallback to anthropometric ratios
    ratios = MALE_RATIOS if gender == 'male' else FEMALE_RATIOS
    measurements = {key: round(ratio * user_height_cm, 1) for key, ratio in ratios.items()}
    return measurements

def validate_image(image_array):
    """Validate image quality."""
    height, width = image_array.shape[:2]
    if height < 256 or width < 256:
        return False, "Image too small (min 256x256)"
    
    gray = np.mean(image_array)
    if gray < 50:
        return False, "Image too dark"
    if gray > 220:
        return False, "Image too bright"
    
    return True, "OK"
