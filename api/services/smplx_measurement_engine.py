"""
SMPL-X Measurement Engine for HBW/SHAPY Dataset Validation
============================================================
Extracts body measurements from SMPL-X meshes (10,475 vertices, 20,908 faces)
using the same plane-mesh intersection approach as the SMPL pipeline.
"""
import os
import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy.spatial import ConvexHull

logger = logging.getLogger("SMPLX_MEASUREMENT")

BASE_DIR = Path(__file__).parent.resolve()
SRC_DIR = BASE_DIR / "src" / "tf_smpl"

FACES_PATH = SRC_DIR / "smplx_faces.npy"
FACE_SEG_PATH = SRC_DIR / "smplx_body_parts_2_faces.json"
VERT_SEG_PATH = SRC_DIR / "smplx_vert_segmentation.json"

# Same body-part mapping as SMPL pipeline (body part names are consistent)
CIRCUMFERENCE_TO_BODYPARTS = {
    'chest': ['spine1', 'spine2'],
    'waist': ['hips', 'spine'],
    'hips': ['hips'],
    'neck': ['neck'],
    'belly': ['spine', 'spine1'],
    'thigh': ['leftUpLeg', 'rightUpLeg'],
    'ankle': ['leftLeg', 'rightLeg', 'leftFoot', 'rightFoot'],
    'bicep': ['leftArm', 'rightArm'],
    'calf': ['leftLeg', 'rightLeg'],
    'knee': ['leftLeg', 'rightLeg'],
}

# Map measurement names to the body part vertex groups for Y-origin computation
# Uses Meshcapade vertex segmentation to get all vertices for each body region
MEASUREMENT_TO_VERTEX_GROUP = {
    'chest': ['spine1', 'spine2'],
    'waist': ['hips', 'spine'],
    'hips': ['hips'],
    'neck': ['neck'],
    'belly': ['spine', 'spine1'],
    'thigh': ['leftUpLeg', 'rightUpLeg'],
    'ankle': ['leftLeg', 'rightLeg'],
    'wrist': ['leftForeArm', 'rightForeArm'],
    'bicep': ['leftArm', 'rightArm'],
    'calf': ['leftLeg', 'rightLeg'],
    'knee': ['leftLeg', 'rightLeg'],
}

# Slice Y position as percentile of the body part's Y range.
# 0.0 = top of body part, 1.0 = bottom of body part.
# These are tuned for SMPL-X HBW meshes (various poses, not T-pose).
SLICE_POSITIONS = {
    'chest': 0.30,    # Upper torso, nipple line
    'waist': 0.60,    # Narrowest point between ribs and hips
    'hips': 0.80,     # Widest point of hips/glutes
    'neck': 0.15,     # Base of neck
    'belly': 0.50,    # Mid-belly
    'thigh': 0.45,    # Mid-upper leg
    'calf': 0.55,     # Mid-lower leg
    'bicep': 0.40,    # Mid-upper arm
    'ankle': 0.85,    # Near bottom of lower leg
    'knee': 0.15,     # Top of lower leg
}

OUTPUT_KEYS = [
    'height_cm', 'chest_cm', 'waist_cm', 'hip_cm', 'shoulder_cm',
    'neck_cm', 'thigh_cm', 'calf_cm', 'bicep_cm', 'ankle_cm'
]


def _mesh_plane_intersection(vertices: np.ndarray, faces: np.ndarray,
                              plane_origin: np.ndarray,
                              plane_normal: np.ndarray) -> np.ndarray:
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


