import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger("KORRA_ADMIN")

class AdminService:
    """
    KORRA Admin Service | Chapter 5: Economic Logic (Phases 141-150)
    Handles regional pricing, master keys, and currency localization.
    """
    def __init__(self):
        # Phase 142: Platform Master Key
        self.master_secret = os.environ.get("KORRA_MASTER_SECRET", "korra_platform_sovereign_2025")

        # Phase 143: Regional Price Override Map (Credits per Scan)
        self.regional_pricing = {
            "NG": 1, # Nigeria (1 Credit = ~500 NGN)
            "GH": 1, # Ghana
            "KE": 1, # Kenya
            "US": 5, # USA (5 Credits = ~$2.50)
            "UK": 5, # United Kingdom
            "FR": 4, # France/EU
            "DEFAULT": 3
        }

    def get_scan_cost(self, country_code: str) -> int:
        """Calculates localized credit cost for a scan."""
        return self.regional_pricing.get(country_code.upper(), self.regional_pricing["DEFAULT"])

    def validate_master_handshake(self, incoming_key: str) -> bool:
        """Phase 142: Secure handshake for industrial data streams."""
        return incoming_key == self.master_secret

    def localize_currency_label(self, country_code: str) -> str:
        """Phase 144: Currency Localization mapping."""
        mapping = {
            "NG": "NGN", "GH": "GHS", "KE": "KES",
            "US": "USD", "UK": "GBP", "FR": "EUR"
        }
        return mapping.get(country_code.upper(), "USD")

# Singleton
admin_service = AdminService()
