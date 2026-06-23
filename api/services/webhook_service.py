"""
Webhook Service | UNICORN SYNC Phase 3
====================================
Handles merchant webhook registration and delivery with retry logic.
"""
import os
import logging
import asyncio
import hmac
import hashlib
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp

logger = logging.getLogger("KORRA_WEBHOOKS")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [2, 8, 32]  # Exponential backoff in seconds

class WebhookService:
    """Service for managing webhooks"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Lazy load Supabase client"""
        try:
            from supabase import create_client
            SUPABASE_URL = os.environ.get("SUPABASE_URL")
            SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
            if SUPABASE_URL and SUPABASE_KEY:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            logger.warning(f"WebhookService: Failed to initialize client: {e}")
    
    # === Webhook Configuration ===
    
    async def register_webhook(
        self,
        merchant_id: str,
        webhook_url: str,
        events: List[str] = None,
        secret_key: str = None
    ) -> Optional[str]:
        """Register a webhook for a merchant"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            logger.error("WebhookService: No database client available")
            return None
        
        if events is None:
            events = ['scan_completed']
        
        if secret_key is None:
            secret_key = uuid.uuid4().hex + uuid.uuid4().hex
        
        try:
            payload = {
                "merchant_id": merchant_id,
                "webhook_url": webhook_url,
                "secret_key": secret_key,
                "events": events,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("webhook_configs").insert(payload).execute()
            
            if result.data:
                logger.info(f"Webhook registered for merchant {merchant_id}: {webhook_url}")
                return result.data[0].get("id")
            return None
            
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            return None
    
    async def list_webhooks(self, merchant_id: str) -> List[Dict[str, Any]]:
        """List webhooks for a merchant"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return []
        
        try:
            result = self.client.table("webhook_configs").select("*").eq("merchant_id", merchant_id).eq("is_active", True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            return []
    
    async def delete_webhook(self, webhook_id: str, merchant_id: str) -> bool:
        """Delete (deactivate) a webhook"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return False
        
        try:
            self.client.table("webhook_configs").update({"is_active": False}).eq("id", webhook_id).eq("merchant_id", merchant_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def get_active_webhooks(self, merchant_id: str) -> List[Dict[str, Any]]:
        """Get active webhooks for merchant"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return []
        
        try:
            result = self.client.table("webhook_configs").select("*").eq("merchant_id", merchant_id).eq("is_active", True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get active webhooks: {e}")
            return []
    
    # === Webhook Delivery ===
    
    def _generate_signature(self, payload: str, secret_key: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def trigger_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        secret_key: str = None,
        event_type: str = "scan_completed"
    ) -> bool:
        """Trigger a webhook with retry logic"""
        if not webhook_url:
            logger.warning("WebhookService: No webhook URL provided")
            return False
        
        payload_json = json.dumps(payload, indent=2)
        
        headers = {
            "Content-Type": "application/json",
            "X-KORRA-Event": event_type,
            "X-KORRA-Timestamp": datetime.utcnow().isoformat()
        }
        
        if secret_key:
            headers["X-KORRA-Signature"] = self._generate_signature(payload_json, secret_key)
        
        # Retry with exponential backoff
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, data=payload_json, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status >= 200 and response.status < 300:
                            logger.info(f"Webhook delivered successfully to {webhook_url}")
                            return True
                        else:
                            logger.warning(f"Webhook returned status {response.status}, attempt {attempt + 1}/{MAX_RETRIES}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Webhook timeout, attempt {attempt + 1}/{MAX_RETRIES}")
            except Exception as e:
                logger.warning(f"Webhook delivery error: {e}, attempt {attempt + 1}/{MAX_RETRIES}")
            
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying webhook in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"Webhook delivery failed after {MAX_RETRIES} attempts: {webhook_url}")
        return False
    
    async def notify_scan_completed(
        self,
        merchant_id: str,
        measurement_data: Dict[str, Any]
    ):
        """Notify all merchant webhooks of completed scan"""
        webhooks = await self.get_active_webhooks(merchant_id)
        
        if not webhooks:
            logger.info(f"No active webhooks for merchant {merchant_id}")
            return
        
        # Build webhook payload
        payload = {
            "event": "scan_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "measurement_id": measurement_data.get("id"),
                "client_name": measurement_data.get("client_name"),
                "biometrics": measurement_data.get("biometrics"),
                "body_shape": measurement_data.get("body_shape"),
                "size_recommendation": measurement_data.get("size_recommendation"),
                "mesh_url": measurement_data.get("mesh_url")
            }
        }
        
        # Trigger all webhooks
        for webhook in webhooks:
            if 'scan_completed' in webhook.get('events', []):
                await self.trigger_webhook(
                    webhook_url=webhook['webhook_url'],
                    payload=payload,
                    secret_key=webhook.get('secret_key'),
                    event_type="scan_completed"
                )


# Singleton instance
webhook_service = WebhookService()
