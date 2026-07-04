"""
Isolated Fusion Subprocess | Memory-Safe AI Extraction
======================================================
Standalone script to perform HMR + MediaPipe + ANSUR fusion inference.
Accepts: front_path side_path height_cm gender [output_mesh_path] [--hmr-only]
Outputs: JSON to stdout
"""
import os
import sys
import json
import logging
import traceback
import numpy as np
from pathlib import Path
from PIL import Image

# Setup paths
SRC_PATH = Path(__file__).parent.resolve() / "src"
ROOT_PATH = Path(__file__).parent.parent.parent.resolve()
for p in (ROOT_PATH, SRC_PATH):
    if str(p) not in sys.path: sys.path.insert(0, str(p))

# Configure minimal logging to stderr to keep stdout clean for JSON
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("HMR_SUBPROCESS")

def run_hmr(front_path, side_path, height_cm, gender, mesh_path=None, attire_name=''):
    import sys # REDUNDANT IMPORT FOR SCOPE PROTECTION
    import gc
    try:
        # Late import of TensorFlow to ensure it only loads in this process
        import tensorflow as tf
        import tensorflow.compat.v1 as tf1
        tf1.disable_v2_behavior()

        logger.info(f"TF version: {tf.__version__}")
        logger.info(f"TF GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")

        # Patching for compatibility
        import types
        import inspect
        if not hasattr(inspect, 'getargspec'):
            inspect.getargspec = inspect.getfullargspec

        # Load images
        img_f = np.array(Image.open(front_path))
        img_s = np.array(Image.open(side_path)) if side_path and os.path.exists(side_path) else None

        # Import extraction engine components
        logger.info(f"Loading HMR model...")
        from api.services.extract_measurements import HMRMasterEngine
        engine = HMRMasterEngine()
        logger.info("HMR engine loaded successfully")
        logger.info(f"Images loaded: front={img_f.shape}, side={img_s.shape if img_s is not None else None}")

        # Perform extraction
        extraction_result = engine.extract(img_f, height_cm, gender, side_image=img_s)

        # Robust Unpacking (9-element tuple as of Phase 0, backward-compatible to 7)
        if isinstance(extraction_result, tuple):
            measurements = extraction_result[0]
            vertices = extraction_result[1]
            landmarks = extraction_result[2]
            body_shape = extraction_result[3]
            size_rec = extraction_result[4]
            error = extraction_result[5]
            v_measure_tpose = extraction_result[6] if len(extraction_result) > 6 else None
            smpl_params = extraction_result[7] if len(extraction_result) > 7 else None
            joints3d = extraction_result[8] if len(extraction_result) > 8 else None
        else:
            # Fallback if something returned a single value (error string or dict)
            return {"status": "failed", "error": f"Invalid engine return type: {type(extraction_result)}"}

        # CLEANUP AGGRESSIVELY
        del img_f
        if img_s is not None: del img_s

        if error:
            return {"status": "failed", "error": error}

        # Phase 15: Snapshot raw (pre-calibration) measurements into smpl_params
        if smpl_params is not None and measurements is not None:
            smpl_params['raw_measurements'] = dict(measurements)

        # Export posed mesh if requested
        mesh_url = None
        tpose_mesh_path = None
        if mesh_path and vertices is not None:
            from api.services.mesh_exporter import MeshExporter
            MeshExporter.save_to_obj(vertices, mesh_path)
            mesh_url = mesh_path # Caller will convert to relative URL

            # Export T-pose mesh alongside (Phase 0: self-improving accuracy)
            if v_measure_tpose is not None:
                tpose_path = str(mesh_path).replace('.obj', '_tpose.obj')
                MeshExporter.save_to_obj(v_measure_tpose, tpose_path)
                tpose_mesh_path = tpose_path
                # Sanity check dimensions
                v_range = np.max(v_measure_tpose, axis=0) - np.min(v_measure_tpose, axis=0)
                logger.info(f"T-pose mesh: X={v_range[0]:.3f} Y={v_range[1]:.3f} Z={v_range[2]:.3f}")
                if v_range[1] < 0.5 or v_range[1] > 3.0:
                    logger.warning(f"T-pose height {v_range[1]:.3f}m outside expected [0.5, 3.0]")

        # Compute clinical realism index from measurement consistency
        clinical_realism_index = 97.0
        if measurements:
            chest = measurements.get('Chest Round') or measurements.get('Bust Round', 0)
            waist = measurements.get('Waist Round', 0)
            m_height = measurements.get('Height', height_cm)
            if chest > 0 and waist > 0 and chest <= waist:
                clinical_realism_index -= 5.0
            if m_height < 100 or m_height > 250:
                clinical_realism_index -= 10.0
            if 0 < waist < 50:
                clinical_realism_index -= 5.0
            clinical_realism_index = max(70.0, min(100.0, round(clinical_realism_index, 1)))

        # Try MediaPipe fusion for complementary measurements
        fusion_used = False
        try:
            from api.services.mediapipe_measurement_engine import (
                extract_measurements_from_dual_photos as mp_extract
            )
            front_rgb = np.array(Image.open(front_path))
            side_rgb = np.array(Image.open(side_path)) if side_path and os.path.exists(side_path) else None
            mp_result, _, _ = mp_extract(front_rgb, side_rgb or front_rgb, height_cm, gender)

            if mp_result and mp_result.get('Shoulder', 0) > 0:
                # Supplement HMR with MP measurements not yet in HMR output
                mp_only = {'Across Back', 'Across Chest', 'Knee Round', 'Calf Round',
                           'Trouser Waist', 'Bust Round', 'High Bust', 'Under Bust',
                           'Armhole Round', 'Sleeve Length', 'Bicep Round', 'Elbow Round',
                           'Wrist Round'}
                for k, v in mp_result.items():
                    if k in mp_only and isinstance(v, (int, float)) and v > 0:
                        measurements[k] = v
                logger.info(f"MediaPipe fusion applied: +{len(mp_only & set(mp_result.keys()))} measurements")
                fusion_used = True

            del front_rgb, side_rgb
        except ImportError:
            logger.info("MediaPipe not available — HMR-only mode")
        except Exception as e:
            logger.warning(f"MediaPipe fusion skipped: {e}")

        # Try ANSUR imputation for shape-context refinement
        try:
            from api.services.imputation_service import imputation_service
            refined = imputation_service.fuse_measurements(gender, hmr_measurements=measurements,
                                                           mp_measurements=None,
                                                           user_height_cm=height_cm,
                                                           hmr_confidence=0.85, mp_confidence=0.0)
            if refined:
                # Merge refined values (prefer refined for torso measurements)
                for k in ('Chest Round', 'Waist Round', 'Hip Round', 'Neck Round', 'Shoulder'):
                    if refined.get(k, 0) > 0:
                        measurements[k] = refined[k]
                logger.info(f"ANSUR imputation applied")
        except Exception as e:
            logger.warning(f"ANSUR imputation skipped: {e}")

        # Apply SMPL-to-real-world calibration for core measurements
        try:
            from api.services.measurement_calibration import calibrator
            calibrator.calibrate(measurements, gender)
            logger.info("Measurement calibration applied")
        except Exception as e:
            logger.warning(f"Measurement calibration skipped: {e}")

        # FINAL CLEANUP (safely handle T-pose mesh alias)
        if v_measure_tpose is not None and v_measure_tpose is not vertices:
            del v_measure_tpose
        del vertices
        gc.collect()

        return {
            "status": "completed",
            "measurements": measurements,
            "landmarks": landmarks,
            "body_shape": body_shape,
            "size_recommendation": size_rec,
            "clinical_realism_index": clinical_realism_index,
            "fusion_used": fusion_used,
            "mesh_path": str(mesh_path) if mesh_path else None,
            "smpl_params": smpl_params,
            "joints3d": joints3d,
            "tpose_mesh_path": str(tpose_mesh_path) if tpose_mesh_path else None,
        }

    except Exception as e:
        logger.error(f"SUBPROCESS ERROR: {e}")
        return {"status": "failed", "error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps({"status": "failed", "error": "Missing arguments. Need: front_path side_path height gender [mesh_out]"}))
        sys.exit(1)

    f_path = sys.argv[1]
    s_path = sys.argv[2]
    height = float(sys.argv[3])
    gender = sys.argv[4]
    mesh_out = sys.argv[5] if len(sys.argv) > 5 else None
    attire_name = sys.argv[6] if len(sys.argv) > 6 else ''

    logger.info(f"Subprocess started: front={f_path}, side={s_path}, height={height}, gender={gender}")

    # Force single threaded to save memory on EC2 t3.micro
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    result = run_hmr(f_path, s_path, height, gender, mesh_out, attire_name=attire_name)
    # Phase 14: JSON serialization safety net — fallback for non-serializable types
    try:
        print(json.dumps(result))
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization failed: {e}")
        safe_result = {"status": "failed", "error": f"Serialization error: {e}"}
        print(json.dumps(safe_result))
