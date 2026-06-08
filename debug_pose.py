import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from api.services.extract_measurements import ENGINE

def debug_pose(image_path):
    print(f"--- Debugging Pose for {image_path} ---")
    if not os.path.exists(image_path):
        print("Error: File not found")
        return

    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read image")
        return

    # Ensure engine is initialized
    if not ENGINE.initialized:
        if not ENGINE.initialize():
            print(f"Error: Could not initialize engine: {ENGINE.last_error}")
            return

    # Pre-process
    h, w = image.shape[:2]
    img_resized = cv2.resize(image, (224, 224))
    img_normalized = 2 * ((img_resized / 255.0) - 0.5)
    img_batch = np.expand_dims(img_normalized, 0)

    # Predict
    results = ENGINE.model.predict_dict(img_batch)

    joints_2d = results['joints'][0]
    cams = results['cams'][0]

    print(f"Camera (scale, tx, ty): {cams}")
    print("Joints 2D:")
    for i, j in enumerate(joints_2d):
        print(f"  {i}: {j}")

if __name__ == "__main__":
    debug_pose("/Users/mac/ai-body-scan-saas/pose_model.png")
