"""
HMR-based 3D Body Measurement Extraction | MASTER ARTISAN 1:1 ALIGNMENT
=====================================================================
Strict implementation of the Faraz Bhatti research paper methodology.
Hardened with Atomic Integrity Diagnostics and TF1 Compatibility Bridge.
"""
import os
import sys
import types
import inspect
import pickle
import json
import numpy as np
import logging
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from scipy.spatial import ConvexHull

# --- KORRA DIAGNOSTICS ---
logger = logging.getLogger("KORRA_HMR_EXTRACTION")

# Hardened Package Resolution for AWS EC2 / Docker
SRC_PATH = Path(__file__).parent.resolve() / "src"
if str(SRC_PATH) not in sys.path: sys.path.insert(0, str(SRC_PATH))
if str(SRC_PATH.parent) not in sys.path: sys.path.insert(0, str(SRC_PATH.parent))

# --- NUCLEAR TENSORFLOW LEGACY BRIDGE ---
def setup_tf_bridge():
    """Dynamically sets up TF1 compatibility only when needed."""
    import sys # REDUNDANT IMPORT FOR SCOPE PROTECTION
    try:
        import tensorflow as tf
        import tensorflow.compat.v1 as tf1
        tf1.disable_v2_behavior()

        # Consolidate Environment Patching
        if not hasattr(inspect, 'getargspec'):
            inspect.getargspec = inspect.getfullargspec

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
        return tf1

    except ImportError:
        logger.error("❌ Critical: TensorFlow Infrastructure Offline.")
        return None

# ============================================================================
# MASTER EXTRACTION ENGINE
# ============================================================================

# ============================================================================
# CANONICAL MEASUREMENT CONTRACT (Section 9 Alignment)
# ============================================================================

MALE_KEYS = [
    'Shoulder', 'Neck Round', 'Chest Round', 'Stomach Round', 'Waist Round',
    'Half Length', 'Full Top Length', 'Across Back', 'Across Chest', 'Hip Round',
    'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round', 'Trouser Waist',
    'Trouser Length', 'Inseam', 'Crotch Depth',
    'Sleeve Length', 'Bicep Round', 'Elbow Round', 'Wrist Round',
    # Pattern-drafting dimensions (Phase 16)
    'Across Shoulder', 'Neck to Waist', 'Waist to Hip'
]

FEMALE_KEYS = [
    'Shoulder', 'Neck Round', 'Chest Round', 'Bust Round', 'High Bust', 'Under Bust',
    'Bust Point', 'Shoulder to Bust Point', 'Shoulder to Under Bust',
    'Shoulder to Waist', 'Front Waist Length', 'Back Waist Length',
    'Across Chest', 'Across Back', 'Armhole Round', 'Sleeve Length',
    'Bicep Round', 'Elbow Round', 'Wrist Round', 'Waist Round',
    'Half Length', 'Waist to Hip', 'Upper Hip', 'Hip Round',
    'Thigh Round', 'Knee Round', 'Calf Round', 'Ankle Round',
    # Pattern-drafting dimensions (Phase 16)
    'Across Shoulder', 'Neck to Waist'
]

# ============================================================================
# BODY-PART FACE SEGMENTATION (ported from SMPL-Anthropometry)
# Maps body-part names from Meshcapade segmentation to their SMPL face indices.
# File: src/tf_smpl/smpl_body_parts_2_faces.json
# ============================================================================

# Maps our measurement group names to Meshcapade body-part face groups.
# Limbs use filtered face sets so plane-mesh intersection only captures
# the target body region (avoids spurious torso/arm cross-section).
CIRCUMFERENCE_TO_BODYPARTS = {
    'chest': ['spine1', 'spine2'],
    'waist': ['hips', 'spine'],
    'hips': ['hips'],
    'neck': ['neck'],
    'belly': ['spine', 'spine1'],
    'thigh': ['leftUpLeg', 'rightUpLeg'],
    'ankle': ['leftLeg', 'rightLeg', 'leftFoot', 'rightFoot'],
    # Wrist excluded: T-pose forearm cross-section at wrist Y is artificially
    # thick (muscle belly of forearm). Falls back to bounding-box ellipse.
    'bicep': ['leftArm', 'rightArm'],
    'elbow': ['leftArm', 'rightArm'],
    'calf': ['leftLeg', 'rightLeg'],
    'knee': ['leftLeg', 'rightLeg'],
}

MALE_RATIOS = {
    'Shoulder': 0.265, 'Neck Round': 0.224, 'Chest Round': 0.588, 'Stomach Round': 0.500,
    'Waist Round': 0.471, 'Half Length': 0.353, 'Full Top Length': 0.441, 'Across Back': 0.247,
    'Across Chest': 0.259, 'Hip Round': 0.559, 'Thigh Round': 0.324, 'Knee Round': 0.224,
    'Calf Round': 0.212, 'Ankle Round': 0.153, 'Trouser Waist': 0.482, 'Trouser Length': 0.588,
    'Inseam': 0.459, 'Crotch Depth': 0.165,
    'Sleeve Length': 0.333, 'Bicep Round': 0.180, 'Elbow Round': 0.150, 'Wrist Round': 0.120,
    # Pattern-drafting ratio aliases (Phase 16)
    'Across Shoulder': 0.265, 'Neck to Waist': 0.353, 'Waist to Hip': 0.165,
}

