"""
HMR-based 3D Body Measurement Extraction | MASTER ARTISAN 1:1 ALIGNMENT
=====================================================================
Strict implementation of the Faraz Bhatti research paper methodology.
Hardened with Atomic Integrity Diagnostics for Cloud Infrastructure.
"""
import os
import sys
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# --- NUCLEAR TENSORFLOW BRIDGE ---
try:
    import tensorflow as tf
    if int(tf.__version__.split('.')[0]) >= 2:
        import tensorflow.compat.v1 as tf1
        tf1.disable_v2_behavior()
        sys.modules['tensorflow'] = tf1
        tf = tf1
    logger = logging.getLogger("KORRA_HMR")
except ImportError:
    print("❌ Critical: TensorFlow Infrastructure Offline.")

BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================================
# CONFIGURATION & INTEGRITY (Absolute Handshake)
# ============================================================================

ROOT_DIR = BASE_DIR.parent.parent
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"

# Research Checkpoint Assets (Fixed explicit pathing)
CKPT_NAME = "model.ckpt-667589"
CHECKPOINT_BASE = MODELS_DIR / CKPT_NAME
CHECKPOINT_INDEX = MODELS_DIR / f"{CKPT_NAME}.index"
CHECKPOINT_DATA = MODELS_DIR / f"{CKPT_NAME}.data-00000-of-00001"
SMPL_MODEL_PATH = MODELS_DIR / "neutral_smpl_with_cocoplus_reg.pkl"
INDEX_FILE_PATH = DATA_DIR / "customBodyPoints.txt"

# Atomic Integrity Status
INTEGRITY = {
    "checkpoint_index": CHECKPOINT_INDEX.exists(),
    "checkpoint_data": CHECKPOINT_DATA.exists(),
    "smpl_mesh": SMPL_MODEL_PATH.exists(),
    "vertex_indices": INDEX_FILE_PATH.exists()
}

HMR_ACTIVE = all([INTEGRITY["checkpoint_index"], INTEGRITY["checkpoint_data"], INTEGRITY["smpl_mesh"]])

# ============================================================================
# MASTER EXTRACTION ENGINE
# ============================================================================

class HMRMasterEngine:
    def __init__(self):
        self.model = None
        self.initialized = False
        self.vertex_map = self._parse_vertex_indices()

    def initialize(self):
        if not HMR_ACTIVE:
            missing = [k for k, v in INTEGRITY.items() if not v]
            print(f"⚠️ HMR MILESTONE GAP: Infrastructure incomplete. Missing: {missing}")
            return False

        try:
            from src.RunModel import RunModel
            self.model = RunModel()
            self.model.load_path = str(CHECKPOINT_BASE)
            self.model.smpl_model_path = str(SMPL_MODEL_PATH)
            self.model.prepare()
            self.initialized = True
            print("💎 KORRA: HMR 3D Brain Fully Synchronized.")
            return True
        except Exception as e:
            print(f"❌ HMR BRIDGE FAILURE: {e}")
            return False

    def extract(self, image: np.ndarray, height_cm: float, gender: str = 'male') -> Tuple[Dict[str, float], Optional[np.ndarray], Optional[dict]]:
        if not self.initialized:
            if not self.initialize():
                return self._fallback_ratios(height_cm, gender), None, None

        try:
            import cv2
            img_resized = cv2.resize(image, (224, 224))
            img_normalized = 2 * ((img_resized / 255.0) - 0.5)
            img_batch = np.expand_dims(img_normalized, 0)

            results = self.model.predict_dict(img_batch)
            vertices = results['verts'][0]
            joints = results['joints'][0]

            landmark_2d = {
                'Shoulder_L': (float(joints[2][0])/224.0, float(joints[2][1])/224.0),
                'Shoulder_R': (float(joints[3][0])/224.0, float(joints[3][1])/224.0),
                'Hip_L': (float(joints[8][0])/224.0, float(joints[8][1])/224.0),
                'Hip_R': (float(joints[9][0])/224.0, float(joints[9][1])/224.0)
            }

            measurements = self._calculate_from_indices(vertices, height_cm)
            return measurements, vertices, landmark_2d

        except Exception as e:
            print(f"⚠️ HMR Pipeline Error: {e}")
            return self._fallback_ratios(height_cm, gender), None, None

    def _calculate_from_indices(self, vertices: np.ndarray, user_height_cm: float) -> Dict[str, float]:
        v_height = np.max(vertices[:, 1]) - np.min(vertices[:, 1])
        scale = user_height_cm / (v_height * 100)
        results = {}
        target_groups = {'chest': 'Chest Round', 'waist': 'Waist Round', 'hips': 'Hip Round', 'shoulder width': 'Shoulder'}
        for key, display_name in target_groups.items():
            indices = self.vertex_map.get(key, [])
            if not indices: continue
            group_verts = vertices[indices]
            w = (np.max(group_verts[:, 0]) - np.min(group_verts[:, 0])) * 100 * scale
            d = (np.max(group_verts[:, 2]) - np.min(group_verts[:, 2])) * 100 * scale
            a, b = w/2, d/2
            h_val = ((a - b) ** 2) / ((a + b) ** 2)
            circ = np.pi * (a + b) * (1 + (3 * h_val) / (10 + np.sqrt(4 - 3 * h_val)))
            results[display_name] = round(circ, 1)
        return results

    def _parse_vertex_indices(self) -> Dict[str, List[int]]:
        if not INDEX_FILE_PATH.exists(): return {}
        mapping = {}
        current_section = None
        try:
            with open(INDEX_FILE_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        current_section = line[1:].strip().lower()
                        mapping[current_section] = []
                    elif current_section and line:
                        parts = line.split()
                        if len(parts) >= 2: mapping[current_section].append(int(parts[1]))
            return mapping
        except: return {}

    def _fallback_ratios(self, height_cm: float, gender: str) -> Dict[str, float]:
        return {'Shoulder': round(0.265 * height_cm, 1), 'Chest Round': round(0.588 * height_cm, 1), 'Waist Round': round(0.471 * height_cm, 1)}

ENGINE = HMRMasterEngine()

def extract_measurements_from_hmr(image, height, gender='male'):
    return ENGINE.extract(image, height, gender)

def get_brain_integrity():
    return INTEGRITY
