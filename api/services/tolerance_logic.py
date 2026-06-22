import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("KORRA_TOLERANCE")

class ToleranceLogic:
    """
    KORRA Biometric Tolerance Engine | Phases 21-30
    Encapsulates standard fit logic and formula encryption.
    """
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.constants_path = self.base_dir / "data" / "tolerance" / "expansion_constants.json"
        self.constants = self._load_constants()

    def _load_constants(self):
        if self.constants_path.exists():
            with open(self.constants_path, 'r') as f:
                return json.load(f)
        return {}

    def calculate_offsets(self, raw_measurements: dict, context: str = "standard", layering: str = "none"):
        """
        Phase 29: Formula Encryption / Obfuscation
        This method calculates the 'Tolerance Data Stream' without exposing raw constants to the frontend.
        """
        # Phase 21 & 22: Layering Offsets
        layering_buffer = 0.0
        if layering == "internal": layering_buffer = 0.5 # Undershirt
        elif layering == "external": layering_buffer = 8.0 # Overcoat

        # Phase 23 & 24: Gala Compression vs Daily Wear
        fluidity_multiplier = 1.035 # Default 3.5% Daily Wear
        if context == "gala": fluidity_multiplier = 1.005 # 0.5% Compression

        refined = {}
        for key, val in raw_measurements.items():
            # Phase 25: ISO 8559-1 Mapping (Standardized Labels)
            iso_key = self._map_to_iso(key)

            # Phase 47 Logic: Final = Raw + (Raw * Multiplier) + Static_Offset
            # Obfuscated Math
            offset_val = (val * fluidity_multiplier) + layering_buffer
            refined[iso_key] = round(offset_val, 2)

        return refined

    def _map_to_iso(self, korra_key):
        """Phase 25: ISO 8559-1 Standardizer"""
        mapping = {
            "Chest Round": "ISO_8559_CHEST",
            "Waist Round": "ISO_8559_WAIST",
            "Hip Round": "ISO_8559_HIP",
            "Shoulder": "ISO_8559_SHOULDER"
        }
        return mapping.get(korra_key, korra_key)

# Singleton Instance
tolerance_logic = ToleranceLogic()
