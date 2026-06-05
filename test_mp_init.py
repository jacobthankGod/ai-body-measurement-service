import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from api.services.mediapipe_measurement_engine import initialize_pose_detector, HAS_MEDIAPIPE, POSE_MODEL_PATH
    print(f"HAS_MEDIAPIPE: {HAS_MEDIAPIPE}")
    print(f"POSE_MODEL_PATH: {POSE_MODEL_PATH}")
    print(f"Model exists: {os.path.exists(POSE_MODEL_PATH) if POSE_MODEL_PATH else False}")

    detector = initialize_pose_detector()
    if detector:
        print("SUCCESS: Detector initialized")
    else:
        print("FAILURE: Detector is None")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
