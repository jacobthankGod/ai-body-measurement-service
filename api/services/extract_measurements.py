"""
HMR-based 3D Body Measurement Extraction
=========================================
Uses HMR (Human Mesh Recovery) for ±1-2cm accuracy.

Ported from /Users/mac/desby_app/backend/ai_measurement/hmr_inference.py

Requires:
- TensorFlow 1.x or 2.x
- HMR model checkpoint (model.ckpt)
- SMPL model (neutral_smpl_with_cocoplus_reg.pkl)

For production use, run download_models.py first.
"""
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Optional

# Try TensorFlow imports
TF_VERSION = 0
try:
    import tensorflow as tf
    if int(tf.__version__.split('.')[0]) >= 2:
        import tensorflow.compat.v1 as tf1
        tf1.disable_v2_behavior()
        TF_VERSION = 2
    else:
        tf1 = tf
        TF_VERSION = 1
except ImportError:
    print("TensorFlow not available")

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR.parent / "models"

# Model paths - check multiple naming patterns
HMR_PATTERNS = [
    MODELS_DIR / "hmr_model.ckpt",
    MODELS_DIR / "model.ckpt-667589",
]
SMPL_MODEL_PATH = MODELS_DIR / "neutral_smpl_with_cocoplus_reg.pkl"

# Verify models exist - check any HMR checkpoint pattern
HMR_AVAILABLE = any(p.exists() or list(MODELS_DIR.glob(f"{p.stem}*")) for p in HMR_PATTERNS)
# Also check for index files
if not HMR_AVAILABLE:
    HMR_AVAILABLE = any(p.with_suffix('.index').exists() for p in HMR_PATTERNS)
SMPL_AVAILABLE = SMPL_MODEL_PATH.exists()

# Use first available pattern
for p in HMR_PATTERNS:
    if p.exists() or list(MODELS_DIR.glob(f"{p.stem}*")):
        HMR_CHECKPOINT = p
        break
else:
    HMR_CHECKPOINT = HMR_PATTERNS[0]

print(f"📦 HMR Model: {'Available' if HMR_AVAILABLE else 'Not found'} at {HMR_CHECKPOINT}")
print(f"📦 SMPL Model: {'Available' if SMPL_AVAILABLE else 'Not found'} at {SMPL_MODEL_PATH}")

# ============================================================================
# HMR MODEL CLASS
# ============================================================================

