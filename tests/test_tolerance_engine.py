import pytest
from api.services.tolerance_logic import tolerance_logic

def test_tolerance_scalar_math():
    """Verify Phase 47: Final = Raw * Multiplier + Static_Offset"""
    # Test Standard Fit (Default 3.5% ease)
    raw_chest = 100.0
    result = tolerance_logic.calculate_offsets({"Chest Round": raw_chest}, context="standard")
    assert result["ISO_8559_CHEST"] == 103.5

def test_agbada_extreme_volume():
    """Verify Phase 5: Agbada 1.45x multiplier"""
    raw_chest = 100.0
    result = tolerance_logic.calculate_offsets({"Chest Round": raw_chest}, context="agbada")
    assert result["ISO_8559_CHEST"] == 145.0

def test_activewear_negative_ease():
    """Verify Phase 53: Compression wear logic"""
    raw_val = 100.0
    multiplier = 0.9 # Factor based (> 0.5)
    result = tolerance_logic.calculate_tolerance(raw_val, multiplier, 0.0)
    assert result == 90.0

    # Test Volume Guard Floor (Lower values treated as ease-based)
    # multiplier 0.1 is ease-based -> 1 + 0.1 = 1.1 -> final = 110
    result_ease = tolerance_logic.calculate_tolerance(raw_val, 0.1, 0.0)
    assert result_ease == 110.0

def test_static_drape_offsets():
    """Verify Phase 52: Abaya/Burnous static additions"""
    raw_val = 100.0
    multiplier = 1.0 # Factor based
    static_offset = 15.0 # Abaya standard
    result = tolerance_logic.calculate_tolerance(raw_val, multiplier, static_offset)
    assert result == 115.0

def test_multi_measurement_sync():
    """Verify Phase 48: Skeletal alignment (Shoulder linked to Chest)"""
    raw_data = {"Chest Round": 100.0, "Shoulder": 40.0}
    # multipliers dict keys must be lowercase and underscored
    multipliers = {"chest_round": 0.45, "shoulder": 0.05}
    result = tolerance_logic.process_full_attire(raw_data, multipliers, {}, gender="male")

    # chest_m = 0.45
    # shoulder base_m = 0.05
    # synced_m = 0.05 + (0.45 * 0.3) = 0.185
    # Since 0.185 <= 0.5, it's ease-based: calc_m = 1.185
    # final = 40 * 1.185 = 47.4
    assert result["Shoulder"] == 47.4
