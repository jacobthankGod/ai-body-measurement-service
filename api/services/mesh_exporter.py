"""
KORRA Mesh Exporter | PHASE 7: OBJ SERIALIZATION
===============================================
Serializes HMR 3D vertices into standard industrial formats (OBJ).
Enables the "Digital Twin" visualization ecosystem.
"""
import os
import numpy as np
from pathlib import Path

class MeshExporter:
    @staticmethod
    def save_to_obj(vertices: np.ndarray, output_path: str):
        """
        Serializes vertices into a Wavefront OBJ file.
        HMR returns ~6890 vertices.
        """
        try:
            # Get faces from the research source (Phase 7 alignment)
            # SMPL has a fixed topology of 13776 faces
            faces_path = Path(__file__).parent / "src" / "tf_smpl" / "smpl_faces.npy"

            if faces_path.exists():
                faces = np.load(faces_path)
            else:
                # Fallback to empty faces if research source is missing
                faces = []

            with open(output_path, 'w') as f:
                f.write("# KORRA Digital Twin | 3D Body Mesh\n")

                # Write Vertices
                for v in vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

                # Write Faces (1-indexed for OBJ)
                for face in faces:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

            return True
        except Exception as e:
            print(f"❌ Mesh Export Failed: {e}")
            return False

    @staticmethod
    def cleanup_cache(file_path: str):
        """Removes temporary mesh files after cloud upload."""
        if os.path.exists(file_path):
            os.remove(file_path)
