import json
import os
import pytest
from pathlib import Path

def test_expansion_constants_integrity():
    """Phase 40: Chapter 1 Verification"""
    path = Path("./data/tolerance/expansion_constants.json")
    assert path.exists(), "Expansion constants file missing."

    with open(path, 'r') as f:
        constants = json.load(f)

    # Verify core clinical deltas
    assert constants['chest_expansion_delta'] == 4.5
    assert constants['stomach_extension_depth_sitting'] > 20.0
    assert 'agbada_volume_scalar' in constants

    # Verify Chapter 1 Completion Phase constants
    assert 'soft_tissue_bmi_scalars' in constants
    assert 'wash_day_shrinkage_buffer' in constants
    print("✅ Phase 40: Biometric Data Engineering verified.")

if __name__ == "__main__":
    test_expansion_constants_integrity()
