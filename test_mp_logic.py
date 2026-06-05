import sys
import os
import numpy as np

# Add current dir to path
sys.path.append(os.getcwd())

from api.services.mediapipe_measurement_engine import extract_measurements_from_landmarks

# Create synthetic landmarks for a 170cm male
# (x, y) normalized coords
landmarks = {
    'nose': (0.5, 0.1),
    'left_shoulder': (0.4, 0.25),
    'right_shoulder': (0.6, 0.25),
    'left_hip': (0.45, 0.5),
    'right_hip': (0.55, 0.5),
    'left_ankle': (0.48, 0.9),
    'right_ankle': (0.52, 0.9),
}

image_shape = (1000, 1000)
user_height = 170.0

results = extract_measurements_from_landmarks(landmarks, image_shape, user_height, gender='male')

print("\n--- SYNTHETIC LANDMARK EXTRACTION ---")
print(f"Height: {user_height}cm")
print(f"Shoulder (landmarks): {results.get('Shoulder')} cm")
print(f"Waist Round (estimated from hip landmarks): {results.get('Waist Round')} cm")

# Ratio-based Shoulder for 170cm is 45.1
# Let's see if our synthetic shoulder (0.2 width on 1000px image) differs.
# pixels_per_cm = (0.9 - 0.1) * 1000 / 170 = 800 / 170 = 4.7 px/cm
# shoulder_px = (0.6 - 0.4) * 1000 = 200 px
# shoulder_cm = 200 / 4.7 = 42.5 cm
# Our result should be 42.5 if landmarks are used, NOT 45.1.
