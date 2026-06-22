import numpy as np
import json
import os
from pathlib import Path

class ShapeTransformer:
    """
    KORRA Shape Transformer | Phases 46-60
    Handles the physical deformation of the 3D mesh based on scanned biometrics.
    """
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.partition_path = self.base_dir / "data" / "mesh_partitions.json"
        self.partitions = self._load_partitions()

    def _load_partitions(self):
        if self.partition_path.exists():
            with open(self.partition_path, 'r') as f:
                return json.load(f)
        return {}

    def apply_deformation(self, vertices: np.ndarray, measurements: dict, gender: str = "male"):
        """
        Phase 48: Linear Deformation Logic
        V_new = V_base + M * P
        For Phase 48-50, we implement the grouping logic that scales specific vertex clusters.
        """
        print(f"🧬 Reshaping 3D Mesh... ({len(vertices)} vertices)")
        new_vertices = vertices.copy()

        # Phase 51: Scale Lock (Height only deforms Y-axis)
        height_cm = measurements.get('height', 175)
        # Assuming base mesh is 175cm. Scale factor:
        height_scale = height_cm / 175.0
        new_vertices[:, 1] *= height_scale # Global Y-scaling (simplistic for Phase 51)

        # Phase 49: Batch Processing (Iterate through vertex groups)
        # Mapping Parameters to Partitions
        mapping = {
            'chestcircumference': 'chest',
            'waistcircumference': 'waist',
            'buttockcircumference': 'legs' # Using legs for hip/buttock volume
        }

        for param, group_name in mapping.items():
            if param in measurements and group_name in self.partitions:
                indices = self.partitions[group_name]
                # Calculate volume expansion factor based on ANSUR II mean
                # (Simplistic logic for Phase 48-50 validation)
                val = measurements[param]
                # Scale XZ plane for horizontal girth expansion
                # Phase 52: Volume Guard (preventing < 0.5 or > 2.0 scaling)
                scale_factor = np.clip(val / 90.0, 0.5, 2.0)

                new_vertices[indices, 0] *= scale_factor # X expansion
                new_vertices[indices, 2] *= scale_factor # Z expansion

        # Phase 50: Coordinate System Sync (Ensure Y-Up for Three.js)
        # Our internal numpy logic is already Y-up.

        print(f"✅ Phase 48: Linear Deformation Complete.")
        return new_vertices

# Singleton
shape_transformer = ShapeTransformer()
