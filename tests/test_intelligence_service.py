import pytest
from api.services.intelligence_service import intelligence_service

def test_regional_localization_bias():
    """Verify Phase 81-89: Regional Multipliers"""
    raw_measurements = {"ISO_8559_CHEST": 100.0}

    # West Africa: Lagos Grand (1.4x regional bias)
    result_wa = intelligence_service.get_localized_offsets(raw_measurements, "WEST_AFRICA", "agbada")
    assert result_wa["region_label"] == "Lagos Grand"
    # Logic applies regional_bias on top of attire_multiplier
    # If agbada base is 1.45, then 145 * 1.4 = 203.0
    assert result_wa["refined_measurements"]["ISO_8559_CHEST"] == 203.0

def test_multilingual_labels():
    """Verify Phase 91-94: Hausa, Swahili, Amharic"""
    # Test Hausa
    result_ha = intelligence_service.get_localized_offsets({}, "WEST_AFRICA", "standard", lang="ha")
    assert result_ha["labels"]["ease"] == "Hutu"

    # Test Swahili
    result_sw = intelligence_service.get_localized_offsets({}, "EAST_AFRICA", "standard", lang="sw")
    assert result_sw["labels"]["accuracy"] == "Usahihi"

def test_african_fit_certification():
    """Verify Phase 96: Automated Badging"""
    # African region should be certified
    result_wa = intelligence_service.get_localized_offsets({}, "WEST_AFRICA", "standard")
    assert result_wa["certified_african_fit"] is True

    # European region should NOT be certified
    result_eu = intelligence_service.get_localized_offsets({}, "EUROPE", "standard")
    assert result_eu["certified_african_fit"] is False

def test_sustainability_impact_calc():
    """Verify Phase 99: Fabric Waste Reduction metrics"""
    result = intelligence_service.get_localized_offsets({}, "WEST_AFRICA", "standard")
    assert result["sustainability_impact"]["fabric_waste_reduction"] == "90%"
