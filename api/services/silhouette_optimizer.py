"""
Silhouette-Based Shape Optimizer | PILLAR 3: ITERATIVE FITTING
==============================================================
Optimizes SMPL shape parameters (betas) to maximize overlap (IoU)
between the 3D mesh projection and the 2D image silhouette.
"""
import numpy as np
import cv2
import logging
from scipy.optimize import minimize
from typing import Dict, Optional, Tuple, List, Any

logger = logging.getLogger("SILHOUETTE_OPTIMIZER")

class SilhouetteOptimizer:
    def __init__(self, v_template: np.ndarray, shapedirs: np.ndarray,
                 gmm: Optional[Any] = None, scaler: Optional[Any] = None):
        """
        v_template: (6890, 3)
        shapedirs: (6890, 3, 10) or (20670, 10)
        gmm: Optional sklearn GaussianMixture
        scaler: Optional sklearn StandardScaler
        """
        self.v_template = v_template
        self.shapedirs = shapedirs.reshape(-1, 3, 10) if shapedirs.ndim == 2 else shapedirs
        self.gmm = gmm
        self.scaler = scaler
        self.num_betas = 10

    def project_mesh(self, betas: np.ndarray, camera: np.ndarray, img_shape: Tuple[int, int]) -> np.ndarray:
        """
        Projects SMPL mesh to 2D image plane.
        camera: [scale, tx, ty]
        Returns: points_2d (6890, 2)
        """
        # 1. Reconstruct shaped mesh (T-pose)
        # v = v_template + shapedirs @ betas
        v_shaped = self.v_template + np.tensordot(self.shapedirs, betas, axes=([2], [0]))

        # 2. Project using weak-perspective camera
        s, tx, ty = camera
        h, w = img_shape[:2]

        points_2d = v_shaped[:, :2].copy()
        # Scale and Translate
        points_2d[:, 0] = (points_2d[:, 0] * s + tx) * w / 2 + w / 2
        points_2d[:, 1] = (points_2d[:, 1] * s + ty) * h / 2 + h / 2

        return points_2d

    def render_silhouette(self, points_2d: np.ndarray, img_shape: Tuple[int, int]) -> np.ndarray:
        """Renders binary mask using cv2.fillPoly."""
        h, w = img_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        # Use a subset of vertices for speed, or a convex hull if appropriate
        # For a full human body, we need the outer boundary.
        # Actually, fillPoly works on the full set of vertices if they are ordered,
        # but SMPL vertices are not a single contour.
        # However, we can use cv2.convexHull for a quick approximation,
        # or just draw points and dilate.
        # Better: use a pre-defined list of boundary vertices or use a hull.

        # Silhouette from vertices:
        # Drawing every vertex as a point and then closing the gaps is robust.
        pts = points_2d.astype(np.int32)

        # Filter points inside image bounds
        pts = pts[(pts[:, 0] >= 0) & (pts[:, 0] < w) & (pts[:, 1] >= 0) & (pts[:, 1] < h)]
        if len(pts) > 0:
            mask[pts[:, 1], pts[:, 0]] = 255
            # Dilate and erode to fill gaps between vertices
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.erode(mask, kernel, iterations=1)

        return mask

    def compute_iou(self, mask_pred: np.ndarray, mask_gt: np.ndarray) -> float:
        """Intersection over Union."""
        # Ensure mask_gt is 2D (MediaPipe often returns H,W,1)
        if mask_gt.ndim == 3:
            mask_gt = np.squeeze(mask_gt)

        intersection = np.logical_and(mask_pred > 0, mask_gt > 0).sum()
        union = np.logical_or(mask_pred > 0, mask_gt > 0).sum()
        if union == 0:
            return 0.0
        return float(intersection / union)

    def optimize(self, initial_betas: np.ndarray, camera: np.ndarray,
                 image_mask: np.ndarray, max_iter: int = 20) -> np.ndarray:
        """
        Optimizes betas to maximize IoU with image_mask.
        """
        h, w = image_mask.shape[:2]

        def objective(betas):
            # 1. Project
            pts_2d = self.project_mesh(betas, camera, (h, w))
            # 2. Render
            mask_pred = self.render_silhouette(pts_2d, (h, w))
            # 3. Score
            iou = self.compute_iou(mask_pred, image_mask)

            # 4. Penalty: GMM Log-Likelihood (Pillar 2 Regularization)
            # If GMM is available, use it to penalize biologically implausible shapes.
            # Otherwise fallback to L2.
            if self.gmm and self.scaler:
                try:
                    betas_std = self.scaler.transform(betas.reshape(1, -1))
                    logprob = self.gmm.score_samples(betas_std)[0]
                    # Score is 1-IoU + negative log-likelihood (minimized)
                    # We scale NLL to be competitive with IoU units (0-1)
                    penalty = -logprob * 0.05
                except:
                    penalty = 0.01 * np.sum(betas ** 2)
            else:
                penalty = 0.01 * np.sum(betas ** 2)

            return (1.0 - iou) + penalty

        # COBYLA is good for derivative-free optimization with few variables
        res = minimize(
            objective,
            initial_betas,
            method='COBYLA',
            options={'maxiter': max_iter, 'rhobeg': 0.1},
            bounds=[(-5, 5)] * self.num_betas
        )

        logger.info(f"🚀 Silhouette Optimization Complete. IoU Improved: {1.0 - res.fun + 0.01*np.sum(res.x**2):.4f}")
        return res.x

# Singleton for engine-wide use
_instance = None
def get_optimizer():
    global _instance
    if _instance is None:
        from api.services.extract_measurements import ENGINE
        if ENGINE._v_template is not None and ENGINE._shapedirs is not None:
            _instance = SilhouetteOptimizer(
                ENGINE._v_template,
                ENGINE._shapedirs,
                gmm=getattr(ENGINE, '_shape_prior_gmm', None),
                scaler=getattr(ENGINE, '_shape_scaler', None)
            )
        else:
            logger.warning("SilhouetteOptimizer failed: SMPL templates not loaded in ENGINE")
    return _instance
