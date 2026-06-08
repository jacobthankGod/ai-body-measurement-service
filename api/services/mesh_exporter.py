"""
KORRA Mesh Exporter | PHASE 7: OBJ SERIALIZATION
===============================================
Serializes HMR 3D vertices into standard industrial formats (OBJ).
Enables the "Digital Twin" visualization ecosystem.
"""
import os
import numpy as np
import logging
import traceback
from pathlib import Path

logger = logging.getLogger("KORRA_EXPORTER")

class MeshExporter:
    @staticmethod
    def save_to_obj(vertices: np.ndarray, output_path: str):
        """
        Serializes vertices into a Wavefront OBJ file.
        HMR returns ~6890 vertices.
        """
        try:
            # FORENSIC FIX: Resolve faces from absolute path independent of import context
            # Try multiple possible paths to ensure robustness
            base_dir = Path(__file__).resolve().parent.parent
            possible_faces_paths = [
                base_dir / "api" / "services" / "src" / "tf_smpl" / "smpl_faces.npy",
                base_dir / "api" / "services" / "tf_smpl" / "smpl_faces.npy",
            ]
            
            faces = []
            faces_path = None
            for candidate in possible_faces_paths:
                if candidate.exists():
                    faces_path = candidate
                    break
            
            if faces_path:
                try:
                    faces = np.load(faces_path)
                    logger.info(f"💎 KORRA: Loaded {len(faces)} SMPL faces from {faces_path}")
                except Exception as load_err:
                    logger.warning(f"⚠️ KORRA: Failed to load faces from {faces_path}: {load_err}. Using vertex-only.")
                    faces = []
            else:
                logger.warning(f"⚠️ KORRA: SMPL faces MISSING. Searching recursively...")
                # Last resort: Search recursively from base
                for root, dirs, files in os.walk(base_dir):
                    if "smpl_faces.npy" in files:
                        faces_path = Path(root) / "smpl_faces.npy"
                        try:
                            faces = np.load(faces_path)
                            logger.info(f"💎 KORRA: Recovered {len(faces)} SMPL faces from {faces_path}")
                            break
                        except: continue
                if not faces_path:
                    logger.warning(f"⚠️ KORRA: SMPL faces NOT FOUND. OBJ will be vertex-only.")
                    faces = []

            with open(output_path, 'w') as f:
                f.write("# KORRA Digital Twin | 3D Body Mesh\n")
                f.write(f"# Vertices: {len(vertices)} | Faces: {len(faces)}\n")

                # Write Vertices
                for v in vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

                # Write Faces (1-indexed for OBJ)
                for face in faces:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

            mesh_size = Path(output_path).stat().st_size
            logger.info(f"💾 KORRA: Mesh persisted to {output_path} ({mesh_size} bytes)")
            return True
        except Exception as e:
            logger.error(f"❌ Mesh Export Failed: {e}")
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def cleanup_cache(file_path: str):
        """Removes temporary mesh files after cloud upload."""
        if os.path.exists(file_path):
            os.remove(file_path)
