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
