"""
KORRA Vision Guard | PHASE 14: INPUT INTEGRITY
==============================================
Performs pre-flight validation on body scan photos to ensure
clinical accuracy (Lighting, Pose, Resolution).
"""
import numpy as np
import cv2

class VisionGuard:
    @staticmethod
    def validate_photo(image_array: np.ndarray, side: str = "front"):
        """
        Validate image quality and subject positioning.
        Returns: (bool, str) -> (is_valid, reason)
        """
        if image_array is None or image_array.size == 0:
            return False, "Empty image data."

        h, w = image_array.shape[:2]

        # 1. Resolution Check
        if h < 480 or w < 480:
            return False, f"Low resolution ({w}x{h}). High-fidelity scans require min 480px."

        # 2. Lighting Check (Brightness & Contrast)
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)

        if avg_brightness < 40:
            return False, "Lighting too low. Please increase lighting for biometric accuracy."
        if avg_brightness > 230:
            return False, "Lighting too bright (overexposed). Reduce direct light."

        # 3. Contrast Check (ensure subject isn't blending into background)
        contrast = gray.std()
        if contrast < 20:
            return False, "Low contrast. Ensure subject stands against a neutral background."

        # 4. Preliminary Pose Alignment (Face/Shoulder presence)
        # Note: Deep pose validation happens in the MediaPipe stage,
        # this is just the immediate optical guard.

        return True, "Input Verified."

    @staticmethod
    def analyze_pose_stability(landmarks: dict, side: str = "front"):
        """
        Verify if the subject is standing in the correct clinical pose.
        """
        if not landmarks:
            return False, "Subject not detected. Stand clearly in frame."

        # Check for shoulder alignment (Front)
        if side == "front":
            l_sh = landmarks.get('left_shoulder')
            r_sh = landmarks.get('right_shoulder')
            if l_sh and r_sh:
                # Check for extreme tilt (>15 degrees)
                tilt = abs(l_sh[1] - r_sh[1])
                if tilt > 0.15:
                    return False, "Shoulder tilt detected. Stand straight for clinical fit."

        return True, "Pose Verified."
