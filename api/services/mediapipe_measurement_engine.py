"""
MediaPipe-based Body Measurement Engine | PHASE 15: LANDMARK EXPORT
===================================================================
Calculates personalized circumferences and exports landmark maps for UI visualization.
"""

import os
import numpy as np
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

# Check for OpenCV availability
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Check for MediaPipe availability
HAS_MEDIAPIPE = False
pose_landmarker = None

def get_mediapipe_vision():
    """Late import of MediaPipe to prevent TensorFlow load in main process."""
    global HAS_MEDIAPIPE
    try:
        from mediapipe import Image, ImageFormat
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
        HAS_MEDIAPIPE = True
        return Image, ImageFormat, python, vision, PoseLandmarker, PoseLandmarkerOptions
    except ImportError as e:
        print(f"Warning: MediaPipe not available: {e}")
        return None, None, None, None, None, None

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR.parent / "models"

def get_pose_model_path():
    path = MODELS_DIR / "pose_landmarker_full.task"
    return str(path) if path.exists() else None

def initialize_pose_detector():
    global pose_landmarker
    # Late import to prevent module-level TF load
    mp_vision = get_mediapipe_vision()
    if not mp_vision[0]: return None
    Image, ImageFormat, python, vision, PoseLandmarker, PoseLandmarkerOptions = mp_vision

    model_path = get_pose_model_path()
    if not model_path: return None
    
    try:
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )
        pose_landmarker = PoseLandmarker.create_from_options(options)
        return pose_landmarker
    except Exception as e:
        print(f"❌ Failed to initialize Pose Landmarker: {e}")
        return None

def detect_pose_landmarks(image: np.ndarray) -> Optional[Dict[str, Tuple[float, float]]]:
    global pose_landmarker
    if pose_landmarker is None:
        if not initialize_pose_detector(): return None
    if not HAS_CV2: return None
    
    try:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_image)
        result = pose_landmarker.detect(mp_image)

        if not result or not result.pose_landmarks: return None
        landmarks = result.pose_landmarks[0]
        
        # Extended mapping for Phase 15 visualization
        landmark_mapping = {
            0: 'nose',
            11: 'left_shoulder', 12: 'right_shoulder',
            13: 'left_elbow', 14: 'right_elbow',
            23: 'left_hip', 24: 'right_hip',
            25: 'left_knee', 26: 'right_knee',
            27: 'left_ankle', 28: 'right_ankle',
        }
        
        landmark_dict = {}
        for idx, name in landmark_mapping.items():
            if idx < len(landmarks):
                lm = landmarks[idx]
                if lm.visibility > 0.5:
                    landmark_dict[name] = (lm.x, lm.y)
        return landmark_dict
    except Exception as e:
        return None

def calculate_pixels_per_cm(landmarks, img_height, user_height_cm):
    try:
        nose = landmarks.get('nose')
        left_ankle = landmarks.get('left_ankle')
        right_ankle = landmarks.get('right_ankle')
        
        if nose and left_ankle and right_ankle:
            ankle_mid_y = (left_ankle[1] + right_ankle[1]) / 2
            body_span_norm = abs(ankle_mid_y - nose[1])
            body_pixels = body_span_norm * img_height
            return body_pixels / (user_height_cm * 0.9)
    except:
        pass
    return (img_height * 0.7) / user_height_cm

def compute_elliptical_circumference(width_cm, depth_cm):
    a = width_cm / 2
    b = depth_cm / 2
    h = ((a - b) ** 2) / ((a + b) ** 2)
    return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

