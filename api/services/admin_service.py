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

# Phase 143: Global Flat Pricing - $0.50 per scan (constant worldwide)
        self.regional_pricing = {
            "NG": 1, # Nigeria
            "GH": 1, # Ghana
            "KE": 1, # Kenya
            "US": 5, # USA
            "UK": 1, # United Kingdom
            "FR": 1, # France/EU
            "DEFAULT": 1  # Global constant $0.50
        }

        # Unified pricing: 1 credit = $0.50 USD worldwide
        self.UNIFIED_PRICE = 0.50  # $0.50 constant

        # Phase 146 & 157: Usage Quota & Monitoring
        self.regional_quotas = {
            "NG": 10000,
            "US": 5000,
            "DEFAULT": 1000
        }
        self.usage_stats = {} # {region: current_count}

        # Phase 148: Administrative Audit Trail
        self.audit_log = [] # List of dicts with timestamp, admin_id, and change_detail

# Phase 154: No regional tax - flat $1 everywhere
        self.regional_tax = {
            "NG": 0.0,  # No VAT
            "GH": 0.0,  # No VAT
            "UK": 0.0,  # No VAT
            "FR": 0.0,  # No VAT
            "US": 0.0,  # No VAT
            "DEFAULT": 0.0  # Flat $1 worldwide
        }

    def calculate_final_price(self, credit_amount: int, country_code: str) -> dict:
        """Phase 154: Flat $1 per scan globally - no regional variations"""
        # Constant $1 per scan regardless of region
        subtotal = credit_amount * self.UNIFIED_PRICE
        tax_amount = 0.0  # No tax
        total = subtotal  # Total = subtotal

        return {
            "subtotal": round(subtotal, 2),
            "tax_rate": "0%",
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2),
            "currency": "USD",  # Always USD
            "price_per_scan": self.UNIFIED_PRICE,
            "note": "$1 per scan - Global flat rate"
        }

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
