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

        # Load validation metadata (Phase 64)
        norm_path = Path(__file__).parent.parent.parent / "data" / "ansur_processed" / "normalization_meta.json"
        if norm_path.exists():
            with open(norm_path, 'r') as f:
                self.validation_meta = json.load(f)
        else:
            self.validation_meta = {}

    def validate_scan(self, gender: str, measurements: dict, confidence: float = 1.0):
        """
        Phase 64: Biometric Validation (3 Standard Deviations)
        Phase 65: Scan Integrity Check (Confidence > 85%)
        """
        # 1. Confidence Check (Phase 65)
        if confidence < 0.85:
            return False, f"Scan Integrity Failed: Confidence ({confidence:.2f}) < 85%"

        # 2. Biometric Outlier Check (Phase 64)
        meta = self.validation_meta.get(gender.lower())
        if not meta: return True, "OK" # Fallback if meta missing

        # Mapping KORRA keys to ANSUR keys used in validation
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
        """
        model = self.models.get(gender.lower())
        if not model:
            return inputs # Fallback

        # Map KORRA keys to ANSUR predictors
        # Predictors: ['stature_cm', 'chestcircumference', 'waistcircumference', 'buttockcircumference', 'biacromialbreadth']
        x = np.array([
            inputs.get('height', 170),
            inputs.get('chest_round', 90),
            inputs.get('waist_round', 80),
            inputs.get('hip_round', 95),
            inputs.get('shoulder', 40)
        ]).reshape(1, -1)

        coef = np.array(model['coef'])
        intercept = np.array(model['intercept'])

        # Matrix Multiplication: y = X * W^T + b
        predictions = (x @ coef.T + intercept).flatten()

        result = {**inputs}
        for i, target_name in enumerate(model['targets']):
            # Map back to KORRA terminology if needed, or keep ANSUR names
            result[target_name] = round(float(predictions[i]), 2)

        return result

# Singleton Instance
imputation_service = ImputationService()