def _calc_circ_from_mesh_slice(vertices: np.ndarray, faces: np.ndarray,
                                group_indices: List[int], scale: float,
                                normal=(0, 1, 0),
                                face_mask: Optional[np.ndarray] = None) -> float:
    if not group_indices or faces is None or len(faces) == 0:
        return 0.0
    if face_mask is not None:
        faces = faces[face_mask]
        if len(faces) == 0:
            return 0.0
    normal = np.asarray(normal, dtype=np.float64)
    origin = np.mean(vertices[group_indices], axis=0)
    points = _mesh_plane_intersection(vertices, faces, origin, normal)
    if len(points) < 3:
        return 0.0
    points = np.round(points, decimals=6)
    points = np.unique(points, axis=0)
    if len(points) < 3:
        return 0.0
    # Bilateral cluster detection
    xs = points[:, 0]
    x_range = xs.max() - xs.min()
    if x_range > 0.15 and len(points) >= 6:
        sorted_xs = np.sort(xs)
        gaps = sorted_xs[1:] - sorted_xs[:-1]
        max_gap = np.max(gaps)
        if max_gap > 0.08:
            gap_idx = np.argmax(gaps)
            split_x = (sorted_xs[gap_idx] + sorted_xs[gap_idx + 1]) / 2
            left_pts = points[xs < split_x]
            right_pts = points[xs >= split_x]
            def _hp(pts):
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
            return round(_hp(left_pts) + _hp(right_pts), 1)
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


