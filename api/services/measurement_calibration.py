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
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any


def _default_factors() -> Dict[str, Dict[str, list]]:
    """
    Default calibration factors. First tries calibration_factors.json (if file
    exists alongside this module), otherwise uses inline defaults trained from
    UniData (6 subjects) via ridge regression (alpha=1.0).

    Note: Model Agency factors are available in calibration_factors.json but
    NOT used as defaults — they're optimized for fashion models who have
    systematically different body proportions than the general population.
    To switch, pass factors_path to MeasurementCalibrator().

    Format: {gender: {measurement_key: [alpha, beta]}}
    Where: real = alpha * smpl + beta
    """
    # Inline defaults (trained on UniData 6 subjects — general population)
    return {
        "male": {
            "Waist Round": [0.87, -0.9],
            "Hip Round": [0.90, -0.6],
            "Chest Round": [0.84, -0.5],
            "Shoulder": [0.96, 0.0],
            "Neck Round": [0.95, 0.0],
            "Thigh Round": [0.95, 0.0],
            "Calf Round": [0.96, 0.0],
            # Pattern-drafting dimensions (Phase 17)
            "Across Shoulder": [0.96, 0.0],
            "Neck to Waist": [1.0, 0.0],
            "Waist to Hip": [1.0, 0.0],
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
            # Pattern-drafting dimensions (Phase 17)
            "Across Shoulder": [0.93, 0.2],
            "Neck to Waist": [1.0, 0.0],
            "Waist to Hip": [1.0, 0.0],
        },
    }


class MeasurementCalibrator:
    """
    Calibrates SMPL-derived measurements to real-world-equivalent values.
    Thread-safe (read-only after init).

    NEW: Supports Subgroup-Specific Calibration (Pillar 4).
    """

    def __init__(self, factors_path: Optional[str] = None):
        self.factors_path = factors_path
        self.factors = self._load(factors_path)
        self.subgroup_model = self._load_subgroup_model()

    def _load(self, path: Optional[str] = None) -> Dict[str, Dict[str, list]]:
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return _default_factors()

    def _load_subgroup_model(self) -> Optional[Dict[str, Any]]:
        """Load the trained subgroup calibration model (KMeans + Ridge)."""
        model_path = Path(__file__).parent.parent / "models" / "priors" / "subgroup_calibration.pkl"
        if model_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                print(f"✅ Subgroup Calibration Active: {model.get('n_clusters')} archetypes loaded.")
                return model
            except Exception as e:
                print(f"⚠️ Subgroup Calibration Load failed: {e}")
        return None

    def calibrate(self, measurements: Dict[str, float],
                  gender: str = 'male') -> Dict[str, float]:
        """
        Apply calibration to a measurements dict in-place and return it.

        Logic:
        1. Try Subgroup-Specific Calibration if model and smpl_params are available.
        2. Fallback to Global Gender-Based Calibration.
        3. Apply Pose-Aware Corrections (Waist).
        """
        # A. ATTEMPT SUBGROUP CALIBRATION (Pillar 4)
        subgroup_applied = False
        if self.subgroup_model and 'pose_metrics' in measurements:
            # We need shape params to find the cluster
            # In our pipeline, smpl_params are usually available in the full measurements dict
            # or passed through the extraction flow.
            # Assume __smpl_params key (Phase 0 convention)
            smpl = measurements.get('__smpl_params', {})
            shape = smpl.get('shape')
            height = measurements.get('height') or measurements.get('Height')

            if shape and len(shape) == 10 and height:
                try:
                    gender_enc = 1.0 if gender.lower() == 'male' else 0.0
                    feat = np.concatenate([shape, [gender_enc], [height / 200.0]]).reshape(1, -1)

                    # Normalize features
                    feat_std = self.subgroup_model['scaler'].transform(feat)

                    # Predict cluster
                    cluster_idx = self.subgroup_model['clusterer'].predict(feat_std)[0]
                    cluster_factors = self.subgroup_model['per_cluster_factors'][cluster_idx]

                    # Apply factors
                    for mk, f in cluster_factors.items():
                        if mk in measurements and measurements[mk] > 0 and f['alpha'] != 1.0:
                            measurements[mk] = round(f['alpha'] * measurements[mk] + f['beta'], 1)

                    subgroup_applied = True
                except Exception as e:
                    print(f"⚠️ Subgroup application failed: {e}")

        # B. FALLBACK TO GLOBAL CALIBRATION (Only if subgroup didn't handle it)
        if not subgroup_applied:
            gender_factors = self.factors.get(gender, {})
            for factor_key, (alpha, beta) in gender_factors.items():
                snake_key = factor_key.lower().replace(' ', '_')
                matched_keys = [k for k in (factor_key, snake_key)
                                if k in measurements and measurements.get(k, 0) > 0]
                for matched_key in matched_keys:
                    val = measurements[matched_key]
                    corrected = alpha * val + beta
                    measurements[matched_key] = round(max(corrected, 0.1), 1)

        # C. POSE-AWARE CORRECTIONS (Always apply)
        pose_metrics = measurements.get('pose_metrics', {})
        tilt = pose_metrics.get('torso_tilt', 0.0)
        expansion = pose_metrics.get('abdomen_expansion', 1.0)

        # We need the key to exist to apply pose correction
        waist_keys = [k for k in ('Waist Round', 'waist_round') if k in measurements]
        for wk in waist_keys:
            val = measurements[wk]
            shrinkage = 1.0
            if tilt > 10:
                # Tilt shrinkage: 1% per 2 degrees above 10
                shrinkage *= (1.0 - (min(tilt, 30) - 10) / 100.0 * 0.5)
            if expansion > 1.1:
                # Expansion shrinkage: proportional to overshoot
                shrinkage *= (1.0 / expansion)

            if shrinkage != 1.0:
                measurements[wk] = round(max(val * shrinkage, 10.0), 1)

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
