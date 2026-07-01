"""
Back-Calculation Engine | PILLAR 1: FEEDBACK LOOP
===============================================
Optimizes SMPL shape parameters (betas) to match target measurements
provided by manual edits (e.g. from a tailor's ledger).

This allows the system to "learn" the true body shape that corresponds
to a set of ground-truth measurements.
"""
import numpy as np
import logging
from scipy.optimize import minimize
from typing import Dict, Optional, Tuple, List, Any

logger = logging.getLogger("BACK_CALCULATION")

class BackCalculationService:
    def __init__(self):
        from api.services.extract_measurements import ENGINE
        self.engine = ENGINE
        self.v_template = ENGINE._v_template
        self.shapedirs = ENGINE._shapedirs.reshape(-1, 3, 10) if ENGINE._shapedirs is not None else None

    def optimize_betas(self, target_measurements: Dict[str, float],
                       initial_betas: np.ndarray,
                       height_cm: float,
                       gender: str = 'male',
                       max_iter: int = 30) -> np.ndarray:
        """
        Refines betas so that mesh-extracted measurements match targets.
        """
        if self.v_template is None or self.shapedirs is None:
            logger.error("BackCalculation failed: SMPL templates not loaded")
            return initial_betas

        # Filter target measurements to those supported by the engine
        supported_keys = ['Chest Round', 'Waist Round', 'Hip Round', 'Thigh Round', 'Neck Round', 'Shoulder']
        targets = {k: v for k, v in target_measurements.items() if k in supported_keys and v > 0}

        if not targets:
            logger.warning("No valid target measurements for back-calculation.")
            return initial_betas

        def objective(betas):
            # 1. Reconstruct shaped mesh
            v_shaped = self.v_template + np.tensordot(self.shapedirs, betas, axes=([2], [0]))

            # 2. Extract measurements from mesh
            # Note: We use the raw extraction without calibration to get the true mesh state
            extracted = self.engine._calculate_from_indices(v_shaped, height_cm, gender)

            # 3. Compute L2 Error
            error = 0
            for k, target_val in targets.items():
                pred_val = extracted.get(k, 0)
                if pred_val > 0:
                    error += (pred_val - target_val) ** 2

            # 4. Biological Prior Regularization (GMM)
            # Ensure the back-calculated shape remains human-like
            prior_penalty = 0
            if hasattr(self.engine, '_shape_prior_gmm') and self.engine._shape_prior_gmm:
                try:
                    betas_std = self.engine._shape_scaler.transform(betas.reshape(1, -1))
                    logprob = self.engine._shape_prior_gmm.score_samples(betas_std)[0]
                    prior_penalty = -logprob * 0.1 # Weight prior
                except:
                    prior_penalty = 0.01 * np.sum(betas ** 2)
            else:
                prior_penalty = 0.01 * np.sum(betas ** 2)

            return error + prior_penalty

        # Optimization
        res = minimize(
            objective,
            initial_betas,
            method='L-BFGS-B',
            options={'maxiter': max_iter},
            bounds=[(-5, 5)] * 10
        )

        logger.info(f"✨ Back-Calculation Success. Error Reduced: {res.fun:.4f}")
        return res.x

# Singleton
back_calc_service = None
def get_back_calc_service():
    global back_calc_service
    if back_calc_service is None:
        back_calc_service = BackCalculationService()
    return back_calc_service