class SmplxMeasurementEngine:
    def __init__(self):
        self.faces: Optional[np.ndarray] = None
        self.face_segmentation: Optional[dict] = None
        self.vert_segmentation: Optional[dict] = None
        self._load_faces()
        self._load_face_segmentation()
        self._load_vert_segmentation()

    def _load_faces(self):
        try:
            self.faces = np.load(str(FACES_PATH)).astype(np.int32)
        except Exception as e:
            logger.warning(f"Could not load SMPL-X faces: {e}")

    def _load_face_segmentation(self):
        try:
            with open(str(FACE_SEG_PATH)) as f:
                self.face_segmentation = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load SMPL-X face segmentation: {e}")

    def _load_vert_segmentation(self):
        try:
            with open(str(VERT_SEG_PATH)) as f:
                self.vert_segmentation = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load SMPL-X vertex segmentation: {e}")

    def get_vertex_group(self, group_name: str) -> List[int]:
        """Get vertex indices for a measurement group from the Meshcapade segmentation."""
        if self.vert_segmentation is None:
            return []
        body_parts = MEASUREMENT_TO_VERTEX_GROUP.get(group_name)
        if body_parts is None:
            return []
        indices = set()
        for bp in body_parts:
            indices.update(self.vert_segmentation.get(bp, []))
        return sorted(indices)

    def get_face_mask(self, group_name: str,
                      vertices: Optional[np.ndarray] = None,
                      group_indices: Optional[List[int]] = None) -> Optional[np.ndarray]:
        """Get boolean mask of faces for a given measurement group's body parts."""
        if self.face_segmentation is None or self.faces is None:
            return None
        body_parts = CIRCUMFERENCE_TO_BODYPARTS.get(group_name)
        if body_parts is None:
            return None
        face_indices = set()
        for bp in body_parts:
            face_indices.update(self.face_segmentation.get(bp, []))
        if not face_indices:
            return None
        if vertices is not None and group_indices and len(group_indices) > 0:
            vg_mean_x = np.mean(vertices[group_indices, 0])
            if abs(vg_mean_x) > 0.01:
                face_list = np.array(list(face_indices), dtype=np.int32)
                face_verts = self.faces[face_list]
                face_mean_x = vertices[face_verts].mean(axis=1)[:, 0]
                same_side = np.sign(face_mean_x) == np.sign(vg_mean_x)
                mask = np.zeros(len(self.faces), dtype=bool)
                mask[face_list[same_side]] = True
                return mask
        mask = np.zeros(len(self.faces), dtype=bool)
        mask[list(face_indices)] = True
        return mask

    def _slice_y_for_group(self, vertices: np.ndarray, group_name: str) -> Optional[float]:
        """Compute the Y position to slice for a given measurement group.
        Uses the body part's vertex Y-range and a predefined percentile.
        """
        indices = self.get_vertex_group(group_name)
        if not indices:
            return None
        y_vals = vertices[indices, 1]
        y_min, y_max = y_vals.min(), y_vals.max()
        percentile = SLICE_POSITIONS.get(group_name, 0.5)
        y_slice = y_max - (y_max - y_min) * percentile
        return y_slice

    def _calc_circ_at_y(self, vertices: np.ndarray, group_name: str,
                         y_slice: float, scale: float,
                         group_indices: Optional[List[int]] = None) -> float:
        """Compute circumference at a given Y position using body-part face filtering."""
        face_mask = self.get_face_mask(group_name, vertices, group_indices)
        if face_mask is None:
            return 0.0
        filtered_faces = self.faces[face_mask]
        if len(filtered_faces) == 0:
            return 0.0
        # Origin is at (0, y_slice, 0) — center of body at that Y
        origin = np.array([0.0, y_slice, 0.0])
        normal = np.array([0.0, 1.0, 0.0])
        points = _mesh_plane_intersection(vertices, filtered_faces, origin, normal)
        if len(points) < 3:
            return 0.0
        points = np.round(points, decimals=6)
        points = np.unique(points, axis=0)
        if len(points) < 3:
            return 0.0
        # Bilateral split: if the face mask includes left/right body part pairs,
        # split at X=0 midline to get single-side measurements.
        # Torso measurements (spine, hips, neck) stay as single hull.
        bs = CIRCUMFERENCE_TO_BODYPARTS.get(group_name, [])
        is_bilateral = all(bp.startswith(('left', 'right')) for bp in bs) if bs else False
        if is_bilateral:
            left_pts = points[points[:, 0] < 0]
            right_pts = points[points[:, 0] >= 0]
            def _hp(pts):
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
            lh = _hp(left_pts)
            rh = _hp(right_pts)
            if lh > 0 and rh > 0:
                return round(max(lh, rh), 1)
            if lh > 0 or rh > 0:
                return round(max(lh, rh), 1)
            return 0.0
        # Single cluster
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

    def compute_measurements(self, vertices: np.ndarray,
                              height_cm: float,
                              gender: str = 'neutral') -> Dict[str, float]:
        if self.faces is None:
            return {k: 0.0 for k in OUTPUT_KEYS}
        v_min, v_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
        v_height = v_max - v_min
        scale = height_cm / (v_height * 100)
        results = {}
        results['height_cm'] = height_cm

        for metric, group_name in [('chest_cm', 'chest'), ('waist_cm', 'waist'),
                                    ('hip_cm', 'hips'), ('neck_cm', 'neck'),
                                    ('thigh_cm', 'thigh'), ('calf_cm', 'calf'),
                                    ('bicep_cm', 'bicep'), ('ankle_cm', 'ankle')]:
            y_slice = self._slice_y_for_group(vertices, group_name)
            if y_slice is not None:
                indices = self.get_vertex_group(group_name)
                results[metric] = self._calc_circ_at_y(
                    vertices, group_name, y_slice, scale, group_indices=indices)
            else:
                results[metric] = 0.0

        # Shoulder width: dynamic from mesh
        # For non-T-pose SMPL-X, shoulder Y is at the top of the spine2 body part
        sp2_idx = self.vert_segmentation.get('spine2', []) if self.vert_segmentation else []
        if sp2_idx:
            sp2_y_top = np.max(vertices[sp2_idx, 1])
            sh_y = sp2_y_top - 0.005
        else:
            y_slice = self._slice_y_for_group(vertices, 'chest')
            sh_y = (y_slice or 0) + 0.015
        band = 0.020
        sh_mask = np.abs(vertices[:, 1] - sh_y) < band
        if np.sum(sh_mask) >= 5:
            sh_width = (vertices[sh_mask, 0].max() - vertices[sh_mask, 0].min()) * 100 * scale
            if 22 < sh_width < 65:
                results['shoulder_cm'] = round(sh_width, 1)
            else:
                results['shoulder_cm'] = 0.0
        else:
            results['shoulder_cm'] = 0.0

        return results


ENGINE = SmplxMeasurementEngine()


def extract_smplx_measurements(vertices: np.ndarray, height_cm: float,
                                gender: str = 'neutral') -> Dict[str, float]:
    return ENGINE.compute_measurements(vertices, height_cm, gender)
