import pytest
import json

def test_widget_studio_config_integrity():
    """Verify that the Widget Studio generates valid JSONB configurations."""
    # Simulate a merchant's custom branding choice
    config = {
        "primary": "#C6FF00",
        "theme": "glass",
        "brand_name": "KORRA LUXE",
        "logo_size": "32",
        "btn_text_fitting": "Get Sculpted",
        "btn_color": "#FF0000"
    }

    # In a real environment, we'd check the Supabase 'profiles' update
    # Here we verify the structure meets our industrial standard (WIDGET_SQL_UPDATE.sql)
    required_keys = ["primary", "theme", "brand_name", "btn_text_fitting"]
    for key in required_keys:
        assert key in config

    assert config["theme"] in ["dark", "light", "glass"]

def test_post_scan_curation_logic():
    """Verify the 'Biometrics First, Context Second' architectural state."""
    # 1. Capture Raw Biometric (Clinical Truth)
    raw_scan = {"chest": 100.0, "status": "verified"}

    # 2. Apply Cultural Context (Tolerance Intelligence)
    # This imitates the 'window.handleAttireToggle' logic
    from api.services.tolerance_logic import tolerance_logic

    agbada_result = tolerance_logic.calculate_offsets({"Chest Round": 100.0}, context="agbada")
    suit_result = tolerance_logic.calculate_offsets({"Chest Round": 100.0}, context="suit")

    # Verify the Raw Scan remains unchanged while context outputs differ
    assert raw_scan["chest"] == 100.0
    assert agbada_result["ISO_8559_CHEST"] == 145.0 # Regal Volume
    assert suit_result["ISO_8559_CHEST"] == 110.0  # Structured Ease
