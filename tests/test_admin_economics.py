import pytest
from api.services.admin_service import admin_service

def test_regional_price_overrides():
    """Verify Phase 143: Localized Scan Costs"""
    # Nigeria should be 1 Credit (LMIC Advantage)
    assert admin_service.get_scan_cost("NG") == 1

    # USA should be 5 Credits (Global Standard)
    assert admin_service.get_scan_cost("US") == 5

def test_master_key_handshake():
    """Verify Phase 142: Platform Security"""
    # Test valid key
    assert admin_service.validate_master_handshake("korra_platform_sovereign_2025") is True

    # Test invalid key
    assert admin_service.validate_master_handshake("wrong_key") is False

def test_currency_localization():
    """Verify Phase 144: Label Mapping"""
    assert admin_service.localize_currency_label("NG") == "NGN"
    assert admin_service.localize_currency_label("UK") == "GBP"

def test_usage_quota_alerting(caplog):
    """Verify Phase 157: Quota Threshold Warning"""
    # Default limit is 1000. 90% is 900.
    for _ in range(900):
        admin_service.track_scan_usage("DEFAULT")

    assert "QUOTA ALERT" in caplog.text
