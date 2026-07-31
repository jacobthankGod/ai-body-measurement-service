"""
Configuration for the Blender cloth draping pipeline.
9 anchor sizes covering the full measurement range for continuous interpolation.
"""
import os

# ── 9 Anchor Body Sizes ──
# Spans chest 82-118cm, waist 70-108cm, hip 82-118cm
# Density: tighter at center (M range) for better interpolation accuracy
SIZES = {
    "XXS": {"chest": 82,  "waist": 70,  "hip": 82,  "height": 160},
    "XS":  {"chest": 88,  "waist": 76,  "hip": 88,  "height": 165},
    "S":   {"chest": 94,  "waist": 82,  "hip": 94,  "height": 170},
    "M":   {"chest": 100, "waist": 88,  "hip": 100, "height": 175},
    "ML":  {"chest": 106, "waist": 94,  "hip": 106, "height": 178},
    "L":   {"chest": 112, "waist": 100, "hip": 112, "height": 180},
    "XL":  {"chest": 118, "waist": 106, "hip": 118, "height": 183},
    "XXL": {"chest": 124, "waist": 112, "hip": 124, "height": 185},
    "3XL": {"chest": 130, "waist": 118, "hip": 130, "height": 188},
}

# Base size (identity morph = no displacement)
BASE_SIZE = "XXS"

# ── MakeHuman Morph Mapping ──
# From model_config.json morph_limits (male)
# Maps measurement name → (morph_index, low_cm, high_cm)
MALE_MORPH_MAP = {
    "height":       (0,  175, 195),
    "chest":        (1,  96,  130),
    "neck":         (2,  39,  45),
    "shoulders":    (4,  43,  55),
    "bust_girth":   (6,  86,  100),
    "stomach_form": (7,  55,  140),
    "waist":        (8,  84,  140),
    "arm_length":   (9,  62,  80),
    "armgirth":     (10, 32,  42),
    "wrist_girth":  (11, 17,  22),
    "hips":         (12, 96,  130),
    "hip_height":   (13, 28,  38),
    "thigh_girth":  (14, 55,  75),
    "calf_girth":   (16, 36,  48),
    "ankle_round":  (17, 24,  35),
    "across_chest": (18, 41,  55),
    "knee_round":   (19, 38,  50),
    "across_back":  (20, 39,  55),
    "inseam":       (23, 91,  110),
    "trouser_waist": (24, 84,  150),
}

FEMALE_MORPH_MAP = {
    "height":       (0,  160, 185),
    "chest":        (1,  80,  120),
    "neck":         (2,  33,  40),
    "shoulders":    (4,  38,  50),
    "bust_girth":   (6,  76,  110),
    "waist":        (8,  64,  110),
    "hips":         (12, 82,  120),
    "thigh_girth":  (14, 48,  70),
    "calf_girth":   (16, 32,  44),
}

# ── Cloth Simulation Parameters ──
# PROVEN WORKING SETTINGS:
# - impulse_clamp=0.01 prevents collision explosion
# - 1cm outward offset prevents initial penetration
# - collision proxy (2000 faces) is 13x faster than full body (26K)
# - quality=2 gives ~4s/frame, quality=5 gives ~14s/frame
CLOTH_PARAMS = {
    "mass": 0.05,                  # 0.03-0.1 kg is the sweet spot for anti-jitter
    "tension_stiffness": 25.0,
    "compression_stiffness": 25.0,
    "shear_stiffness": 25.0,
    "bending_stiffness": 5.0,
    "tension_damping": 5.0,
    "compression_damping": 5.0,
    "shear_damping": 5.0,
    "bending_damping": 5.0,
    "pressure": 0.0,
    "collision_quality": 10,       # More iterations = better accuracy
    "self_collision_distance": 0.001,
    "self_collision_friction": 0.1,
    "frame_count": 60,             # Increased for better draping
    "pin_percentage": 0.10,
    "impulse_clamp": 0.5,          # Prevents explosions
    "garment_offset": 0.01,        # 1cm outward offset before simulation
}

# ── Collision Proxy ──
COLLISION_PARAMS = {
    "target_faces": 2000,
    "damping": 0.1,               # Reduced to allow natural drape
    "friction_factor": 0.1,
    "thickness_outer": 0.05,      # 5cm padding distance
    "thickness_inner": 0.05,
    "use_culling": False,         # CRITICAL: body has mixed normals
}

# ── Paths ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAKEHUMAN_DIR = os.path.join(PROJECT_ROOT, "public", "models", "makehuman")
GARMENTS_DIR = os.path.join(PROJECT_ROOT, "public", "models", "garments")
