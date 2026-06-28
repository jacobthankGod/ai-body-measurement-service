"""
Notification Service | UNICORN SYNC Phase 5
=========================================
Handles in-app notifications for scan events and alerts.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger("KORRA_NOTIFICATIONS")

class NotificationService:
    """Service for managing in-app notifications"""
    
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
            logger.warning(f"NotificationService: Failed to initialize client: {e}")
    
    async def add_notification(
        self,
        user_id: str,
        notif_type: str,
        title: str,
        message: str = None,
        data: Dict[str, Any] = None,
        link_url: str = None
    ) -> Optional[str]:
        """
        Add a notification for a user.
        Returns notification ID if successful.
        """
        if not self.client:
            self._init_client()
        
        if not self.client:
            logger.error("NotificationService: No database client available")
            return None
        
        try:
            payload = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": notif_type,
                "title": title,
                "message": message,
                "data": data or {},
                "link_url": link_url,
                "is_read": False,
                "is_archived": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("client_notifications").insert(payload).execute()
            
            if result.data:
                logger.info(f"Notification sent to user {user_id}: {title}")
                return result.data[0].get("id")
            return None
            
        except Exception as e:
            logger.error(f"Failed to add notification: {e}")
            return None
    
    async def get_notifications(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return []
        
        try:
            query = self.client.table("client_notifications").select("*").eq("user_id", user_id).eq("is_archived", False).order("created_at", {"ascending": False}).limit(limit)
            
            if unread_only:
                query = query.eq("is_read", False)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return False
        
        try:
            self.client.table("client_notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return False
        
        try:
            self.client.table("client_notifications").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return False
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return 0
        
        try:
            result = self.client.table("client_notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).eq("is_archived", False).execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0
    
    async def archive_notification(self, notification_id: str, user_id: str) -> bool:
        """Archive a notification"""
        if not self.client:
            self._init_client()
        
        if not self.client:
            return False
        
        try:
            self.client.table("client_notifications").update({"is_archived": True}).eq("id", notification_id).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to archive notification: {e}")
            return False
    
    # === Convenience methods for common notifications ===
    
    async def notify_scan_completed(
        self,
        merchant_id: str,
        client_name: str,
        measurement_id: str
    ):
        """Notify merchant of completed scan"""
        return await self.add_notification(
            user_id=merchant_id,
            notif_type="scan_completed",
            title=f"New scan from {client_name}",
            message=f"Body scan completed. View measurements in your dashboard.",
            data={"measurement_id": measurement_id, "client_name": client_name},
            link_url="/dashboard#measurements"
        )
    
    async def notify_scan_request(
        self,
        client_email: str,
        merchant_name: str,
        scan_request_id: str
    ):
        """Notify client of scan request (store for when they login)"""
        # This would typically be linked to their client account
        return await self.add_notification(
            user_id=client_email,  # Would be user_id in practice
            notif_type="scan_request",
            title=f"Scan request from {merchant_name}",
            message=f"{merchant_name} has requested a new body scan.",
            data={"scan_request_id": scan_request_id},
            link_url=f"/share?request={scan_request_id}"
        )
    
    async def notify_measurement_shared(
        self,
        client_id: str,
        merchant_name: str,
        measurement_id: str
    ):
        """Notify client their measurement was shared"""
        return await self.add_notification(
            user_id=client_id,
            notif_type="measurement_shared",
            title=f"Measurement shared with {merchant_name}",
            message=f"Your measurements are now accessible by {merchant_name}.",
            data={"measurement_id": measurement_id, "merchant_name": merchant_name},
            link_url="/profile"
        )


# Singleton instance
notification_service = NotificationService()