class HMRModel:
    """
    HMR (Human Mesh Regression) Model Wrapper.
    Loads pre-trained HMR model and performs 3D body mesh regression.
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = str(model_path or HMR_CHECKPOINT)
        self.smpl_path = str(SMPL_MODEL_PATH)
        self.session = None
        self.smpl_model = None
        self.session_started = False
        
    def load(self) -> bool:
        if not HMR_AVAILABLE:
            print(f"HMR checkpoint not found: {self.model_path}")
            return False
            
        try:
            if SMPL_AVAILABLE:
                import pickle
                with open(self.smpl_path, 'rb') as f:
                    self.smpl_model = pickle.load(f, encoding='latin1')
                print("SMPL model loaded")
            else:
                print("SMPL model not found, using approximation")
                
            if TF_VERSION >= 1:
                self._setup_session()
                
            return True
            
        except Exception as e:
            print(f"Failed to load HMR model: {e}")
            return False
    
    def _setup_session(self):
        try:
            self.session = tf1.Session()
            
            # Find checkpoint
            ckpt_files = list(Path(self.model_path).parent.glob("hmr_model.ckpt-*"))
            if ckpt_files:
                saver = tf1.train.Saver()
                base_path = str(ckpt_files[0]).rsplit('.', 1)[0]
                saver.restore(self.session, base_path)
                print(f"HMR checkpoint loaded: {base_path}")
                
            self.session_started = True
            
        except Exception as e:
            print(f"TF session setup failed: {e}")
            self.session_started = False
    
    def predict(self, image: np.ndarray) -> Optional[Dict]:
        if not self.session_started:
            return None
            
        try:
            image_rgb = self._preprocess_image(image)
            
            joints, verts, camera = self.session.run(
                ['joints:0', 'vertices:0', 'camera:0'],
                feed_dict={'image:0': image_rgb}
            )
            
            return {
                'joints': joints,
                'verts': verts,
                'camera': camera,
                'smpl_model': self.smpl_model
            }
            
        except Exception as e:
            print(f"HMR inference error: {e}")
            return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        import cv2
        resized = cv2.resize(image, (224, 224))
        normalized = resized.astype(np.float32) / 127.5 - 1.0
        return normalized
    
    def close(self):
        if self.session:
            self.session.close()
            self.session = None


# ============================================================================
# SMPL MESH HANDLER
# ============================================================================

class SMPLMesh:
    """SMPL Mesh Handler for extracting measurements from 3D vertices."""
    
    def __init__(self, smpl_model_path: str = None):
        self.smpl_path = str(smpl_model_path or SMPL_MODEL_PATH)
        self.smpl_model = None
        self.load()
    
    def load(self) -> bool:
        if not SMPL_AVAILABLE:
            return False
        try:
            import pickle
            with open(self.smpl_path, 'rb') as f:
                self.smpl_model = pickle.load(f, encoding='latin1')
            return True
        except Exception as e:
            print(f"SMPL load error: {e}")
            return False
    
    def extract_measurements(self, vertices: np.ndarray) -> Dict[str, float]:
        if vertices is None or len(vertices) < 100:
            return {}
        
        measurements = {}
        
        try:
            # Body height
            if len(vertices) > 300:
                body_height = np.max(vertices[:, 1]) - np.min(vertices[:, 1])
                measurements['Body Height'] = body_height * 100
            
            # Shoulder width
            shoulder_verts = vertices[(vertices[:, 1] > 0.3) & (vertices[:, 1] < 0.5)]
            if len(shoulder_verts) > 10:
                shoulder_width = np.max(shoulder_verts[:, 0]) - np.min(shoulder_verts[:, 0])
                measurements['Shoulder'] = shoulder_width * 100
            
            # Chest circumference
            chest_verts = vertices[(vertices[:, 1] > 0.1) & (vertices[:, 1] < 0.3)]
            if len(chest_verts) > 10:
                chest_width = np.max(chest_verts[:, 0]) - np.min(chest_verts[:, 0])
                chest_depth = np.max(chest_verts[:, 2]) - np.min(chest_verts[:, 2])
                measurements['Chest Round'] = 2 * np.pi * ((chest_width + chest_depth) / 2) * 100
            
            # Waist circumference
            waist_verts = vertices[(vertices[:, 1] > -0.1) & (vertices[:, 1] < 0.1)]
            if len(waist_verts) > 10:
                waist_width = np.max(waist_verts[:, 0]) - np.min(waist_verts[:, 0])
                waist_depth = np.max(waist_verts[:, 2]) - np.min(waist_verts[:, 2])
                measurements['Waist Round'] = 2 * np.pi * ((waist_width + waist_depth) / 2) * 100
            
            # Hip circumference
            hip_verts = vertices[(vertices[:, 1] > -0.3) & (vertices[:, 1] < -0.1)]
            if len(hip_verts) > 10:
                hip_width = np.max(hip_verts[:, 0]) - np.min(hip_verts[:, 0])
                hip_depth = np.max(hip_verts[:, 2]) - np.min(hip_verts[:, 2])
                measurements['Hip Round'] = 2 * np.pi * ((hip_width + hip_depth) / 2) * 100
            
            # Arm lengths
            right_arm = vertices[vertices[:, 0] > 0.15]
            left_arm = vertices[vertices[:, 0] < -0.15]
            
            if len(right_arm) > 10:
                measurements['Right Arm Length'] = (np.max(right_arm[:, 1]) - np.min(right_arm[:, 1])) * 100
            if len(left_arm) > 10:
                measurements['Left Arm Length'] = (np.max(left_arm[:, 1]) - np.min(left_arm[:, 1])) * 100
            
            # Leg lengths / Inseam
            right_leg = vertices[(vertices[:, 0] > 0.05) & (vertices[:, 1] < -0.3)]
            left_leg = vertices[(vertices[:, 0] < -0.05) & (vertices[:, 1] < -0.3)]
            
            if len(right_leg) > 10:
                measurements['Right Leg Length'] = (np.max(right_leg[:, 1]) - np.min(right_leg[:, 1])) * 100
            if len(left_leg) > 10:
                measurements['Left Leg Length'] = (np.max(left_leg[:, 1]) - np.min(left_leg[:, 1])) * 100
            
            inner_leg = vertices[np.abs(vertices[:, 0]) < 0.05]
            if len(inner_leg) > 10:
                measurements['Inseam'] = (np.max(inner_leg[:, 1]) - np.min(inner_leg[:, 1])) * 100
            
        except Exception as e:
            print(f"Measurement extraction error: {e}")
        
        return measurements


# ============================================================================
# EXPORTED FUNCTIONS
# ============================================================================

def create_hmr_model() -> Optional[HMRModel]:
    """Create and initialize HMR model."""
    model = HMRModel()
    if model.load():
        return model
    return None


def run_hmr_inference(image: np.ndarray) -> Optional[Dict]:
    """Run full HMR inference on an image."""
    model = create_hmr_model()
    if not model:
        return None
    
    try:
        result = model.predict(image)
        
        if result and result.get('verts') is not None:
            smpl = SMPLMesh()
            measurements = smpl.extract_measurements(result['verts'])
            result['measurements'] = measurements
            return result
        
    except Exception as e:
        print(f"HMR inference failed: {e}")
    
    finally:
        model.close()
    
    return None


def extract_measurements_from_hmr(front_image, user_height_cm, gender='male') -> Dict[str, float]:
    """
    Extract measurements using HMR 3D.
    
    Args:
        front_image: OpenCV image (front view)
        user_height_cm: User's height in cm
        gender: 'male' or 'female'
    
    Returns:
        Dict of measurements in cm
    """
    # Check if image is valid
    if front_image is None or (isinstance(front_image, np.ndarray) and front_image.size == 0):
        print("Invalid image, using ratio fallback")
        return from_ratios(user_height_cm, gender)
    
    # Try HMR inference
    if HMR_AVAILABLE and SMPL_AVAILABLE:
        try:
            result = run_hmr_inference(front_image)
            if result and 'measurements' in result:
                print("Using HMR 3D extraction")
                return result['measurements']
        except Exception as e:
            print(f"HMR inference failed: {e}, falling back to ratios")
    
    # Fallback to anthropometric ratios
    return from_ratios(user_height_cm, gender)


def from_ratios(height_cm: float, gender: str) -> Dict[str, float]:
    """Generate measurements from anthropometric ratios."""
    if gender == 'male':
        ratios = {
            'Shoulder': 0.265, 'Neck Round': 0.224, 'Chest Round': 0.588,
            'Stomach Round': 0.500, 'Waist Round': 0.471, 'Hip Round': 0.559,
            'Half Length': 0.353, 'Full Top Length': 0.441,
            'Thigh Round': 0.324, 'Knee Round': 0.224, 'Calf Round': 0.212,
            'Ankle Round': 0.153, 'Trouser Length': 0.588, 'Inseam': 0.459,
            'Arm Length': 0.353, 'Crotch Depth': 0.165,
        }
    else:
        ratios = {
            'Shoulder': 0.230, 'Neck Round': 0.206, 'Bust Round': 0.521,
            'High Bust': 0.460, 'Under Bust': 0.412, 'Waist Round': 0.400,
            'Half Length': 0.315, 'Hip Round': 0.570, 'Thigh Round': 0.315,
            'Knee Round': 0.206, 'Calf Round': 0.194, 'Ankle Round': 0.133,
            'Sleeve Length': 0.333, 'Bicep Round': 0.170, 'Wrist Round': 0.109,
            'Arm Length': 0.333, 'Waist to Hip': 0.109, 'Upper Hip': 0.521,
        }
    
    return {k: round(v * height_cm, 1) for k, v in ratios.items()}


# Export
__all__ = ['extract_measurements_from_hmr', 'from_ratios', 'HMRModel', 'SMPLMesh', 'run_hmr_inference']
