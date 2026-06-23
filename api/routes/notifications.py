"""
Notification Routes | UNICORN SYNC Phase 5
=======================================
Handles in-app notifications.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from middleware.subscription_check import validate_subscription
from api.services.notification_service import notification_service

router = APIRouter()

def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail="Invalid subscription")
    return {'user_id': result.get('user_id'), 'api_key': x_api_key}


@router.get("/notifications")
async def get_notifications(
    limit: int = Query(20, le=50),
    unread_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """
    Get notifications for the authenticated user.
    """
    notifications = await notification_service.get_notifications(
        user_id=user['user_id'],
        limit=limit,
        unread_only=unread_only
    )
    
    return {
        "status": True,
        "notifications": notifications,
        "count": len(notifications)
    }


@router.get("/notifications/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    """
    Get count of unread notifications.
    """
    count = await notification_service.get_unread_count(user['user_id'])
    
    return {
        "status": True,
        "unread_count": count
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Mark a notification as read.
    """
    success = await notification_service.mark_as_read(notification_id, user['user_id'])
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {
        "status": True,
        "message": "Notification marked as read"
    }


@router.put("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """
    Mark all notifications as read.
    """
    success = await notification_service.mark_all_as_read(user['user_id'])
    
    return {
        "status": True,
        "message": "All notifications marked as read"
    }


@router.delete("/notifications/{notification_id}")
async def archive_notification(
    notification_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Archive a notification.
    """
    success = await notification_service.archive_notification(notification_id, user['user_id'])
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {
        "status": True,
        "message": "Notification archived"
    }
