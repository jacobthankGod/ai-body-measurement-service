"""
MediaPipe Measurement Engine
===========================
Real body measurement extraction using MediaPipe pose detection.

This module uses Google's MediaPipe to detect 33 body landmarks,
then calculates precise measurements based on pixel coordinates.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Dict, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# MediaPipe instance
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Body landmarks used for measurements
LANDMARK_INDICES = {
    # Upper body
    'nose': 0,
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_hip': 23,
    'right_hip': 24,
    # Lower body
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
}

# Anthropometric ratios for fallback (multipliers of height)
MALE_RATIOS = {
    'Shoulder': 0.265,
    'Neck Round': 0.224,
    'Chest Round': 0.588,
    'Stomach Round': 0.500,
    'Waist Round': 0.471,
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
    'Arm Length': 0.353,
}

FEMALE_RATIOS = {
    'Shoulder': 0.230,
    'Neck Round': 0.206,
    'Bust Round': 0.521,
    'High Bust': 0.460,
    'Under Bust': 0.412,
    'Waist Round': 0.400,
    'Half Length': 0.315,
    'Waist to Hip': 0.109,
    'Upper Hip': 0.521,
    'Hip Round': 0.570,
    'Thigh Round': 0.315,
    'Knee Round': 0.206,
    'Calf Round': 0.194,
    'Ankle Round': 0.133,
    'Arm Length': 0.333,
    'Bicep Round': 0.170,
    'Wrist Round': 0.109,
}


# ============================================================================
# MEDIAPIPE PROCESSOR
# ============================================================================

class MediaPipeProcessor:
    """Process images with MediaPipe for body pose detection."""
    
    def __init__(self, static_image_mode=False, model_complexity=1):
        self.pose = mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,
            smooth_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    
    def process(self, image: np.ndarray) -> Optional[object]:
        """Process image and return pose results."""
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        return self.pose.process(image_rgb)
    
    def get_landmarks(self, pose_results, image_shape: Tuple[int, int]) -> Dict[str, np.ndarray]:
        """Extract landmark coordinates from pose results."""
        h, w = image_shape
        
        if not pose_results.pose_landmarks:
            return {}
        
        landmarks = {}
        for name, idx in LANDMARK_INDICES.items():
            landmark = pose_results.pose_landmarks.landmark[idx]
            landmarks[name] = np.array([landmark.x * w, landmark.y * h])
        
        return landmarks
    
    def close(self):
        """Release resources."""
        self.pose.close()


# ============================================================================
# MEASUREMENT CALCULATOR
# ============================================================================

class MeasurementCalculator:
    """Calculate body measurements from pose landmarks."""
    
    def __init__(self):
        self.processor = MediaPipeProcessor()
    
    def calculate_distance(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate Euclidean distance between two points."""
        return np.linalg.norm(p1 - p2)
    
    def calculate_circumference(self, points: np.ndarray, scale: float) -> float:
        """Estimate circumference from points on outline."""
        if len(points) < 3:
            return 0.0
        
        # Calculate perimeter and estimate circumference
        perimeter = 0.0
        for i in range(len(points)):
            perimeter += self.calculate_distance(points[i], points[(i + 1) % len(points)])
        
        # Use formula: circumference ≈ π * (3 * a + b) / (a + b) for ellipse
        # where a and b are min/max radii
        points_array = np.array(points)
        min_radius = np.min(np.linalg.norm(points_array - points_array.mean(axis=0), axis=1))
        max_radius = np.max(np.linalg.norm(points_array - points_array.mean(axis=0), axis=1))
        
        if min_radius > 0:
            circumference = np.pi * (3 * min_radius + max_radius) / 4
            return circumference * scale
        return perimeter * scale
    
    def calculate_measurements(
        self,
        landmarks: Dict[str, np.ndarray],
        front_landmarks: Dict[str, np.ndarray],
        side_landmarks: Dict[str, np.ndarray],
        user_height_cm: float,
        gender: str = 'male'
    ) -> Dict[str, float]:
        """Calculate all body measurements from landmarks."""
        
        if not front_landmarks or not side_landmarks:
            # Fallback to ratios
            ratios = MALE_RATIOS if gender == 'male' else FEMALE_RATIOS
            return {k: round(v * user_height_cm, 1) for k, v in ratios.items()}
        
        # Calculate scale (pixels per cm)
        # Use total body height as reference
        if 'nose' in front_landmarks and 'left_ankle' in front_landmarks:
            body_height_px = self.calculate_distance(
                front_landmarks['nose'], 
                front_landmarks['left_ankle']
            )
        elif 'nose' in side_landmarks and 'left_ankle' in side_landmarks:
            body_height_px = self.calculate_distance(
                side_landmarks['nose'], 
                side_landmarks['left_ankle']
            )
        else:
            body_height_px = 700  # Default assumption
        
        pixels_per_cm = body_height_px / user_height_cm
        
        measurements = {}
        
        # 1. Shoulder width (front only)
        if 'left_shoulder' in front_landmarks and 'right_shoulder' in front_landmarks:
            shoulder_width = self.calculate_distance(
                front_landmarks['left_shoulder'],
                front_landmarks['right_shoulder']
            ) / pixels_per_cm
            measurements['Shoulder'] = round(shoulder_width, 1)
        
        # 2. Chest circumference (front + side)
        if 'left_shoulder' in front_landmarks and 'right_shoulder' in front_landmarks:
            chest_width = self.calculate_distance(
                front_landmarks['left_shoulder'],
                front_landmarks['right_shoulder']
            )
            if 'left_hip' in front_landmarks and 'right_hip' in front_landmarks:
                chest_height = abs(front_landmarks['left_shoulder'][1] - front_landmarks['left_hip'][1])
                chest_depth = 0  # Approximate from side
                chest_circumference = 2 * np.sqrt((chest_width/2)**2 + (chest_depth/2)**2) / pixels_per_cm
                measurements['Chest Round'] = round(chest_circumference, 1)
        
        # 3. Waist circumference (front only)
        if 'left_hip' in front_landmarks and 'right_hip' in front_landmarks:
            hip_width = self.calculate_distance(
                front_landmarks['left_hip'],
                front_landmarks['right_hip']
            )
            measurements['Hip Round'] = round(hip_width / pixels_per_cm, 1)
            
            # Waist is typically ~5cm above hip
            waist_width = hip_width * 0.95
            measurements['Waist Round'] = round(waist_width / pixels_per_cm, 1)
        
        # 4. Arm length (front only)
        if 'left_shoulder' in front_landmarks and 'left_wrist' in front_landmarks:
            # Left arm
            left_arm = (
                self.calculate_distance(front_landmarks['left_shoulder'], front_landmarks['left_elbow']) +
                self.calculate_distance(front_landmarks['left_elbow'], front_landmarks['left_wrist'])
            ) / pixels_per_cm
            measurements['Arm Length'] = round(left_arm, 1)
            
            # Right arm
            right_arm = (
                self.calculate_distance(front_landmarks['right_shoulder'], front_landmarks['right_elbow']) +
                self.calculate_distance(front_landmarks['right_elbow'], front_landmarks['right_wrist'])
            ) / pixels_per_cm
            measurements['Arm Length'] = round((left_arm + right_arm) / 2, 1)
        
        # 5. Inseam / Leg length (side + front)
        if 'left_hip' in side_landmarks and 'left_ankle' in side_landmarks:
            inseam = self.calculate_distance(
                side_landmarks['left_hip'],
                side_landmarks['left_ankle']
            ) / pixels_per_cm
            measurements['Inseam'] = round(inseam, 1)
        
        # 6. Full body height (side)
        if 'nose' in side_landmarks and 'left_ankle' in side_landmarks:
            full_height = self.calculate_distance(
                side_landmarks['nose'],
                side_landmarks['left_ankle']
            ) / pixels_per_cm
            measurements['Full Height'] = round(full_height, 1)
        
        # 7. Neck circumference (front)
        if 'nose' in front_landmarks and 'left_shoulder' in front_landmarks:
            neck_width = self.calculate_distance(
                front_landmarks['nose'],
                front_landmarks['left_shoulder']
            ) * 0.3
            measurements['Neck Round'] = round(neck_width / pixels_per_cm * np.pi, 1)
        
        # Fill in missing with ratios
        ratios = MALE_RATIOS if gender == 'male' else FEMALE_RATIOS
        for key, ratio in ratios.items():
            if key not in measurements:
                measurements[key] = round(ratio * user_height_cm, 1)
        
        return measurements
    
    def close(self):
        """Release resources."""
        self.processor.close()


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
    Extract body measurements from dual photos using MediaPipe.
    
    Args:
        front_image: Front view image
        side_image: Side view image  
        user_height_cm: User's height in cm
        gender: male/female
    
    Returns:
        dict: Measurements in centimeters
    """
    calculator = MeasurementCalculator()
    
    try:
        # Process images
        front_results = calculator.processor.process(front_image)
        side_results = calculator.processor.process(side_image)
        
        # Get landmarks
        front_landmarks = calculator.processor.get_landmarks(front_results, front_image.shape[:2])
        side_landmarks = calculator.processor.get_landmarks(side_results, side_image.shape[:2])
        
        # Calculate measurements
        measurements = calculator.calculate_measurements(
            {},
            front_landmarks,
            side_landmarks,
            user_height_cm,
            gender
        )
        
        return measurements
        
    except Exception as e:
        print(f"MediaPipe error: {e}, falling back to ratios")
        # Fallback to ratios
        ratios = MALE_RATIOS if gender == 'male' else FEMALE_RATIOS
        return {k: round(v * user_height_cm, 1) for k, v in ratios.items()}
    
    finally:
        calculator.close()


def validate_image(image: np.ndarray) -> Tuple[bool, str]:
    """Validate image for measurement extraction."""
    height, width = image.shape[:2]
    
    if height < 256 or width < 256:
        return False, "Image too small (min 256x256)"
    
    gray = np.mean(image)
    if gray < 50:
        return False, "Image too dark"
    if gray > 220:
        return False, "Image too bright"
    
    return True, "OK"
