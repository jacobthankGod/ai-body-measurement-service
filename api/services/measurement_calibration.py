"""
SMPL-to-Real-World Measurement Calibration
===========================================
Corrects systematic biases in SMPL-derived body measurements using
learned linear factors from validation data.

Industry-standard approach: SMPL shape parameters are accurate at the
vertex level (PVE-T-SC 2.16cm), but the SMPL template's T-pose shape
space overestimates torso circumferences relative to real-world tailor
tape measurements. This module applies a per-measurement, per-gender
linear calibration:  real = alpha * smpl + beta

Calibration factors are computed from ground truth validation data
(UniData: 6 subjects) and stored in calibration_factors.json for easy
update as more data is collected.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional


def _default_factors() -> Dict[str, Dict[str, list]]:
    """
    Default calibration factors computed from UniData validation (6 subjects).
    Ridge regression (alpha=1.0) to prevent overfitting on small sample.
    Format: {gender: {measurement_key: [alpha, beta]}}
    Where: real = alpha * smpl + beta
    """
    return {
        "male": {
            "Waist Round": [0.87, -0.9],
            "Hip Round": [0.90, -0.6],
            "Chest Round": [0.84, -0.5],
            "Shoulder": [0.96, 0.0],
            "Neck Round": [0.95, 0.0],
            "Thigh Round": [0.95, 0.0],
            "Calf Round": [0.96, 0.0],
        },
        "female": {
            "Waist Round": [0.85, -0.0],
            "Hip Round": [0.88, 0.5],
            "Bust Round": [0.89, 0.9],
            "Chest Round": [0.89, 0.9],
            "Shoulder": [0.93, 0.2],
            "Neck Round": [0.93, 0.1],
            "Thigh Round": [0.95, 0.0],
            "Calf Round": [0.95, 0.0],
        },
    }


class MeasurementCalibrator:
    """
    Calibrates SMPL-derived measurements to real-world-equivalent values.
    Thread-safe (read-only after init).
    """

    def __init__(self, factors_path: Optional[str] = None):
        self.factors_path = factors_path
        self.factors = self._load(factors_path)

    def _load(self, path: Optional[str] = None) -> Dict[str, Dict[str, list]]:
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return _default_factors()

    def calibrate(self, measurements: Dict[str, float],
                  gender: str = 'male') -> Dict[str, float]:
        """
        Apply calibration to a measurements dict in-place and return it.
        Only modifies measurements that have calibration factors defined.
        Handles both Title Case (e.g. 'Waist Round') and snake_case
        (e.g. 'waist_round') key formats. If both variants exist in the
        dict, both are updated.
        """
        gender_factors = self.factors.get(gender, {})
        for factor_key, (alpha, beta) in gender_factors.items():
            snake_key = factor_key.lower().replace(' ', '_')
            matched_keys = [k for k in (factor_key, snake_key)
                            if k in measurements and measurements.get(k, 0) > 0]
            for matched_key in matched_keys:
                corrected = alpha * measurements[matched_key] + beta
                measurements[matched_key] = round(max(corrected, 0.1), 1)
        return measurements

    def save_factors(self, path: Optional[str] = None):
        """Save current calibration factors to JSON file."""
        out_path = path or self.factors_path
        if out_path:
            with open(out_path, 'w') as f:
                json.dump(self.factors, f, indent=2)

    @staticmethod
    def compute_factors(smpl_values: list, real_values: list,
                        ridge_alpha: float = 1.0) -> tuple:
        """
        Compute calibration factors [alpha, beta] using ridge regression.
        smpl_values: list of SMPL-predicted measurements
        real_values: list of corresponding ground truth measurements
        ridge_alpha: L2 regularization strength (1.0 = mild shrinkage)
        Returns: (alpha, beta)
        """
        import numpy as np
        X = np.array(smpl_values)
        y = np.array(real_values)
        n = len(X)
        if n < 2:
            return [1.0, 0.0]

        # Ridge regression: beta = (X'X + lambda*I)^(-1) X'y
        # For 1D case with intercept: minimize ||y - (a*x + b)||^2 + lambda*(a^2 + b^2)
        X_design = np.column_stack([X, np.ones(n)])
        I = np.eye(2)
        coef = np.linalg.inv(X_design.T @ X_design + ridge_alpha * I) @ X_design.T @ y
        return [round(float(coef[0]), 4), round(float(coef[1]), 4)]


# Singleton for production use
calibrator = MeasurementCalibrator()
