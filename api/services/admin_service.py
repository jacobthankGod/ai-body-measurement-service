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

        # Phase 146 & 157: Usage Quota & Monitoring
        self.regional_quotas = {
            "NG": 10000,
            "US": 5000,
            "DEFAULT": 1000
        }
        self.usage_stats = {} # {region: current_count}

        # Phase 147: Algorithm Weight Overrides
        # Allows real-time tuning of multipliers without code changes
        self.weight_overrides = {} # {attire_id: {measurement: override_val}}

        # Phase 148: Administrative Audit Trail
        self.audit_log = [] # List of dicts with timestamp, admin_id, and change_detail

    def log_audit(self, admin_id: str, action: str, details: dict):
        """Phase 148: Record administrative actions for transparency."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "admin_id": admin_id,
            "action": action,
            "details": details
        }
        self.audit_log.append(entry)
        logger.info(f"🛡️ Audit: {action} by {admin_id}")

    def apply_weight_override(self, admin_id: str, attire_id: str, measurement: str, value: float):
        """Phase 147: Dynamic adjustment of fit formulas."""
        if attire_id not in self.weight_overrides:
            self.weight_overrides[attire_id] = {}

        self.weight_overrides[attire_id][measurement] = value
        self.log_audit(admin_id, "WEIGHT_OVERRIDE", {"attire": attire_id, "measure": measurement, "val": value})

    def track_scan_usage(self, country_code: str):
        """Phase 146: Monitor regional scan volume."""
        cc = country_code.upper()
        self.usage_stats[cc] = self.usage_stats.get(cc, 0) + 1

        # Phase 157: Quota Alerting
        current = self.usage_stats[cc]
        limit = self.regional_quotas.get(cc, self.regional_quotas["DEFAULT"])
        if current >= limit * 0.9: # 90% threshold
            logger.warning(f"⚠️ QUOTA ALERT: {cc} has reached {current}/{limit} scans.")

    def bulk_allocate_credits(self, admin_id: str, merchant_id: str, amount: int):
        """Phase 152: Administrative credit injection."""
        # This would interface with the database in a real scenario
        self.log_audit(admin_id, "CREDIT_ALLOCATION", {"merchant": merchant_id, "amount": amount})
        return True

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
