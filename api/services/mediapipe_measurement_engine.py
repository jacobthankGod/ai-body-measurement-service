"""
MediaPipe-based Body Measurement Engine
======================================
Uses Google MediaPipe Pose Landmarker for accurate body keypoint detection.
FastAPI-compatible wrapper for measurement extraction.

Copied from desby_app/backend/ai_measurement/mediapipe_measurement_engine.py
"""

import os
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple

# Check for OpenCV availability
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("Warning: OpenCV not available")

# Check for MediaPipe availability
HAS_MEDIAPIPE = False
pose_landmarker = None

try:
    from mediapipe import Image, ImageFormat
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
    HAS_MEDIAPIPE = True
except ImportError as e:
    print(f"Warning: MediaPipe not available: {e}")


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR.parent / "models"
DATA_DIR = BASE_DIR.parent / "data"

# Only attempt directory creation if not running on Vercel
if os.environ.get('VERCEL', '0') != '1':
    MODELS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

# Pose Landmarker model - use existing model file
def get_pose_model_path():
    path = MODELS_DIR / "pose_landmarker_full.task"
    return str(path) if path.exists() else None

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_pose_detector():
    """Initialize MediaPipe Pose Landmarker."""
    global pose_landmarker
    
    if not HAS_MEDIAPIPE:
        return None

    model_path = get_pose_model_path()
    if not model_path:
        print("⚠️ MediaPipe model file not found. Server-side pose detection disabled.")
        return None
    
    try:
        # Configure Pose Landmarker - using bundled model
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )
        
        options = PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )
        
        pose_landmarker = PoseLandmarker.create_from_options(options)
        print("✅ MediaPipe Pose Landmarker initialized")
        return pose_landmarker
        
    except Exception as e:
        print(f"❌ Failed to initialize Pose Landmarker: {e}")
        return None


# ============================================================================
# POSE DETECTION
# ============================================================================

def detect_pose_landmarks(image: np.ndarray) -> Optional[Dict[str, Tuple[float, float]]]:
    """
    Detect pose landmarks using MediaPipe Tasks API.
    
    Args:
        image: OpenCV image (BGR format)
    
    Returns:
        Dict of landmark name -> (x, y) normalized coordinates
        or None if detection fails
    """
    global pose_landmarker
    
    if pose_landmarker is None:
        if not initialize_pose_detector():
            return None
    
    if not HAS_CV2:
        return None
    
    try:
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe image
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_image)
        
        # Detect pose
        result = pose_landmarker.detect(mp_image)
        
        if not result or not result.pose_landmarks:
            return None
        
        landmarks = result.pose_landmarks[0]
        
        # MediaPipe landmark indices
        landmark_mapping = {
            0: 'nose',
            11: 'left_shoulder',
            12: 'right_shoulder',
            13: 'left_elbow',
            14: 'right_elbow',
            15: 'left_wrist',
            16: 'right_wrist',
            23: 'left_hip',
            24: 'right_hip',
            25: 'left_knee',
            26: 'right_knee',
            27: 'left_ankle',
            28: 'right_ankle',
        }
        
        landmark_dict = {}
        for idx, name in landmark_mapping.items():
            if idx < len(landmarks):
                lm = landmarks[idx]
                if lm.visibility > 0.5:
                    landmark_dict[name] = (lm.x, lm.y)
        
        return landmark_dict
    
    except Exception as e:
        print(f"⚠️ Pose detection error: {e}")
        return None


# ============================================================================
# MEASUREMENT EXTRACTION
# ============================================================================