def extract_measurements_from_dual_photos(
    front_image: np.ndarray,
    side_image: np.ndarray,
    user_height_cm: float,
    gender: str = 'male'
) -> Tuple[Dict[str, float], Dict[str, Tuple[float, float]]]:
    """
    PHASE 15: Volumetric Extraction + Landmark Export.
    Returns: (measurements_dict, landmarks_for_ui)
    """
    front_lms = detect_pose_landmarks(front_image)
    side_lms = detect_pose_landmarks(side_image)
    
    if not front_lms:
        return _extract_proportional_measurements(user_height_cm, gender), {}

    px_cm_front = calculate_pixels_per_cm(front_lms, front_image.shape[0], user_height_cm)
    px_cm_side = px_cm_front
    if side_lms:
        px_cm_side = calculate_pixels_per_cm(side_lms, side_image.shape[0], user_height_cm)

    def get_width(lms, px_cm, img_width):
        l_sh = lms.get('left_shoulder')
        r_sh = lms.get('right_shoulder')
        l_hp = lms.get('left_hip')
        r_hp = lms.get('right_hip')
        shoulder_w = abs(r_sh[0] - l_sh[0]) * img_width / px_cm if l_sh and r_sh else 0
        hip_w = abs(r_hp[0] - l_hp[0]) * img_width / px_cm if l_hp and r_hp else 0
        return shoulder_w, hip_w

    f_sh_w, f_hp_w = get_width(front_lms, px_cm_front, front_image.shape[1])
    s_sh_d, s_hp_d = 0, 0
    if side_lms:
        s_sh_d, s_hp_d = get_width(side_lms, px_cm_side, side_image.shape[1])

    if s_sh_d == 0: s_sh_d = f_sh_w * 0.65
    if s_hp_d == 0: s_hp_d = f_hp_w * 0.85

    measurements = {}
    measurements['Shoulder'] = round(f_sh_w, 1)
    measurements['Chest Round'] = round(compute_elliptical_circumference(f_sh_w * 1.1, s_sh_d * 1.2), 1)
    measurements['Waist Round'] = round(compute_elliptical_circumference(f_hp_w * 0.9, s_hp_d * 0.95), 1)
    measurements['Hip Round'] = round(compute_elliptical_circumference(f_hp_w * 1.05, s_hp_d * 1.1), 1)

    base_m = _extract_proportional_measurements(user_height_cm, gender)
    for k, v in base_m.items():
        if k not in measurements: measurements[k] = v

    print(f"✅ Phase 15: Volumetric Extraction Success.")
    return measurements, front_lms

def _extract_proportional_measurements(user_height_cm: float, gender: str = 'male') -> Dict[str, float]:
    if gender == 'male':
        ratios = {
            'Shoulder': 0.265, 'Neck Round': 0.224, 'Chest Round': 0.588, 'Stomach Round': 0.500,
            'Waist Round': 0.471, 'Half Length': 0.353, 'Full Top Length': 0.441, 'Across Back': 0.247,
            'Across Chest': 0.259, 'Hip Round': 0.559, 'Thigh Round': 0.324, 'Knee Round': 0.224,
            'Calf Round': 0.212, 'Ankle Round': 0.153, 'Trouser Waist': 0.482, 'Trouser Length': 0.588,
            'Inseam': 0.459, 'Crotch Depth': 0.165,
        }
    else:
        ratios = {
            'Shoulder': 0.230, 'Neck Round': 0.206, 'Bust Round': 0.521, 'High Bust': 0.460,
            'Under Bust': 0.412, 'Bust Point': 0.121, 'Shoulder to Bust Point': 0.145,
            'Shoulder to Under Bust': 0.170, 'Shoulder to Waist': 0.230, 'Front Waist Length': 0.218,
            'Back Waist Length': 0.242, 'Across Chest': 0.206, 'Across Back': 0.194,
            'Armhole Round': 0.242, 'Sleeve Length': 0.333, 'Bicep Round': 0.170, 'Elbow Round': 0.145,
            'Wrist Round': 0.109, 'Waist Round': 0.400, 'Half Length': 0.315, 'Waist to Hip': 0.109,
            'Upper Hip': 0.521, 'Hip Round': 0.570, 'Thigh Round': 0.315, 'Knee Round': 0.206,
            'Calf Round': 0.194, 'Ankle Round': 0.133,
        }
    return {k: round(v * user_height_cm, 1) for k, v in ratios.items()}

def validate_image(image_array):
    if not HAS_CV2: return True, "OK"
    height, width = image_array.shape[:2]
    if height < 256 or width < 256: return False, "Image too small"
    gray = np.mean(image_array)
    if gray < 50: return False, "Image too dark"
    if gray > 220: return False, "Image too bright"
    return True, "OK"
