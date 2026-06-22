import numpy as np
import logging
from typing import Dict, Tuple

logger = logging.getLogger("KORRA_MESH_VALIDATOR")

class MeshValidator:
    """
    KORRA Mesh Validator | Phases 91-105
    Validates clinical parity between scanned biometrics and the virtual 3D mesh.
    """

    def calculate_mesh_measurements(self, vertices: np.ndarray, partitions: dict) -> Dict[str, float]:
        """
        Phase 92: Mesh Measurement Extractor
        Calculates physical dimensions from the 3D vertex cloud.
        """
        measurements = {}

        try:
            # 1. Height Calculation
            y_coords = vertices[:, 1]
            height = (np.max(y_coords) - np.min(y_coords)) * 100.0 # Convert to cm
            measurements['height'] = round(float(height), 2)

            # 2. Sectional Girth Approximations (Simplistic Euclidean Distances for Phase 92)
            # In a full implementation, this would use convex hulls or path-finding around vertex loops.
            for part in ['chest', 'waist', 'legs']:
                if part in partitions and len(partitions[part]) > 0:
                    part_vertices = vertices[partitions[part]]
                    # Girth approximation: 2 * PI * average radius in XZ plane
                    radii = np.sqrt(part_vertices[:, 0]**2 + part_vertices[:, 2]**2)
                    avg_radius = np.mean(radii)
                    girth = 2 * np.pi * avg_radius * 100.0
                    measurements[f'{part}_round'] = round(float(girth), 2)

            return measurements
        except Exception as e:
            logger.error(f"❌ Phase 92 Validation Failure: {e}")
            return {}

    def calculate_realism_index(self, scanned: dict, mesh_derived: dict) -> float:
        """
        Phase 96: Anthropomorphic Score
        Targets < 1.2cm variance (Phase 93)
        """
        variances = []
        mapping = {
            'height': 'height',
            'chest_round': 'chest_round',
            'waist_round': 'waist_round'
        }

        for s_key, m_key in mapping.items():
            if s_key in scanned and m_key in mesh_derived:
                var = abs(scanned[s_key] - mesh_derived[m_key])
                variances.append(var)

        if not variances: return 0.0

        mean_variance = np.mean(variances)
        # Score: 100 - (mean_variance * factor). Target variance < 1.2cm
        score = max(0, 100 - (mean_variance * 5))

        logger.info(f"📊 Phase 96 Audit: Clinical Realism Index = {score:.2f}% (Avg Var: {mean_variance:.2f}cm)")
        return float(score)

# Singleton
mesh_validator = MeshValidator()