def extract_measurements_from_landmarks(
    landmarks: Dict[str, Tuple[float, float]],
    image_shape: Tuple[int, int],
    user_height_cm: float,
    gender: str = 'male'
) -> Dict[str, float]:
    """
    Extract body measurements from pose landmarks.
    
    Args:
        landmarks: Dict of landmark name -> (x, y)
        image_shape: (height, width)
        user_height_cm: User's height in cm
        gender: 'male' or 'female'
    
    Returns:
        Dictionary of measurements in cm
    """
    if landmarks is None:
        return None
    
    img_height, img_width = image_shape[:2]
    
    # Calculate pixel-to-cm ratio
    try:
        nose = landmarks.get('nose')
        left_ankle = landmarks.get('left_ankle')
        right_ankle = landmarks.get('right_ankle')
        
        if nose and left_ankle and right_ankle:
            ankle_mid_y = (left_ankle[1] + right_ankle[1]) / 2
            body_pixels = (nose[1] - ankle_mid_y) * img_height
            pixels_per_cm = body_pixels / user_height_cm if body_pixels > 0 else img_height / user_height_cm
        else:
            pixels_per_cm = img_height / user_height_cm
    except:
        pixels_per_cm = (img_height * 0.7) / user_height_cm
    
    measurements = {}
    
    # Calculate key measurements
    try:
        left_shoulder = landmarks.get('left_shoulder')
        right_shoulder = landmarks.get('right_shoulder')
        
        if left_shoulder and right_shoulder:
            shoulder_px = (right_shoulder[0] - left_shoulder[0]) * img_width
            measurements['Shoulder'] = round(shoulder_px / pixels_per_cm, 1)
        
        left_hip = landmarks.get('left_hip')
        right_hip = landmarks.get('right_hip')
        
        if left_hip and right_hip:
            hip_px = (right_hip[0] - left_hip[0]) * img_width
            measurements['Hip Round'] = round(hip_px * 2.1 / pixels_per_cm, 1)
            measurements['Waist Round'] = round(hip_px * 1.8 / pixels_per_cm, 1)
            measurements['Chest Round'] = round(hip_px * 2.2 / pixels_per_cm, 1)
    except:
        pass
    
# Full 18 male / 27 female anthropometric ratios
    if gender == 'male':
        ratios = {
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
    else:
        ratios = {
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
    
    for key, ratio in ratios.items():
        measurements[key] = round(ratio * user_height_cm, 1)
    
    return measurements


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def extract_measurements_from_dual_photos(
    front_image: np.ndarray,
    side_image: np.ndarray,
    user_height_cm: float,
    gender: str = 'male'
) -> Dict[str, float]:
    """
    Extract body measurements from dual photos.
    
    Args:
        front_image: OpenCV image (front view)
        side_image: OpenCV image (side view) 
        user_height_cm: User's height in cm
        gender: 'male' or 'female'
    
    Returns:
        Dictionary of measurements in cm
    """
    # Try MediaPipe pose detection first
    if HAS_MEDIAPIPE and pose_landmarker is not None:
        try:
            landmarks = detect_pose_landmarks(front_image)
            if landmarks:
                measurements = extract_measurements_from_landmarks(
                    landmarks, front_image.shape, user_height_cm, gender
                )
                if measurements:
                    print("✅ Using MediaPipe pose detection")
                    return measurements
        except Exception as e:
            print(f"⚠️ MediaPipe failed: {e}")
    
    # Fallback to proportional calculation
    return _extract_proportional_measurements(front_image, user_height_cm, gender)


def _extract_proportional_measurements(
    front_image: np.ndarray,
    user_height_cm: float,
    gender: str = 'male'
) -> Dict[str, float]:
    """Extract measurements using proportional calculation (fallback)."""
    # Full 18 male / 27 female ratios
    if gender == 'male':
        ratios = {
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
    else:
        ratios = {
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
    
    measurements = {}
    for key, ratio in ratios.items():
        measurements[key] = round(ratio * user_height_cm, 1)
    
    return measurements


def validate_image(image_array):
    """Validate image quality."""
    if not HAS_CV2:
        return True, "OK"
    
    height, width = image_array.shape[:2]
    if height < 256 or width < 256:
        return False, "Image too small (min 256x256)"
    
    gray = np.mean(image_array)
    if gray < 50:
        return False, "Image too dark"
    if gray > 220:
        return False, "Image too bright"
    
    return True, "OK"


# Export for measurement_engine.py
__all__ = [
    'extract_measurements_from_dual_photos',
    'validate_image',
    'detect_pose_landmarks',
    'HAS_MEDIAPIPE'
]
