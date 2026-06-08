"""
HMR-based 3D Body Measurement Extraction | MASTER ARTISAN 1:1 ALIGNMENT
=====================================================================
Strict implementation of the Faraz Bhatti research paper methodology.
Hardened with Atomic Integrity Diagnostics and TF1 Compatibility Bridge.
"""
import os
import sys
import types
import numpy as np
import logging
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger("KORRA_HMR")

# --- NUCLEAR TENSORFLOW LEGACY BRIDGE ---
try:
    import tensorflow as tf
    import tensorflow.compat.v1 as tf1
    tf1.disable_v2_behavior()

    def create_mock_module(name):
        msg = types.ModuleType(name)
        sys.modules[name] = msg
        return msg

    # SATISFY TF-SLIM / TF-KERAS DRIFT
    tk = create_mock_module('tf_keras')
    sys.modules['tf_keras.legacy_tf_layers'] = tf1.layers
    sys.modules['tf_keras.legacy_tf_layers.normalization'] = tf1.layers
    sys.modules['tf_keras.legacy_tf_layers.convolutional'] = tf1.layers
    sys.modules['tf_keras.legacy_tf_layers.pooling'] = tf1.layers
    sys.modules['tf_keras.legacy_tf_layers.core'] = tf1.layers

    contrib = create_mock_module('tensorflow.contrib')

    try:
        import tf_slim
        if not hasattr(tf_slim.stack, '_slim_arg_scope'):
            tf_slim.stack = tf_slim.add_arg_scope(tf_slim.stack)
        contrib.slim = tf_slim
        sys.modules['tensorflow.contrib.slim'] = tf_slim

        create_mock_module('tensorflow.contrib.slim.python')
        create_mock_module('tensorflow.contrib.slim.python.slim')
        create_mock_module('tensorflow.contrib.slim.python.slim.nets')
    except: pass

    layers = create_mock_module('tensorflow.contrib.layers')
    initializers = create_mock_module('tensorflow.contrib.layers.python.layers.initializers')
    from tensorflow.python.ops import init_ops
    initializers.variance_scaling_initializer = init_ops.variance_scaling_initializer
    contrib.layers = layers

    framework = create_mock_module('tensorflow.contrib.framework')
    def _get_vars(scope=None, suffix=None, collection=tf1.GraphKeys.GLOBAL_VARIABLES):
        return tf1.get_collection(collection, scope=scope)
    framework.get_variables = _get_vars
    contrib.framework = framework

    tf1.contrib = contrib
    sys.modules['tensorflow'] = tf1
    tf = tf1

except ImportError:
    logger.error("❌ Critical: TensorFlow Infrastructure Offline.")

# ============================================================================
# MASTER EXTRACTION ENGINE
# ============================================================================

class HMRMasterEngine:
    def __init__(self):
        self.model = None
        self.initialized = False
        self.base_dir = Path(__file__).parent.resolve() # api/services
        self.vertex_map = {}
        self.last_error = None

    def initialize(self):
        """Absolute Handshake for AI Brain Initialization."""
        try:
            root = self.base_dir.parent.parent
            models_dir = root / "models"
            ckpt_base = models_dir / "model.ckpt-667589"
            vertex_path = root / "data" / "customBodyPoints.txt"

            # Use string concatenation to avoid Path.with_suffix bug with dots in filename
            if not Path(str(ckpt_base) + ".index").exists():
                self.last_error = f"Weights missing at {ckpt_base}"
                return False

            # SATISFY NUMPY DEPRECATIONS
            if not hasattr(np, 'bool'):
                np.bool = bool; np.int = int; np.float = float; np.complex = complex; np.object = object; np.str = str; np.unicode = str

            # PACKAGE RESOLUTION HARDENING
            src_path = self.base_dir / "src"
            if str(src_path) not in sys.path: sys.path.insert(0, str(src_path))
            if str(self.base_dir) not in sys.path: sys.path.insert(0, str(self.base_dir))

            from src import resnet_v2
            sys.modules['tensorflow.contrib.slim.python.slim.nets.resnet_v2'] = resnet_v2

            from src.RunModel import RunModel
            logger.info("📦 HMR: Instantiating RunModel...")
            self.model = RunModel()

            logger.info("📦 HMR: Loading Checkpoint Weights...")
            self.model.prepare()

            self.vertex_map = self._parse_vertex_indices(vertex_path)
            self.initialized = True
            logger.info("✅ KORRA: HMR 3D Brain Fully Synchronized.")
            return True
        except Exception as e:
            self.last_error = f"INIT_CRASH: {str(e)}"
            logger.error(f"❌ HMR INITIALIZATION CRASH: {e}")
            traceback.print_exc()
            return False

    def extract(self, image: np.ndarray, height_cm: float, gender: str = 'male') -> Tuple[Dict[str, float], Optional[np.ndarray], Optional[dict], Optional[str]]:
        if not self.initialized:
            if not self.initialize():
                return self._fallback_ratios(height_cm, gender), None, None, f"Initialization Failed: {self.last_error}"
        try:
            import cv2
            h, w = image.shape[:2]
            if max(h, w) > 1024:
                scale_f = 1024 / max(h, w)
                image = cv2.resize(image, (int(w * scale_f), int(h * scale_f)))

            img_resized = cv2.resize(image, (224, 224))
            img_normalized = 2 * ((img_resized / 255.0) - 0.5)
            img_batch = np.expand_dims(img_normalized, 0)

            results = self.model.predict_dict(img_batch)
            vertices = results['verts'][0]
            joints = results['joints'][0]

            landmark_2d = {
                'Shoulder_L': (float(joints[2][0])/224.0, float(joints[2][1])/224.0),
                'Shoulder_R': (float(joints[3][0])/224.0, float(joints[3][1])/224.0)
            }
            measurements = self._calculate_from_indices(vertices, height_cm)

            # Clinical Scaling
            v_min, v_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
            v_height = v_max - v_min
            scale_to_meters = (height_cm / 100.0) / v_height
            vertices_scaled = vertices * scale_to_meters

            return measurements, vertices_scaled, landmark_2d, None
        except Exception as e:
            err_msg = f"RUNTIME_CRASH: {str(e)}"
            logger.error(f"⚠️ HMR Pipeline Error: {e}")
            traceback.print_exc()
            return self._fallback_ratios(height_cm, gender), None, None, err_msg

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

    def _parse_vertex_indices(self, path) -> Dict[str, List[int]]:
        mapping = {}
        if not os.path.exists(path): return mapping
        current_section = None
        try:
            with open(path, 'r') as f:
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
HMR_ACTIVE = True

def extract_measurements_from_hmr(image, height, gender='male'):
    return ENGINE.extract(image, height, gender)

def get_brain_integrity():
    """Returns absolute technical status of AI weights."""
    root = Path(__file__).parent.parent.parent.resolve()
    m_dir = root / "models"
    status = {
        "hmr_weights": (m_dir / "model.ckpt-667589.index").exists(),
        "smpl_model": (m_dir / "neutral_smpl_with_cocoplus_reg.pkl").exists(),
        "vertex_map": (root / "data" / "customBodyPoints.txt").exists()
    }
    return status
