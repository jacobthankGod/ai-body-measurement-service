import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("KORRA_TOLERANCE")

class ToleranceLogic:
    """
    KORRA Biometric Tolerance Engine | Phases 21-50
    Encapsulates standard fit logic and persistent attire contexts.
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
        Phase 81-89: Regional Fine-Tuning
        """
        # Phase 21 & 22: Layering Offsets
        layering_buffer = 0.0
        if layering == "internal": layering_buffer = 0.5 # Undershirt
        elif layering == "external": layering_buffer = 8.0 # Overcoat

        # Phase 23 & 24: Gala Compression vs Daily Wear
        fluidity_multiplier = 1.035 # Default 3.5% Daily Wear
        if context == "gala": fluidity_multiplier = 1.005 # 0.5% Compression

        # Chapter 3: Specific Archetype Multipliers (Phase 81-89)
        if "agbada" in context: fluidity_multiplier = 1.45
        elif "kanzu" in context: fluidity_multiplier = 1.25
        elif "djellaba" in context: fluidity_multiplier = 1.3
        elif "qipao" in context: fluidity_multiplier = 1.02 # Minimal ease
        elif "suit" in context: fluidity_multiplier = 1.1

        refined = {}
        for key, val in raw_measurements.items():
            # Phase 25: ISO 8559-1 Mapping (Standardized Labels)
            iso_key = self._map_to_iso(key)

            # Obfuscated Math
            offset_val = (val * fluidity_multiplier) + layering_buffer
            refined[iso_key] = round(offset_val, 2)

        return refined

    def calculate_tolerance(self, raw_val: float, multiplier: float, static_offset: float, group: str = "chest"):
        """
        Phase 47: The Tolerance Scalar
        Phase 53: Negative Ease (Activewear)
        """
        # Phase 49: Volume Guard Integration
        safe_multiplier = min(multiplier, 1.8)
        # Phase 53: Negative ease for compression wear
        if multiplier < 1.0:
            safe_multiplier = max(multiplier, 0.8) # Min 20% compression

        # Phase 52: Abaya/Etibo static offsets
        final = raw_val * safe_multiplier + static_offset
        return round(final, 2)

    def process_full_attire(self, raw_measurements: dict, multipliers: dict, offsets: dict, gender: str = "male"):
        """
        Phase 48: Multi-Measurement Sync
        Ensures a change in 'Chest' ease doesn't break 'Shoulder' alignment.
        """
        refined = {}
        # Phase 50: Gender-Logic Sharding
        is_female = gender.lower() == 'female'
        chest_key = "Bust Round" if is_female else "Chest Round"

        for key, val in raw_measurements.items():
            # Get specific multiplier for this body part, fallback to base
            m = multipliers.get(key.lower().replace(' ', '_'), 0.05) # Default 5% ease
            o = offsets.get(key.lower().replace(' ', '_'), 0.0)

            # Phase 48: Sync shoulder to chest expansion
            if key == "Shoulder" and chest_key in raw_measurements:
                # Shoulder ease is proportionally linked to chest volume (30% ratio)
                m = m + (multipliers.get(chest_key.lower().replace(' ', '_'), 0) * 0.3)

            refined[key] = self.calculate_tolerance(val, m, o, key)

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
