import logging
import json
from typing import List, Dict, Optional
from pathlib import Path
from api.services.tolerance_logic import tolerance_logic

logger = logging.getLogger("KORRA_INTELLIGENCE")

class IntelligenceService:
    """
    KORRA Intelligence Service | Phases 81-120
    Handles global scaling, regional localization, and LMIC hardening.
    """
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.regional_data_path = self.base_dir / "data" / "tolerance" / "regional_localization.json"
        self._load_regional_data()

    def _load_regional_data(self):
        # Phase 81-89: Regional Localization Constants
        self.regional_offsets = {
            "WEST_AFRICA": {"base_multiplier": 1.4, "name": "Lagos Grand"},
            "EAST_AFRICA": {"base_multiplier": 1.2, "name": "Nairobi Swahili"},
            "NORTH_AFRICA": {"base_multiplier": 1.3, "name": "Maghreb Caftan"},
            "SOUTH_AFRICA": {"base_multiplier": 1.1, "name": "Jo'burg Structured"},
            "CENTRAL_AFRICA": {"base_multiplier": 1.25, "name": "Bamenda Toghu"},
            "ASIA": {"base_multiplier": 1.05, "name": "Sherwani Precision"},
            "EUROPE": {"base_multiplier": 1.08, "name": "Savile Row Classic"},
            "LATIN_AMERICA": {"base_multiplier": 1.12, "name": "Guayabera Airflow"},
            "ANDEAN": {"base_multiplier": 1.15, "name": "Poncho Span"}
        }

    def get_localized_offsets(self, raw_measurements: dict, region: str, attire_name: str):
        """
        Phase 81-89: Core Regional Calculation Logic
        """
        region_key = region.upper().replace(' ', '_')
        region_bias = self.regional_offsets.get(region_key, {"base_multiplier": 1.0})

        # Phase 90: LMIC Device Hardening (Optimized payload)
        # We strip unnecessary metadata for low-bandwidth zones
        refined = tolerance_logic.calculate_offsets(raw_measurements, context=attire_name.lower())

        # Apply regional bias multiplier
        for key in refined:
            refined[key] = round(refined[key] * region_bias['base_multiplier'], 2)

        return {
            "region_label": region_bias.get("name", "Standard"),
            "refined_measurements": refined
        }

# Singleton
intelligence_service = IntelligenceService()
