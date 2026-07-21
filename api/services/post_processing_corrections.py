"""
Post-processing measurement corrections using rembg silhouettes.

This module is COMPLETELY SEPARATE from the main HMR extraction pipeline.
It applies corrections AFTER measurements are extracted and calibrated.

Approach:
1. Use rembg to extract front silhouette (background removal)
2. Use rembg to extract side silhouette (background removal)
3. Project SMPL mesh to 2D using camera params
4. Compare silhouette widths with mesh projection widths at chest/waist/hip
5. Apply correction factors to calibrated measurements

Usage in hmr_subprocess.py (AFTER calibration):
    from api.services.post_processing_corrections import apply_silhouette_corrections
    measurements = apply_silhouette_corrections(
        measurements, front_image, side_image, 
        smpl_params, height_cm, gender, vertex_map
    )
"""

import numpy as np
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def apply_silhouette_corrections(
    measurements: Dict[str, float],
    front_image: np.ndarray,
    side_image: Optional[np.ndarray],
    smpl_params: Optional[Dict],
    height_cm: float,
    gender: str,
    vertex_map: Dict[str, list],
    vertices: np.ndarray
) -> Dict[str, float]:
    """
    Apply silhouette-based corrections to calibrated measurements.
    
    This is a POST-PROCESSING step that runs AFTER calibration.
    It does NOT modify the main extraction pipeline.
    
    Args:
        measurements: Already calibrated measurements dict
        front_image: Front photo (BGR numpy array)
        side_image: Side photo (BGR numpy array) or None
        smpl_params: Dict with 'camera' key [s, tx, ty]
        height_cm: User's height in cm
        gender: 'male' or 'female'
        vertex_map: Dict mapping body part names to vertex indices
        vertices: SMPL mesh vertices (6890, 3)
    
    Returns:
        measurements dict with corrections applied
    """
    if front_image is None or smpl_params is None or 'camera' not in smpl_params:
        return measurements
    
    try:
        import cv2
        
        camera = smpl_params['camera']
        s, tx, ty = camera[0], camera[1], camera[2]
        img_h, img_w = front_image.shape[:2]
        
        # 1. Extract front silhouette using rembg
        front_silhouette = _extract_silhouette(front_image)
        if front_silhouette is None:
            logger.warning("Front silhouette extraction failed, skipping corrections")
            return measurements
        
        # 2. Extract side silhouette if available
        side_silhouette = None
        if side_image is not None:
            side_silhouette = _extract_silhouette(side_image)
        
        # 3. Project SMPL mesh to 2D
        pts_2d = _project_mesh_to_2d(vertices, s, tx, ty, img_w, img_h)
        
        # 4. Compute width corrections at chest/waist/hip levels
        front_corrections = _compute_width_corrections(
            pts_2d, front_silhouette, vertex_map, img_h, img_w, 'front'
        )
        logger.info(f"Front silhouette corrections: {front_corrections}")
        
        # 5. Compute depth corrections from side silhouette if available
        side_corrections = None
        if side_silhouette is not None and side_image is not None:
            # For side view, we need to re-project using side camera params
            # But we don't have side camera params, so skip side corrections for now
            logger.info("Side silhouette extracted but side camera params not available — skipping depth correction")
        
        # 6. Apply corrections to measurements
        corrected = dict(measurements)
        for level_name, key in [('chest', 'Chest Round'), ('waist', 'Waist Round'), ('hip', 'Hip Round')]:
            # Front correction: width (X-axis)
            front_corr = front_corrections.get(level_name, 1.0)
            
            # Combined correction (front only for now)
            combined = front_corr
            combined = max(0.85, min(1.25, combined))  # Conservative: ±15%
            
            if combined != 1.0 and key in corrected and corrected[key] > 0:
                old_val = corrected[key]
                corrected[key] = round(old_val * combined, 1)
                logger.info(f"Silhouette correction {level_name}: {old_val:.1f} → {corrected[key]:.1f}cm (×{combined:.2f})")
        
        return corrected
        
    except Exception as e:
        logger.warning(f"Silhouette corrections failed: {e}")
        return measurements


def _extract_silhouette(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract binary silhouette from photo using rembg.
    Returns True/False mask for each pixel.
    """
    try:
        from rembg import remove
        from PIL import Image
        import cv2
        
        # Convert BGR to RGB for rembg
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb = image.copy()
        
        # Run rembg
        pil_img = Image.fromarray(rgb)
        result = remove(pil_img)
        
        # Convert to numpy mask (alpha channel > 128 = foreground)
        result_np = np.array(result)
        if result_np.shape[2] == 4:  # RGBA
            mask = result_np[:, :, 3] > 128
        else:
            # Fallback: use grayscale threshold
            gray = cv2.cvtColor(result_np, cv2.COLOR_RGB2GRAY)
            mask = gray > 128
        
        return mask
        
    except Exception as e:
        logger.warning(f"rembg silhouette extraction failed: {e}")
        return None


def _project_mesh_to_2d(
    vertices: np.ndarray, 
    s: float, tx: float, ty: float,
    img_w: int, img_h: int
) -> np.ndarray:
    """Project SMPL mesh vertices to 2D using weak-perspective camera."""
    pts_2d = np.zeros((len(vertices), 2), dtype=np.float64)
    pts_2d[:, 0] = (vertices[:, 0] * s + tx) * img_w / 2 + img_w / 2
    pts_2d[:, 1] = (vertices[:, 1] * s + ty) * img_h / 2 + img_h / 2
    return pts_2d


def _compute_width_corrections(
    pts_2d: np.ndarray,
    silhouette: np.ndarray,
    vertex_map: Dict[str, list],
    img_h: int, img_w: int,
    view: str  # 'front' or 'side'
) -> Dict[str, float]:
    """
    Compare silhouette width with mesh projection width at chest/waist/hip levels.
    Returns correction factors: silhouette_width / mesh_width.
    """
    corrections = {}
    band_half = max(5, int(img_h * 0.02))  # ±2% of image height
    
    for level_name, vertex_key in [('chest', 'chest'), ('waist', 'waist'), ('hip', 'hips')]:
        group = vertex_map.get(vertex_key, [])
        if not group:
            continue
        
        # Find the 2D Y-level for this body part
        group_2d = pts_2d[group]
        level_y = int(np.mean(group_2d[:, 1]))
        
        if level_y < 0 or level_y >= img_h:
            continue
        
        # Measure mesh width at this level
        y_lo = max(0, level_y - band_half)
        y_hi = min(img_h, level_y + band_half)
        band_mask = (pts_2d[:, 1] >= y_lo) & (pts_2d[:, 1] <= y_hi)
        mesh_xs = pts_2d[band_mask, 0]
        if len(mesh_xs) < 2:
            continue
        mesh_width = (np.max(mesh_xs) - np.min(mesh_xs)) / img_w
        
        # Measure silhouette width at the same level
        band_silhouette = silhouette[y_lo:y_hi, :]
        fg_cols = np.where(np.any(band_silhouette, axis=0))[0]
        if len(fg_cols) < 2:
            continue
        sil_width = (fg_cols[-1] - fg_cols[0]) / img_w
        
        # Compute correction factor
        if mesh_width > 0.01:
            ratio = sil_width / mesh_width
            ratio = max(0.85, min(1.25, ratio))  # Conservative: ±15%
            corrections[level_name] = ratio
    
    return corrections
