import json
import numpy as np
import os
from pathlib import Path

class ImputationService:
    def __init__(self):
        self.model_dir = Path(__file__).parent.parent / "models" / "imputation"
        self.models = {}
        self._load_models()

    def _load_models(self):
        for gender in ['male', 'female']:
            weight_path = self.model_dir / f"{gender}_weights.json"
            if weight_path.exists():
                with open(weight_path, 'r') as f:
                    self.models[gender] = json.load(f)

        norm_path = Path(__file__).parent.parent.parent / "data" / "ansur_processed" / "normalization_meta.json"
        if norm_path.exists():
            with open(norm_path, 'r') as f:
                self.validation_meta = json.load(f)
        else:
            self.validation_meta = {}

    def validate_scan(self, gender: str, measurements: dict, confidence: float = 1.0):
        if confidence < 0.85:
            return False, f"Scan Integrity Failed: Confidence ({confidence:.2f}) < 85%"

        meta = self.validation_meta.get(gender.lower())
        if not meta: return True, "OK"

        mapping = {
            'chest_round': 'chestcircumference',
            'waist_round': 'waistcircumference',
            'height': 'stature_cm'
        }

        for korra_key, ansur_key in mapping.items():
            val = measurements.get(korra_key)
            if val and ansur_key in meta:
                stats = meta[ansur_key]
                z_score = abs(val - stats['mean']) / stats['std']
                if z_score > 3.0:
                    return False, f"Biometric Validation Failed: {korra_key} is outside 3-sigma ({z_score:.2f})"

        return True, "OK"

    def impute(self, gender: str, inputs: dict):
        """
        Phase 26: Biometric Imputation Hook
        Inputs: {height, chest_round, waist_round, hip_round, shoulder}
        Returns: inputs plus ANSUR-predicted derived measurements.
        Core circumferences are not modified here — calibration is
        handled by MeasurementCalibrator (see measurement_engine.py).
        """
        model = self.models.get(gender.lower())
        if not model:
            return inputs

        x = np.array([
            inputs.get('height', 170),
            inputs.get('chest_round', 90),
            inputs.get('waist_round', 80),
            inputs.get('hip_round', 95),
            inputs.get('shoulder', 40)
        ]).reshape(1, -1)

        coef = np.array(model['coef'])
        intercept = np.array(model['intercept'])

        predictions = (x @ coef.T + intercept).flatten()

        result = {**inputs}
        for i, target_name in enumerate(model['targets']):
            result[target_name] = round(float(predictions[i]), 2)

        return result

    def fuse_measurements(self, gender: str, hmr_measurements: dict = None,
                          mp_measurements: dict = None, user_height_cm: float = 170,
                          hmr_confidence: float = 0.9, mp_confidence: float = 0.6):
        """
        Hybrid Fusion: Combines HMR and MediaPipe measurements using ANSUR imputation.
        - HMR is primary (higher precision, weight=0.7)
        - MediaPipe is complementary (fills gaps, weight=0.3)
        - ANSUR II regression provides statistical refinement
        Both sets feed into the imputation model for maximum accuracy.
        """
        fused = {
            'height': user_height_cm,
            'chest_round': 90.0,
            'waist_round': 80.0,
            'hip_round': 95.0,
            'shoulder': 40.0
        }

        weight_hmr = hmr_confidence / (hmr_confidence + mp_confidence) if hmr_measurements else 0.0
        weight_mp = mp_confidence / (hmr_confidence + mp_confidence) if mp_measurements else 0.0

        key_mapping = {
            'Chest Round': ('chest_round', 'chest_round'),
            'Waist Round': ('waist_round', 'waist_round'),
            'Hip Round': ('hip_round', 'hip_round'),
            'Shoulder': ('shoulder', 'shoulder'),
            'Stomach Round': ('stomach_round', 'stomach_round'),
            'Neck Round': ('neck_round', 'neck_round'),
            'Thigh Round': ('thigh_round', 'thigh_round'),
            'Bust Round': ('bust_round', 'bust_round'),
        }

        for mp_key, (hmr_key, fusion_key) in key_mapping.items():
            h_val = hmr_measurements.get(mp_key) if hmr_measurements else None
            m_val = mp_measurements.get(mp_key) if mp_measurements else None

            if h_val is not None and m_val is not None:
                fused[fusion_key] = round(h_val * weight_hmr + m_val * weight_mp, 1)
            elif h_val is not None:
                fused[fusion_key] = h_val
            elif m_val is not None:
                fused[fusion_key] = m_val

        refined = self.impute(gender, fused)

        refined['fusion_weight_hmr'] = round(weight_hmr, 2)
        refined['fusion_weight_mediapipe'] = round(weight_mp, 2)
        refined['fusion_hmr_available'] = hmr_measurements is not None
        refined['fusion_mp_available'] = mp_measurements is not None

        return refined


imputation_service = ImputationService()
