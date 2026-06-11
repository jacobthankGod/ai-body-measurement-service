"""
Isolated HMR Subprocess | Memory-Safe AI Extraction
===================================================
Standalone script to perform HMR inference and exit immediately.
Accepts: image_path, height_cm, gender, output_mesh_path
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
if str(SRC_PATH) not in sys.path: sys.path.insert(0, str(SRC_PATH))

# Configure minimal logging to stderr to keep stdout clean for JSON
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("HMR_SUBPROCESS")

def run_hmr(front_path, side_path, height_cm, gender, mesh_path=None):
    import sys # REDUNDANT IMPORT FOR SCOPE PROTECTION
    import gc
    try:
        # Late import of TensorFlow to ensure it only loads in this process
        import tensorflow as tf
        import tensorflow.compat.v1 as tf1
        tf1.disable_v2_behavior()

        # Patching for compatibility
        import types
        import inspect
        if not hasattr(inspect, 'getargspec'):
            inspect.getargspec = inspect.getfullargspec

        # Load images
        img_f = np.array(Image.open(front_path))
        img_s = np.array(Image.open(side_path)) if side_path and os.path.exists(side_path) else None

        # Import extraction engine components
        from api.services.extract_measurements import HMRMasterEngine
        engine = HMRMasterEngine()

        # Perform extraction
        extraction_result = engine.extract(img_f, height_cm, gender, side_image=img_s)

        # Robust Unpacking
        if isinstance(extraction_result, tuple):
            measurements = extraction_result[0]
            vertices = extraction_result[1]
            landmarks = extraction_result[2]
            body_shape = extraction_result[3]
            size_rec = extraction_result[4]
            error = extraction_result[5]
        else:
            # Fallback if something returned a single value (error string or dict)
            return {"status": "failed", "error": f"Invalid engine return type: {type(extraction_result)}"}

        # CLEANUP AGGRESSIVELY
        del img_f
        if img_s is not None: del img_s

        if error:
            return {"status": "failed", "error": error}

        # Export mesh if requested
        mesh_url = None
        if mesh_path and vertices is not None:
            from api.services.mesh_exporter import MeshExporter
            MeshExporter.save_to_obj(vertices, mesh_path)
            mesh_url = mesh_path # Caller will convert to relative URL

        # FINAL CLEANUP
        del vertices
        gc.collect()

        return {
            "status": "completed",
            "measurements": measurements,
            "landmarks": landmarks,
            "body_shape": body_shape,
            "size_recommendation": size_rec,
            "mesh_path": str(mesh_path) if mesh_path else None
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

    # Force single threaded to save memory on Render
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    result = run_hmr(f_path, s_path, height, gender, mesh_out)
    print(json.dumps(result))
