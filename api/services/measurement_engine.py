"""
Measurement Engine
================
Cascade measurement extraction:
1. HMR 3D (DeepLab + HMR + vertex-based) - BEST accuracy
2. MediaPipe pose detection - MEDIUM accuracy  
3. Anthropometric ratios - FALLBACK

Uses GitHub repo: https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision
"""
import numpy as np
from pathlib import Path

# Try to import HMR-based extraction (GitHub repo)
try:
    from api.services.extract_measurements import extract_measurements_from_hmr
    HAS_HMR = True
except ImportError:
    HAS_HMR = False
    # print("HMR not available yet, will try other methods")

# Try to import MediaPipe engine
try:
    from api.services.mediapipe_measurement_engine import (
        extract_measurements_from_dual_photos as mp_extract,
        validate_image as mp_validate,
    )
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    # print("MediaPipe not available, using ratio-based extraction")

# Check for HMR models
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR.parent / "models"

# Check multiple possible checkpoint naming patterns
if MODELS_DIR.exists():
    hmr_patterns = [
        MODELS_DIR / "hmr_model.ckpt.index",
        MODELS_DIR / "model.ckpt-667589.index",
    ]
    HMR_READY = any(p.exists() for p in hmr_patterns)
else:
    HMR_READY = False

# Full 18 Male Measurements
MALE_RATIOS = {
    'Shoulder': 0.265,
    'Neck Round': 0.224,
    'Chest Round': 0.588,
    'Stomach Round': 0.500,
    'Waist Round': 0.471,
    'Half Length': 0.353,
    'Full Top Length': 0.441,
    'Across Back': 0.247,
    'Across Chest': 0.259,
    'Hip Round': 0.559,
    'Thigh Round': 0.324,
    'Knee Round': 0.224,
    'Calf Round': 0.212,
    'Ankle Round': 0.153,
    'Trouser Waist': 0.482,
    'Trouser Length': 0.588,
    'Inseam': 0.459,
    'Crotch Depth': 0.165,
}

# Full 27 Female Measurements
FEMALE_RATIOS = {
    'Shoulder': 0.230,
    'Neck Round': 0.206,
    'Bust Round': 0.521,
    'High Bust': 0.460,
    'Under Bust': 0.412,
    'Bust Point': 0.121,
    'Shoulder to Bust Point': 0.145,
    'Shoulder to Under Bust': 0.170,
    'Shoulder to Waist': 0.230,
    'Front Waist Length': 0.218,
    'Back Waist Length': 0.242,
    'Across Chest': 0.206,
    'Across Back': 0.194,
    'Armhole Round': 0.242,
    'Sleeve Length': 0.333,
    'Bicep Round': 0.170,
    'Elbow Round': 0.145,
    'Wrist Round': 0.109,
    'Waist Round': 0.400,
    'Half Length': 0.315,
    'Waist to Hip': 0.109,
    'Upper Hip': 0.521,
    'Hip Round': 0.570,
    'Thigh Round': 0.315,
    'Knee Round': 0.206,
    'Calf Round': 0.194,
    'Ankle Round': 0.133,
}

def extract_measurements_from_dual_photos(front_image, side_image, user_height_cm, gender='male'):
    """
    Extract body measurements using cascade pipeline:
    1. HMR 3D (DeepLab + HMR + vertices) - BEST ±1-2cm
    2. MediaPipe pose detection - MEDIUM ±3-5cm  
    3. Anthropometric ratios - FALLBACK ±5-10cm
    
    Args:
        front_image: OpenCV image (front view)
        side_image: OpenCV image (side view)
        user_height_cm: User height in cm
        gender: male/female
    
    Returns:
        dict: Measurements in centimeters
    """
    # 1. Try HMR 3D extraction (best accuracy)
    if HAS_HMR and HMR_READY:
        try:
            result = extract_measurements_from_hmr(front_image, user_height_cm)
            if result and 'height' in result:
                print("✅ Using HMR 3D extraction")
                return result
        except Exception as e:
            print(f"HMR extraction failed: {e}, trying MediaPipe...")
    
    # 2. Try MediaPipe (medium accuracy)
    if HAS_MEDIAPIPE:
        try:
            return mp_extract(front_image, side_image, user_height_cm, gender)
        except Exception as e:
            print(f"MediaPipe extraction failed: {e}, falling back to ratios")
    
    # 3. Fallback to anthropometric ratios (lowest accuracy)
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
