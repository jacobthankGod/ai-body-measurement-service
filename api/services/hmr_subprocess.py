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

def run_hmr(image_path, height_cm, gender, mesh_path=None):
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

        # Load image
        img = np.array(Image.open(image_path))

        # Import extraction engine components
        from api.services.extract_measurements import HMRMasterEngine
        engine = HMRMasterEngine()

        # Perform extraction
        measurements, vertices, landmarks, error = engine.extract(img, height_cm, gender)

        # CLEANUP AGGRESSIVELY
        del img

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
            "mesh_path": str(mesh_path) if mesh_path else None
        }

    except Exception as e:
        logger.error(f"SUBPROCESS ERROR: {e}")
        return {"status": "failed", "error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"status": "failed", "error": "Missing arguments"}))
        sys.exit(1)

    img_path = sys.argv[1]
    height = float(sys.argv[2])
    gender = sys.argv[3]
    mesh_out = sys.argv[4] if len(sys.argv) > 4 else None

    # Force single threaded to save memory on Render
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

    result = run_hmr(img_path, height, gender, mesh_out)
    print(json.dumps(result))
