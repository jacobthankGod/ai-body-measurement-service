"""
Webhook Routes | UNICORN SYNC Phase 3
=================================
Handles webhook registration and management.
"""
from fastapi import APIRouter, HTTPException, Header, Form, Depends
from typing import List, Optional
from pydantic import BaseModel

from middleware.subscription_check import validate_subscription
from api.services.webhook_service import webhook_service

router = APIRouter()

# Request models
class WebhookRegisterRequest(BaseModel):
    webhook_url: str
    events: List[str] = ['scan_completed']
    secret_key: Optional[str] = None

class WebhookResponse(BaseModel):
    id: str
    webhook_url: str
    events: List[str]
    is_active: bool

def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail="Invalid subscription")
    return {'user_id': result.get('user_id'), 'api_key': x_api_key}


@router.post("/webhooks/register")
async def register_webhook(
    request: WebhookRegisterRequest,
    user: dict = Depends(get_current_user)
):
    """
    Register a webhook URL for receiving scan notifications.
    """
    webhook_id = await webhook_service.register_webhook(
        merchant_id=user['user_id'],
        webhook_url=request.webhook_url,
        events=request.events,
        secret_key=request.secret_key
    )
    
    if not webhook_id:
        raise HTTPException(status_code=500, detail="Failed to register webhook")
    
    return {
        "status": True,
        "message": "Webhook registered successfully",
        "webhook_id": webhook_id
    }


@router.get("/webhooks")
async def list_webhooks(user: dict = Depends(get_current_user)):
    """
    List all webhooks for the authenticated user.
    """
    webhooks = await webhook_service.list_webhooks(user['user_id'])
    
    return {
        "status": True,
        "webhooks": [
            {
                "id": w["id"],
                "webhook_url": w["webhook_url"],
                "events": w.get("events", []),
                "is_active": w.get("is_active", True),
                "created_at": w.get("created_at")
            }
            for w in webhooks
        ]
    }


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete (deactivate) a webhook.
    """
    success = await webhook_service.delete_webhook(webhook_id, user['user_id'])
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {
        "status": True,
        "message": "Webhook deleted"
    }


@router.post("/webhooks/test")
async def test_webhook(
    webhook_url: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """
    Test a webhook URL by sending a sample payload.
    """
    import uuid
    test_payload = {
        "event": "test",
        "timestamp": "2026-01-01T00:00:00Z",
        "data": {
            "measurement_id": str(uuid.uuid4()),
            "client_name": "Test Client",
            "biometrics": {"Chest Round": 100, "Waist Round": 80},
            "body_shape": "Athletic",
            "size_recommendation": "M"
        }
    }
    
    success = await webhook_service.trigger_webhook(
        webhook_url=webhook_url,
        payload=test_payload,
        event_type="test"
    )
    
    return {
        "status": success,
        "message": "Test webhook " + ("delivered" if success else "failed")
    }
