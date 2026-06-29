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
        elif "kurta" in context: fluidity_multiplier = 1.25
        elif "kaftan" in context: fluidity_multiplier = 1.2
        elif "senator" in context: fluidity_multiplier = 1.1
        elif "abaya" in context: fluidity_multiplier = 1.0
        elif "activewear" in context: fluidity_multiplier = 0.95
        elif "swimwear" in context: fluidity_multiplier = 0.9
        elif "streetwear" in context: fluidity_multiplier = 1.2
        elif "inuit_parka" in context: fluidity_multiplier = 1.3
        elif "native_regalia" in context: fluidity_multiplier = 1.2
        elif "cowboy" in context: fluidity_multiplier = 1.1
        elif "hawaiian" in context: fluidity_multiplier = 1.1
        elif "letterman" in context: fluidity_multiplier = 1.12
        elif "maori_korowai" in context: fluidity_multiplier = 1.0
        elif "piupiu" in context: fluidity_multiplier = 1.05
        elif "sulu_lavalava" in context: fluidity_multiplier = 1.15
        elif "driza_bone" in context: fluidity_multiplier = 1.0
        elif "bush_shirt" in context: fluidity_multiplier = 1.1
        elif "grass_skirt" in context: fluidity_multiplier = 1.05
        elif "lehenga" in context: fluidity_multiplier = 1.15
        elif "anarkali" in context: fluidity_multiplier = 1.12
        elif "dhoti" in context: fluidity_multiplier = 1.1
        elif "turban" in context: fluidity_multiplier = 1.0
        elif "barong_tagalog" in context: fluidity_multiplier = 1.08
        elif "longyi" in context: fluidity_multiplier = 1.1
        elif "sinh" in context: fluidity_multiplier = 1.05
        elif "baju_melayu" in context: fluidity_multiplier = 1.12
        elif "dirndl" in context: fluidity_multiplier = 1.1
        elif "lederhosen" in context: fluidity_multiplier = 1.08
        elif "flamenco" in context: fluidity_multiplier = 1.05
        elif "foustanella" in context: fluidity_multiplier = 1.2
        elif "sarafan" in context: fluidity_multiplier = 1.15
        elif "bunad" in context: fluidity_multiplier = 1.1
        elif "vyshyvanka" in context: fluidity_multiplier = 1.15
        elif "aran_sweater" in context: fluidity_multiplier = 1.15
        elif "smock_frock" in context: fluidity_multiplier = 1.2
        elif "tweed_suit" in context: fluidity_multiplier = 1.1
        elif "morning_tails" in context: fluidity_multiplier = 1.06
        elif "mariniere" in context: fluidity_multiplier = 1.02
        elif "bisht" in context: fluidity_multiplier = 1.0
        elif "kufiya" in context: fluidity_multiplier = 1.0
        elif "fez_tarboosh" in context: fluidity_multiplier = 1.0
        elif "chador" in context: fluidity_multiplier = 1.0
        elif "jilbab" in context: fluidity_multiplier = 1.0
        elif "huipil" in context: fluidity_multiplier = 1.15
        elif "poncho" in context: fluidity_multiplier = 1.0
        elif "sombrero_charro" in context: fluidity_multiplier = 1.15
        elif "pollera" in context: fluidity_multiplier = 1.3
        elif "rebozo" in context: fluidity_multiplier = 1.0
        elif "ruana" in context: fluidity_multiplier = 1.0
        elif "faso_dan_fani" in context: fluidity_multiplier = 1.15
        elif "kitenge" in context: fluidity_multiplier = 1.1
        elif "kuba" in context: fluidity_multiplier = 1.1
        elif "tuxedo" in context: fluidity_multiplier = 1.06
        elif "denim" in context: fluidity_multiplier = 1.03

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

        # If multiplier is factor-based (e.g. 1.6), apply raw * m
        # If multiplier is ease-based (e.g. 0.05), apply raw * (1+m)
        if safe_multiplier > 0.5:
            calc_m = safe_multiplier
        else:
            calc_m = 1.0 + safe_multiplier

        final = (raw_val * calc_m) + static_offset
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
        chest_std_key = chest_key.lower().replace(' ', '_')

        # Fix: Extract raw chest ease for sync BEFORE the loop
        # The multipliers dict is expected to contain keys like 'chest_round'
        chest_m = multipliers.get(chest_std_key, 0.0)

        for key, val in raw_measurements.items():
            std_key = key.lower().replace(' ', '_')

            # Get specific multiplier
            m = multipliers.get(std_key, 0.05)
            o = offsets.get(std_key, 0.0)

            # Phase 48: Sync shoulder to chest expansion
            if std_key == "shoulder":
                # Shoulder ease is proportionally linked to chest volume (30% ratio)
                m = m + (chest_m * 0.3)

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