FEMALE_RATIOS = {
    'Shoulder': 0.230, 'Neck Round': 0.206, 'Bust Round': 0.521, 'High Bust': 0.460,
    'Under Bust': 0.412, 'Bust Point': 0.121, 'Shoulder to Bust Point': 0.145,
    'Shoulder to Under Bust': 0.170, 'Shoulder to Waist': 0.230, 'Front Waist Length': 0.218,
    'Back Waist Length': 0.242, 'Across Chest': 0.206, 'Across Back': 0.194,
    'Armhole Round': 0.242, 'Sleeve Length': 0.333, 'Bicep Round': 0.170, 'Elbow Round': 0.145,
    'Wrist Round': 0.109, 'Waist Round': 0.400, 'Half Length': 0.315, 'Waist to Hip': 0.109,
    'Upper Hip': 0.521, 'Hip Round': 0.570, 'Thigh Round': 0.315, 'Knee Round': 0.206,
    'Calf Round': 0.194, 'Ankle Round': 0.133,
    # Pattern-drafting ratio aliases (Phase 16)
    'Across Shoulder': 0.230, 'Neck to Waist': 0.315,
}

class HMRMasterEngine:
    def __init__(self):
        self.base_dir = Path(__file__).parent.resolve() # api/services
        self.project_root = self.base_dir.parent.parent
        self.vertex_map = {}
        self.smpl_faces = None
        self._v_template = None
        self._shapedirs = None
        self._shapedirs_10 = None  # 10-PC shapedirs for HMR basis projection
        self._num_betas = 10       # number of shape components loaded
        self._face_segmentation = None  # body-part → face indices from Meshcapade
        self.last_error = None
        self._shape_prior_gmm = None
        self._shape_scaler = None
        self._load_vertex_map()
        self._load_smpl_faces()
        self._load_face_segmentation()
        self._load_smpl_template()
        self._load_shape_prior()

    def _load_vertex_map(self):
        root = self.base_dir.parent.parent
        vertex_path = root / "data" / "customBodyPoints.txt"
        self.vertex_map = self._parse_vertex_indices(vertex_path)

    def _load_smpl_faces(self):
        faces_path = self.base_dir / "src" / "tf_smpl" / "smpl_faces.npy"
        try:
            self.smpl_faces = np.load(str(faces_path)).astype(np.int32)
        except Exception as e:
            logger.warning(f"Could not load SMPL faces: {e}")
            self.smpl_faces = None

    def _load_face_segmentation(self):
        """Load Meshcapade body-part face segmentation.
        Maps each body part (e.g. 'leftUpLeg', 'rightArm') to a list of
        face indices belonging to that body region.
        """
        seg_path = self.base_dir / "src" / "tf_smpl" / "smpl_body_parts_2_faces.json"
        try:
            import json
            with open(str(seg_path)) as f:
                self._face_segmentation = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load face segmentation: {e}")
            self._face_segmentation = None

    def _get_body_part_faces(self, group_name: str,
                              vertices: Optional[np.ndarray] = None,
                              group_indices: Optional[List[int]] = None) -> Optional[np.ndarray]:
        """Get boolean mask of faces belonging to a given measurement group's body parts.
        If the vertex group is off-center (mean |X| > 0.01), only body parts
        whose faces are on the same side are used — preventing the opposite
        arm/leg from being intersected at the same Y height.

        Returns None if no filtering is needed or segmentation unavailable.
        """
        if self._face_segmentation is None or self.smpl_faces is None:
            return None
        body_parts = CIRCUMFERENCE_TO_BODYPARTS.get(group_name)
        if body_parts is None:
            return None

        face_indices = set()
        for bp in body_parts:
            face_indices.update(self._face_segmentation.get(bp, []))

        if not face_indices:
            return None

        # For limb measurements (off-center vertex group), keep only faces
        # whose center X has the same sign as the vertex group mean X.
        # This handles the case where left/right labels in the segmentation
        # may not align with the actual X sign of our vertex groups.
        if vertices is not None and group_indices and len(group_indices) > 0:
            vg_mean_x = np.mean(vertices[group_indices, 0])
            if abs(vg_mean_x) > 0.01:
                face_list = np.array(list(face_indices), dtype=np.int32)
                face_verts = self.smpl_faces[face_list]
                face_mean_x = vertices[face_verts].mean(axis=1)[:, 0]
                same_side = np.sign(face_mean_x) == np.sign(vg_mean_x)
                mask = np.zeros(len(self.smpl_faces), dtype=bool)
                mask[face_list[same_side]] = True
                return mask

        mask = np.zeros(len(self.smpl_faces), dtype=bool)
        mask[list(face_indices)] = True
        return mask

    def _load_smpl_template(self):
        """Load SMPL template + shapedirs for T-pose measurement extraction.
        Prefers 300-PC model (v1.1.0), falls back to 10-PC model.
        """
        v300_path = self.project_root / "models" / "v_template_300.npy"
        sd300_path = self.project_root / "models" / "shapedirs_300.npy"
        v10_path = self.project_root / "models" / "v_template.npy"
        sd10_path = self.project_root / "models" / "shapedirs.npy"

        # Try 300-PC model first
        if v300_path.exists() and sd300_path.exists():
            try:
                self._v_template = np.load(str(v300_path))
                self._shapedirs = np.load(str(sd300_path))
                self._num_betas = self._shapedirs.shape[1]
                logger.info(f"Loaded 300-PC SMPL template: v={self._v_template.shape}, sd={self._shapedirs.shape}")
                # Also load 10-PC shapedirs for HMR-basis projection
                if sd10_path.exists():
                    self._shapedirs_10 = np.load(str(sd10_path))
                    logger.info(f"Loaded 10-PC shapedirs for projection: {self._shapedirs_10.shape}")
                return
            except Exception as e:
                logger.warning(f"Could not load 300-PC template: {e}")

        # Fall back to 10-PC model
        if v10_path.exists() and sd10_path.exists():
            try:
                self._v_template = np.load(str(v10_path))
                self._shapedirs = np.load(str(sd10_path))
                self._num_betas = self._shapedirs.shape[1]
                logger.info(f"Loaded 10-PC SMPL template: {self._v_template.shape}, {self._shapedirs.shape}")
                return
            except Exception as e:
                logger.warning(f"Could not load 10-PC template: {e}")

        import pickle
        pkl_path = self.project_root / "models" / "neutral_smpl_with_cocoplus_reg.pkl"
        try:
            with open(str(pkl_path), 'rb') as f:
                dd = pickle.load(f, encoding='latin-1')
            t = dd['v_template']
            if hasattr(t, 'r'):
                t = np.array(t)
            self._v_template = np.array(t).reshape(6890, 3)
            sd = dd['shapedirs']
            if hasattr(sd, 'r'):
                sd = np.array(sd)
            nc = sd.shape[-1]
            self._shapedirs = np.array(sd).reshape(6890 * 3, nc)
            self._num_betas = nc
        except Exception as e:
            logger.warning(f"Could not load SMPL template: {e}")
            self._v_template = None
            self._shapedirs = None

    def _load_shape_prior(self):
        """Load trained GMM shape prior and scaler from api/models/priors/."""
        prior_dir = self.base_dir / "models" / "priors"
        gmm_path = prior_dir / "shape_prior_gmm.pkl"
        scaler_path = prior_dir / "shape_scaler.pkl"
        try:
            if gmm_path.exists() and scaler_path.exists():
                with open(gmm_path, 'rb') as f:
                    self._shape_prior_gmm = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self._shape_scaler = pickle.load(f)
                logger.info(f"Shape prior loaded: {self._shape_prior_gmm.n_components} components")
            else:
                logger.info("No shape prior found — inference will run without correction")
        except Exception as e:
            logger.warning(f"Could not load shape prior: {e}")
            self._shape_prior_gmm = None
            self._shape_scaler = None

    def _apply_shape_prior(self, shapes: np.ndarray) -> np.ndarray:
        """Apply GMM shape prior to correct implausible shapes.
        Returns corrected shape vector (10,). If the shape is plausible
        (log-likelihood above 5th-percentile threshold), returns unchanged.
        Otherwise shrinks toward the nearest cluster mean.
        """
        if self._shape_prior_gmm is None or self._shape_scaler is None:
            return shapes
        shapes_std = self._shape_scaler.transform(shapes.reshape(1, -1))[0]
        logprob = self._shape_prior_gmm.score_samples(shapes_std.reshape(1, -1))[0]
        threshold = np.percentile(self._shape_prior_gmm.score_samples(
            self._shape_scaler.transform(
                self._shape_prior_gmm.means_ * 0
            )), 5) if self._shape_prior_gmm.means_.shape[0] > 0 else -10
        if logprob >= threshold:
            return shapes
        probs = self._shape_prior_gmm.predict_proba(shapes_std.reshape(1, -1))
        best_cluster = np.argmax(probs)
        cluster_mean_std = self._shape_prior_gmm.means_[best_cluster]
        cluster_mean_orig = self._shape_scaler.inverse_transform(cluster_mean_std.reshape(1, -1))[0]
        alpha = min(1.0, max(0.3, np.exp(logprob - threshold)))
        corrected = (1 - alpha) * cluster_mean_orig + alpha * shapes
        logger.info(f"Shape prior correction applied: logprob={logprob:.2f}, threshold={threshold:.2f}, alpha={alpha:.2f}")
        return corrected

    def _project_to_300_pc(self, betas_10: np.ndarray) -> np.ndarray:
        """Project HMR's 10-dim betas into the 300-PC basis via least-squares.
        Reconstructs HMR's intended shaped mesh in 10-PC space, then finds
        the 300-PC coefficients that best reproduce it (lossless for in-span meshes).
        """
        if self._shapedirs_10 is None or self._num_betas != 300:
            return np.pad(betas_10, (0, 290))
        delta = self._shapedirs_10 @ betas_10
        betas_300, _, _, _ = np.linalg.lstsq(self._shapedirs, delta, rcond=None)
        return betas_300

    def extract(self, image: np.ndarray, height_cm: float, gender: str = 'male', side_image: Optional[np.ndarray] = None) -> Tuple[Dict[str, float], Optional[np.ndarray], Optional[dict], str, str, Optional[str], Optional[np.ndarray], Optional[dict], Optional[list]]:
        """
        High-Precision Extraction with ABSOLUTE MEMORY ISOLATION.
        Uses a dedicated TF Graph and Session per request to prevent leaks.
        """
        import gc
        tf1 = setup_tf_bridge()
        if not tf1:
            return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", "TensorFlow not found", None, None, None

        model = None
        try:
            # 1. PRE-FLIGHT NUMPY PATCHING
            if not hasattr(np, 'bool'):
                np.bool = bool; np.int = int; np.float = float; np.complex = complex; np.object = object; np.str = str; np.unicode = str

            # 2. ISOLATED GRAPH CONTEXT
            # This is critical for Render 512MB: prevent global graph bloat.
            with tf1.Graph().as_default() as graph:
                config = tf1.ConfigProto()
                config.gpu_options.allow_growth = True
                config.intra_op_parallelism_threads = 1
                config.inter_op_parallelism_threads = 1

                with tf1.Session(config=config, graph=graph) as sess:
                    # 3. TRANSIENT MODEL INSTANTIATION
                    from src.RunModel import RunModel
                    logger.info("📦 HMR: Loading isolated AI brain...")
                    model = RunModel(sess=sess)
                    model.prepare()

                    # 4. PREPROCESSING (Aggressive downscaling)
                    import cv2
                    h, w = image.shape[:2]
                    if max(h, w) > 800:
                        scale_f = 800 / max(h, w)
                        image = cv2.resize(image, (int(w * scale_f), int(h * scale_f)))

                    img_resized = cv2.resize(image, (224, 224))
                    del image

                    img_normalized = 2 * ((img_resized / 255.0) - 0.5)
                    img_batch = np.expand_dims(img_normalized, 0)
                    del img_resized

                    # 5. SIDE IMAGE PROCESSING (If available)
                    side_results = None
                    if side_image is not None:
                        logger.info("🧠 HMR: Processing side profile for depth refinement...")
                        s_h, s_w = side_image.shape[:2]
                        if max(s_h, s_w) > 800:
                            s_scale = 800 / max(s_h, s_w)
                            side_image = cv2.resize(side_image, (int(s_w * s_scale), int(s_h * s_scale)))

                        side_resized = cv2.resize(side_image, (224, 224))
                        side_norm = 2 * ((side_resized / 255.0) - 0.5)
                        side_batch = np.expand_dims(side_norm, 0)
                        side_results = model.predict_dict(side_batch)
                        del side_resized, side_norm

                    # 6. INFERENCE
                    logger.info("🧠 HMR: Executing isolated 3D inference...")
                    results = model.predict_dict(img_batch)
                    vertices = results['verts'][0]
                    joints = results['joints'][0]

                    # INTERLEAVE: Extract raw SMPL params before any post-processing
                    # These are needed for the self-improving accuracy system (Phase 0).
                    # Preserve theta (camera/pose/shape) and 3D joints for dataset building.
                    smpl_params = None
                    joints3d = None
                    if 'theta' not in results:
                        logger.warning("SMPL param extraction skipped: 'theta' key missing from model output")
                    else:
                        try:
                            theta_full = results['theta'][0]
                            camera_params = theta_full[0:3].tolist()   # scale, tx, ty
                            pose_params = theta_full[3:75].tolist()     # 24 joints × 3 axis-angle
                            shape_params = theta_full[75:85].tolist()   # 10 PCA shape coefficients
                            smpl_params = {'camera': camera_params, 'pose': pose_params, 'shape': shape_params}
                            joints3d = results['joints'][0].tolist()    # 19 joints × 3 coordinates
                        except Exception as e:
                            logger.warning(f"SMPL param extraction failed: {e}")

                    # 7. MULTI-VIEW DEPTH REFINEMENT (Advanced)
                    # Instead of averaging vertices (which ruins the pose),
                    # we use the width from the side image to refine the depth (Z) of the front mesh.
                    if side_results is not None:
                        logger.info("💎 HMR: Performing perspective-aware depth refinement...")
                        side_verts = side_results['verts'][0]

                        # Calculate front-view depth (Z-axis span) and side-view width (X-axis span)
                        # We use the torso region for scaling factor
                        torso_indices = self.vertex_map.get('waist', []) + self.vertex_map.get('chest', [])
                        if torso_indices:
                            front_depth = np.max(vertices[torso_indices, 2]) - np.min(vertices[torso_indices, 2])
                            side_width = np.max(side_verts[torso_indices, 0]) - np.min(side_verts[torso_indices, 0])

                            if front_depth > 0 and side_width > 0:
                                depth_scale = side_width / front_depth
                                # Dampen the scale to avoid extreme distortions
                                depth_scale = 1.0 + (depth_scale - 1.0) * 0.7
                                vertices[:, 2] *= depth_scale
                                logger.info(f"💎 HMR: Multi-view depth calibration: {depth_scale:.2f}x")

                        # We still prefer the front-view pose (joints) for landmarks
                        logger.info("💎 HMR: Perspective calibration complete.")

                    # 8. POST-PROCESSING
                    def norm_hmr(val): return float((val + 1.0) / 2.0)
                    landmark_2d = {
                        'Shoulder_L': (norm_hmr(joints[8][0]), norm_hmr(joints[8][1])),
                        'Shoulder_R': (norm_hmr(joints[9][0]), norm_hmr(joints[9][1])),
                        'Hip_L': (norm_hmr(joints[2][0]), norm_hmr(joints[2][1])),
                        'Hip_R': (norm_hmr(joints[3][0]), norm_hmr(joints[3][1])),
                        'Nose': (norm_hmr(joints[14][0]), norm_hmr(joints[14][1]))
                    }

                    # Measurements from T-pose mesh (shape-only, no pose deformation)
                    # This avoids vertex-group drift caused by pose (e.g., belly verts
                    # moving to a different Y level in a non-T-pose pose).
                    # Uses pre-extracted smpl_params from above (Phase 0.1).
                    # Shape prior correction: shrink implausible shapes toward GMM prior
                    # (Phase 3 — Shape Prior Learning).
                    v_measure = vertices
                    if self._v_template is not None and self._shapedirs is not None and smpl_params is not None:
                        try:
                            shapes = np.array(smpl_params['shape'], dtype=np.float64).reshape(10)
                            shapes_corrected = self._apply_shape_prior(shapes)
                            # Project HMR's 10-PC betas into full 300-PC basis
                            if self._num_betas == 300:
                                betas_full = self._project_to_300_pc(shapes_corrected)
                                smpl_params['betas_300'] = betas_full.tolist()
                            else:
                                betas_full = shapes_corrected
                            v_shaped = self._v_template + (self._shapedirs @ betas_full).reshape(-1, 3)
                            v_measure = v_shaped
                            # Phase 119: Tag shape prior diagnostics into smpl_params
                            if self._shape_prior_gmm is not None and self._shape_scaler is not None:
                                shapes_std = self._shape_scaler.transform(shapes.reshape(1, -1))[0]
                                shape_prior_ll = float(self._shape_prior_gmm.score_samples(shapes_std.reshape(1, -1))[0])
                                shape_anomaly = not np.allclose(shapes, shapes_corrected, atol=1e-6)
                                smpl_params['shape_prior_ll'] = shape_prior_ll
                                smpl_params['shape_anomaly'] = shape_anomaly
                        except Exception as e:
                            logger.warning(f"T-pose measurement failed, falling back to posed mesh: {e}")

                    measurements_3d = self._calculate_from_indices(v_measure, height_cm, gender)
                    final_measurements = {key: measurements_3d.get(key, 0.0) for key in (MALE_KEYS if gender == 'male' else FEMALE_KEYS)}

                    v_min, v_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
                    scale_to_meters = (height_cm / 100.0) / (v_max - v_min)
                    vertices_scaled = vertices * scale_to_meters

                    # 9. INTELLIGENCE CONCLUSIONS (Standard Placeholders)
                    body_shape = "Standard"
                    # Simple heuristic for body shape if side view helped
                    if side_results:
                        # compare chest/waist ratios from 3D model
                        m_tmp = self._calculate_from_indices(v_measure, height_cm, gender)
                        c_w = m_tmp.get('Chest Round', 0) / (m_tmp.get('Waist Round', 1) or 1)
                        if gender == 'female':
                            if c_w > 1.2: body_shape = "Hourglass"
                            elif c_w < 1.05: body_shape = "Rectangle"
                        else:
                            if c_w > 1.3: body_shape = "Inverted Triangle"
                            elif c_w < 1.1: body_shape = "Oval"

                    size_rec = "M"
                    if measurements_3d.get('Chest Round', 0) > 110: size_rec = "XL"
                    elif measurements_3d.get('Chest Round', 0) < 90: size_rec = "S"

                    # Clear session before exit
                    sess.close()

                    return final_measurements, vertices_scaled, landmark_2d, body_shape, size_rec, None, v_measure, smpl_params, joints3d

        except Exception as e:
            logger.error(f"❌ HMR ISOLATED CRASH: {e}")
            traceback.print_exc()
            return self._fallback_ratios(height_cm, gender), None, None, "Standard", "M", str(e), None, None, None
        finally:
            # 8. NUCLEAR MEMORY PURGE
            logger.info("♻️ HMR: Purging isolated brain and cleaning RAM...")
            if 'model' in locals(): del model
            if 'sess' in locals(): del sess
            if 'graph' in locals(): del graph
            gc.collect()

    def _mesh_plane_intersection(self, vertices: np.ndarray, faces: np.ndarray,
                                  plane_origin: np.ndarray, plane_normal: np.ndarray) -> np.ndarray:
        """
        Compute the intersection of a mesh with a cutting plane.
        Returns (N, 3) array of intersection points forming the cross-section curve.
        """
        v_shifted = vertices - plane_origin
        signed_dist = np.dot(v_shifted, plane_normal)
        f_dist = signed_dist[faces]

        all_points = []
        for e0, e1 in [(0, 1), (1, 2), (2, 0)]:
            d0 = f_dist[:, e0]
            d1 = f_dist[:, e1]
            crossing = (d0 * d1) < 0
            if np.any(crossing):
                t = d0[crossing] / (d0[crossing] - d1[crossing])
                v0 = vertices[faces[crossing, e0]]
                v1 = vertices[faces[crossing, e1]]
                pts = v0 + t[:, np.newaxis] * (v1 - v0)
                all_points.append(pts)

        if not all_points:
            return np.array([])
        return np.vstack(all_points)

    def _calc_circ_from_mesh_slice(self, vertices: np.ndarray, faces: np.ndarray,
                                    group_indices: List[int], scale: float,
                                    normal=(0, 1, 0),
                                    face_mask: Optional[np.ndarray] = None) -> float:
        """
        Calculate circumference by slicing the mesh with a cutting plane,
        then computing the convex hull perimeter of the intersection.
        If face_mask is provided (bool array), only those faces are used,
        enabling body-part-specific limb measurements.

        For bilateral body parts (e.g. arms, legs), if the intersection
        points form two separate clusters (left and right), it computes
        perimeters independently and sums them — avoiding an inflated
        hull that wraps around both clusters.
        """
        if not group_indices or faces is None:
            return 0.0

        if face_mask is not None:
            faces = faces[face_mask]
            if len(faces) == 0:
                return 0.0

        normal = np.asarray(normal, dtype=np.float64)
        origin = np.mean(vertices[group_indices], axis=0)
        points = self._mesh_plane_intersection(vertices, faces, origin, normal)

        if len(points) < 3:
            return 0.0

        # Deduplicate within rounding tolerance
        points = np.round(points, decimals=6)
        points = np.unique(points, axis=0)
        if len(points) < 3:
            return 0.0

        # Check for bilateral clusters (left + right body parts at same Y).
        # If points are widely separated in X, split at the largest gap.
        xs = points[:, 0]
        x_range = xs.max() - xs.min()
        if x_range > 0.15 and len(points) >= 6:
            sorted_xs = np.sort(xs)
            gaps = sorted_xs[1:] - sorted_xs[:-1]
            max_gap = np.max(gaps)
            if max_gap > 0.08:  # gap > 8cm in SMPL units = likely bilateral
                gap_idx = np.argmax(gaps)
                split_x = (sorted_xs[gap_idx] + sorted_xs[gap_idx + 1]) / 2
                left_pts = points[xs < split_x]
                right_pts = points[xs >= split_x]

                def _hull_perimeter(pts):
                    if len(pts) < 3:
                        return 0.0
                    if abs(normal[1]) > 0.9:
                        p2d = pts[:, [0, 2]]
                    else:
                        u = np.array([1, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1, 0])
                        u = u - np.dot(u, normal) * normal
                        u /= np.linalg.norm(u)
                        v = np.cross(normal, u)
                        p2d = np.column_stack([np.dot(pts, u), np.dot(pts, v)])
                    return ConvexHull(p2d).area * 100 * scale

                total = _hull_perimeter(left_pts) + _hull_perimeter(right_pts)
                return round(total, 1)

        # Single cluster: project to 2D and compute convex hull
        if abs(normal[1]) > 0.9:
            pts_2d = points[:, [0, 2]]
        else:
            u = np.array([1, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1, 0])
            u = u - np.dot(u, normal) * normal
            u /= np.linalg.norm(u)
            v = np.cross(normal, u)
            pts_2d = np.column_stack([np.dot(points, u), np.dot(points, v)])

        hull = ConvexHull(pts_2d)
        return round(hull.area * 100 * scale, 1)

    def _calculate_from_indices(self, vertices: np.ndarray, user_height_cm: float, gender: str) -> Dict[str, float]:
        # Calculated scaled vertices to real-world CM
        v_min, v_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
        v_height = v_max - v_min
        scale = user_height_cm / (v_height * 100) # scale factor for CM

        # Helper to calculate circumference using plane-mesh intersection
        # with body-part face filtering. Falls back to bounding-box ellipse
        # when no body-part-specific face filter is available (e.g. wrist).
        def calc_circ(group_indices, group_name=''):
            if not group_indices: return 0.0
            if self.smpl_faces is not None:
                face_mask = self._get_body_part_faces(group_name, vertices, group_indices)
                if face_mask is not None:
                    return self._calc_circ_from_mesh_slice(
                        vertices, self.smpl_faces, group_indices, scale,
                        face_mask=face_mask)
            # Default/fallback: bounding-box ellipse
            group_verts = vertices[group_indices]
            w = (np.max(group_verts[:, 0]) - np.min(group_verts[:, 0])) * 100 * scale
            d = (np.max(group_verts[:, 2]) - np.min(group_verts[:, 2])) * 100 * scale
            a, b = w/2, d/2
            if (a + b) == 0: return 0.0
            h_val = ((a - b) ** 2) / ((a + b) ** 2)
            circ = np.pi * (a + b) * (1 + (3 * h_val) / (10 + np.sqrt(4 - 3 * h_val)))
            return round(circ, 1)

        # Helper to calculate vertical distance between two groups (y-axis)
        def calc_vert_dist(group1, group2):
            if not group1 or not group2: return 0.0
            y1 = np.mean(vertices[group1][:, 1])
            y2 = np.mean(vertices[group2][:, 1])
            return round(abs(y1 - y2) * 100 * scale, 1)

        results = {}

        # 1. Direct Circumferences from Vertex Map
        results['Chest Round'] = calc_circ(self.vertex_map.get('chest', []), 'chest')
        if gender == 'female': results['Bust Round'] = results['Chest Round']

        results['Waist Round'] = calc_circ(self.vertex_map.get('waist', []), 'waist')
        results['Hip Round'] = calc_circ(self.vertex_map.get('hips', []), 'hips')
        results['Neck Round'] = calc_circ(self.vertex_map.get('neck', []), 'neck')
        results['Stomach Round'] = calc_circ(self.vertex_map.get('belly', []), 'belly')
        results['Thigh Round'] = calc_circ(self.vertex_map.get('thigh', []), 'thigh')
        results['Ankle Round'] = calc_circ(self.vertex_map.get('ankle', []), 'ankle')
        results['Wrist Round'] = calc_circ(self.vertex_map.get('wrist', []), 'wrist')

        # 2. Shoulder Width (Dynamic from mesh)
        sh_indices = self.vertex_map.get('shoulder width', [])
        chest_pts = self.vertex_map.get('chest', [])
        if chest_pts:
            chest_y = np.mean(vertices[chest_pts, 1])
            sh_y = chest_y + 0.015
            band = 0.012
            sh_mask = np.abs(vertices[:, 1] - sh_y) < band
            if np.sum(sh_mask) >= 5:
                sh_width = (vertices[sh_mask, 0].max() - vertices[sh_mask, 0].min()) * 100 * scale
                # Sanity check: shoulder width should be 25-65cm for any human
                if 25 < sh_width < 65:
                    results['Shoulder'] = round(sh_width, 1)
                else:
                    # Fallback to static vertex group
                    sh_indices = self.vertex_map.get('shoulder width', [])
                    if sh_indices:
                        results['Shoulder'] = round((np.max(vertices[sh_indices, 0]) - np.min(vertices[sh_indices, 0])) * 100 * scale, 1)
            else:
                sh_indices = self.vertex_map.get('shoulder width', [])
                if sh_indices:
                    results['Shoulder'] = round((np.max(vertices[sh_indices, 0]) - np.min(vertices[sh_indices, 0])) * 100 * scale, 1)
        else:
            sh_indices = self.vertex_map.get('shoulder width', [])
            if sh_indices:
                results['Shoulder'] = round((np.max(vertices[sh_indices, 0]) - np.min(vertices[sh_indices, 0])) * 100 * scale, 1)

        # 3. Geometric Derivations (Strictly 3D)
        # Lengths derived from vertical distances between mapped landmarks
        neck_pts = self.vertex_map.get('neck', [])
        waist_pts = self.vertex_map.get('waist', [])
        hip_pts = self.vertex_map.get('hips', [])
        ankle_pts = self.vertex_map.get('ankle', [])

        # Common Lengths
        results['Half Length'] = calc_vert_dist(neck_pts, waist_pts)
        results['Full Top Length'] = calc_vert_dist(neck_pts, hip_pts)
        results['Trouser Length'] = calc_vert_dist(waist_pts, ankle_pts)
        results['Inseam'] = round(results['Trouser Length'] * 0.78, 1) # Derived from leg span in 3D
        results['Crotch Depth'] = calc_vert_dist(waist_pts, hip_pts)
        results['Waist to Hip'] = calc_vert_dist(waist_pts, hip_pts) # Pattern drafting dimension

        # Male Specific
        if gender == 'male':
            results['Across Back'] = round(results.get('Shoulder', 0) * 0.92, 1)
            results['Across Chest'] = round(results.get('Shoulder', 0) * 0.96, 1)
            results['Knee Round'] = round(results.get('Thigh Round', 0) * 0.68, 1)
            results['Calf Round'] = round(results.get('Thigh Round', 0) * 0.65, 1)
            results['Trouser Waist'] = results.get('Waist Round', 0)
            results['Bicep Round'] = calc_circ(self.vertex_map.get('bicep', []), 'bicep')
            results['Elbow Round'] = calc_circ(self.vertex_map.get('elbow', []), 'elbow')
            results['Sleeve Length'] = calc_vert_dist(sh_indices, self.vertex_map.get('wrist', []))

        # Female Specific
        else:
            results['High Bust'] = round(results.get('Bust Round', 0) * 0.85, 1)
            results['Under Bust'] = round(results.get('Bust Round', 0) * 0.75, 1)
            results['Shoulder to Waist'] = results['Half Length']
            results['Front Waist Length'] = results['Half Length']
            results['Back Waist Length'] = results['Half Length']
            results['Waist to Hip'] = calc_vert_dist(waist_pts, hip_pts)
            results['Upper Hip'] = round(results.get('Hip Round', 0) * 0.92, 1)
            results['Armhole Round'] = round(results.get('Shoulder', 0) * 0.45, 1)
            results['Sleeve Length'] = calc_vert_dist(sh_indices, self.vertex_map.get('wrist', []))

        # Pattern-drafting dimension aliases (Phase 16)
        results['Across Shoulder'] = results.get('Shoulder', 0.0)
        results['Neck to Waist'] = results.get('Half Length', 0.0)

        return results

    def compute_freesewing_measurements(self, vertices: np.ndarray,
                                         user_height_cm: float,
                                         gender: str) -> dict:
        """Compute Freesewing measurements directly from SMPL mesh.

        Returns dict with Freesewing canonical keys (mm) — ready for
        the Freesewing pattern design API without further conversion.
        Gender-agnostic: same vertex groups, same face masks for both sexes.
        """
        v_min, v_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
        v_height = v_max - v_min
        scale = user_height_cm / (v_height * 100)

        def _circ(group_indices, group_name=''):
            if not group_indices:
                return 0.0
            if self.smpl_faces is not None:
                face_mask = self._get_body_part_faces(group_name, vertices, group_indices)
                if face_mask is not None:
                    return self._calc_circ_from_mesh_slice(
                        vertices, self.smpl_faces, group_indices, scale,
                        face_mask=face_mask)
            # Bounding-box ellipse fallback (used for wrist)
            gv = vertices[group_indices]
            w = (np.max(gv[:, 0]) - np.min(gv[:, 0])) * 100 * scale
            d = (np.max(gv[:, 2]) - np.min(gv[:, 2])) * 100 * scale
            a, b = w / 2, d / 2
            if (a + b) == 0:
                return 0.0
            h_val = ((a - b) ** 2) / ((a + b) ** 2)
            return round(np.pi * (a + b) * (1 + (3 * h_val) / (10 + np.sqrt(4 - 3 * h_val))), 1)

        def _vdist(group1, group2):
            if not group1 or not group2:
                return 0.0
            y1 = np.mean(vertices[group1][:, 1])
            y2 = np.mean(vertices[group2][:, 1])
            return round(abs(y1 - y2) * 100 * scale, 1)

        def _dist3d(group1, group2):
            if not group1 or not group2:
                return 0.0
            c1 = np.mean(vertices[group1], axis=0)
            c2 = np.mean(vertices[group2], axis=0)
            return round(float(np.linalg.norm(c1 - c2)) * 100 * scale, 1)

        # Vertex groups
        chest_v = self.vertex_map.get('chest', [])
        waist_v = self.vertex_map.get('waist', [])
        hip_v = self.vertex_map.get('hips', [])
        neck_v = self.vertex_map.get('neck', [])
        bicep_v = self.vertex_map.get('bicep', [])
        wrist_v = self.vertex_map.get('wrist', [])
        thigh_v = self.vertex_map.get('thigh', [])
        ankle_v = self.vertex_map.get('ankle', [])
        shoulder_v = self.vertex_map.get('shoulder width', [])

        # Shoulder width (dynamic X-span, same as _calculate_from_indices)
        shoulder_cm = 0.0
        chest_pts = self.vertex_map.get('chest', [])
        if chest_pts:
            chest_y = np.mean(vertices[chest_pts, 1])
            sh_y = chest_y + 0.015
            band = 0.012
            sh_mask = np.abs(vertices[:, 1] - sh_y) < band
            if np.sum(sh_mask) >= 5:
                sh_w = (vertices[sh_mask, 0].max() - vertices[sh_mask, 0].min()) * 100 * scale
                if 25 < sh_w < 65:
                    shoulder_cm = round(sh_w, 1)
        if shoulder_cm == 0 and shoulder_v:
            shoulder_cm = round(
                (np.max(vertices[shoulder_v, 0]) - np.min(vertices[shoulder_v, 0])) * 100 * scale, 1)

        # Calf circumference — plane-mesh at mid-shin Y using leftLeg/rightLeg faces
        calf_cm = 0.0
        if self.smpl_faces is not None and self._face_segmentation is not None and thigh_v and ankle_v:
            try:
                calf_faces = set()
                for bp in ['leftLeg', 'rightLeg']:
                    calf_faces.update(self._face_segmentation.get(bp, []))
                if calf_faces:
                    calf_face_verts = self.smpl_faces[list(calf_faces)]
                    calf_all_v = np.unique(calf_face_verts.flatten())
                    # Midpoint Y of lower leg
                    calf_y = np.mean(vertices[calf_all_v, 1])
                    normal = np.array([0, 1, 0], dtype=np.float64)
                    origin = np.array([0, calf_y, 0], dtype=np.float64)
                    calf_mask = np.zeros(len(self.smpl_faces), dtype=bool)
                    calf_mask[list(calf_faces)] = True
                    pts = self._mesh_plane_intersection(vertices, self.smpl_faces[calf_mask],
                                                        origin, normal)
                    if len(pts) >= 3:
                        pts = np.round(pts, decimals=6)
                        pts = np.unique(pts, axis=0)
                        if len(pts) >= 3:
                            xs = pts[:, 0]
                            x_sorted = np.sort(xs)
                            gaps = x_sorted[1:] - x_sorted[:-1]
                            if np.max(gaps) > 0.08:
                                split = np.argmax(gaps) + 1
                                th = (x_sorted[split - 1] + x_sorted[split]) / 2
                                def _hp(p):
                                    if len(p) < 3:
                                        return 0.0
                                    return ConvexHull(p[:, [0, 2]]).area * 100 * scale
                                calf_cm = round(_hp(pts[xs < th]) + _hp(pts[xs >= th]), 1)
                            else:
                                calf_cm = round(ConvexHull(pts[:, [0, 2]]).area * 100 * scale, 1)
            except Exception:
                pass

        # Inseam — hip-to-ankle vertical distance (approximates crotch→ankle)
        inseam_cm = _vdist(hip_v, ankle_v)

        # Build Freesewing dict in cm, then multiply by 10 for mm
        fs = {
            'chest':               _circ(chest_v, 'chest'),
            'waist':               _circ(waist_v, 'waist'),
            'hips':                _circ(hip_v, 'hips'),
            'neckCircumference':   _circ(neck_v, 'neck'),
            'shoulderToShoulder':  shoulder_cm,
            'shoulderToWaist':     _vdist(neck_v, waist_v),
            'waistToHips':         _vdist(waist_v, hip_v),
            'bicepsCircumference': _circ(bicep_v, 'bicep'),
            'wristCircumference':  _circ(wrist_v, 'wrist'),
            'shoulderToWrist':     _dist3d(shoulder_v, wrist_v),
            'inseam':              inseam_cm,
            'thighCircumference':  _circ(thigh_v, 'thigh'),
            'calfCircumference':   calf_cm,
            'waistToHem':          _vdist(neck_v, hip_v),
            'shoulderToHem':       _vdist(neck_v, hip_v),
        }
        return {k: round(v * 10, 1) for k, v in fs.items()}

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
        # Return all measurements using MALE_RATIOS/FEMALE_RATIOS dictionaries
        ratios = MALE_RATIOS if gender == 'male' else FEMALE_RATIOS
        return {key: round(ratio * height_cm, 1) for key, ratio in ratios.items()}

ENGINE = HMRMasterEngine()
HMR_ACTIVE = True

def extract_measurements_from_hmr(image, height, gender='male', side_image=None):
    """Returns (measurements, vertices, landmarks, body_shape, size_rec, error,
    mesh_tpose, smpl_params, joints3d).
    - mesh_tpose: T-pose predicted mesh (6890x3) for PVE analysis, or None on failure.
    - smpl_params: dict with 'camera' (3), 'pose' (72), 'shape' (10) from HMR theta.
    - joints3d: 19x3 SMPL 3D joints list.
    """
    return ENGINE.extract(image, height, gender, side_image=side_image)

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
