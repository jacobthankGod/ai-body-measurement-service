import pytest
import numpy as np
from api.services.imputation_service import imputation_service
from api.services.shape_transformer import shape_transformer
from api.services.mesh_validator import mesh_validator

def test_ansur_imputation_accuracy():
    """Verify Phase 26: Biometric Imputation Hook"""
    input_data = {
        "height": 180.0,
        "chest_round": 90.0,
        "waist_round": 80.0,
        "hip_round": 95.0,
        "shoulder": 40.0
    }

    # Method name is 'impute' in implementation
    predictions = imputation_service.impute("male", input_data)

    # Verify predictions were added (the original 5 + the imputed ones)
    assert len(predictions) > 5
    # Verify one of the target keys from JSON weights is present
    assert "neckcircumference" in predictions

    # Verify clinical realism
    for key, val in predictions.items():
        assert val > 0, f"Metric {key} failed clinical realism check."

def test_shape_transformer_deformation():
    """Verify Phase 48: Linear Deformation Logic"""
    # Create mock vertices (100 vertices in 3D)
    vertices = np.zeros((100, 3), dtype=np.float32)
    measurements = {"height": 180.0, "chestcircumference": 110.0}

    # Method name is 'apply_deformation'
    new_vertices = shape_transformer.apply_deformation(vertices, measurements, gender="male")

    assert new_vertices is not None
    assert new_vertices.shape == (100, 3)

def test_clinical_realism_index():
    """Verify Phase 96: Anthropomorphic Score"""
    scanned = {"height": 180.0, "chest_round": 95.0, "waist_round": 85.0}
    mesh_derived = {"height": 181.0, "chest_round": 94.0, "waist_round": 84.5}

    # Method name is 'calculate_realism_index'
    score = mesh_validator.calculate_realism_index(scanned, mesh_derived)

    assert 0.0 <= score <= 100.0

    # Method name is 'generate_accuracy_certificate'
    certificate = mesh_validator.generate_accuracy_certificate(score, scanned)
    assert "accuracy_score" in certificate
