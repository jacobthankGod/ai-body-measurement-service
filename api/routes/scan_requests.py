"""
Scan Request Routes | UNICORN SYNC Phase 7
=====================================
Handles merchant → client re-scan requests.
"""
from fastapi import APIRouter, HTTPException, Header, Form, Depends, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import os

from middleware.subscription_check import validate_subscription
from api.services.database_service import DatabaseService
from api.services.email_service import email_service

router = APIRouter()

def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail="Invalid subscription")
    return {'user_id': result.get('user_id'), 'api_key': x_api_key}


def _generate_request_token() -> str:
    """Generate unique scan request token"""
    return uuid.uuid4().hex + uuid.uuid4().hex


@router.post("/scan-requests/create")
async def create_scan_request(
    client_email: str = Form(...),
    client_name: Optional[str] = Form(None),
    specialty: str = Form("standard"),
    message: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    Create a scan request to send to a client.
    """
    client = DatabaseService.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Database service unavailable")
    
    # Get merchant profile for name
    try:
        merchant_profile = client.table("profiles").select("full_name, company_name").eq("id", user['user_id']).single().execute()
        merchant_name = merchant_profile.data.get('company_name') or merchant_profile.data.get('full_name') or 'Your tailor'
    except:
        merchant_name = 'Your tailor'
    
    # Generate token
    token = _generate_request_token()
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    try:
        # Save to database
        result = client.table("scan_requests").insert({
            "merchant_id": user['user_id'],
            "client_email": client_email,
            "client_name": client_name,
            "request_token": token,
            "specialty": specialty,
            "message": message,
            "status": "pending",
            "expires_at": expires_at.isoformat()
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create scan request")
        
        # Send email to client
        host = os.environ.get("EXTERNAL_URL", "https://korra.work")
        scan_url = f"{host}/share?request={token}"
        
        try:
            await email_service.send_scan_request_email(
                to_email=client_email,
                client_name=client_name or "Valued Client",
                merchant_name=merchant_name,
                scan_url=scan_url,
                specialty=specialty,
                message=message
            )
        except Exception as e:
            print(f"Warning: Failed to send scan request email: {e}")
        
        return {
            "status": True,
            "message": "Scan request sent",
            "request_token": token,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scan request: {str(e)}")


@router.get("/scan-requests")
async def list_scan_requests(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    user: dict = Depends(get_current_user)
):
    """
    List scan requests for the merchant.
    """
    client = DatabaseService.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Database service unavailable")
    
    try:
        query = client.table("scan_requests").select("*").eq("merchant_id", user['user_id']).order("created_at", {"ascending": False}).limit(limit)
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        
        return {
            "status": True,
            "scan_requests": result.data or [],
            "count": len(result.data or [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scan requests: {str(e)}")


@router.get("/scan-requests/verify/{token}")
async def verify_scan_request(token: str):
    """
    Verify a scan request token (accessed by client via share link).
    """
    client = DatabaseService.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Database service unavailable")
    
    try:
        result = client.table("scan_requests").select("*").eq("request_token", token).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invalid scan request")
        
        request = result.data
        
        # Check if expired
        if request.get('status') != 'pending':
            raise HTTPException(status_code=400, detail=f"Scan request already {request.get('status')}")
        
        if datetime.fromisoformat(request['expires_at']) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Scan request has expired")
        
        # Get merchant info
        merchant = client.table("profiles").select("company_name, full_name, email").eq("id", request['merchant_id']).single().execute()
        
        return {
            "status": True,
            "valid": True,
            "merchant_id": request['merchant_id'],
            "merchant_name": merchant.data.get('company_name') or merchant.data.get('full_name') if merchant.data else 'Unknown',
            "merchant_email": merchant.data.get('email') if merchant.data else None,
            "client_name": request.get('client_name'),
            "specialty": request.get('specialty', 'standard'),
            "message": request.get('message')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify scan request: {str(e)}")


@router.put("/scan-requests/{request_id}/complete")
async def complete_scan_request(
    request_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Mark a scan request as completed (called after client completes scan).
    """
    client = DatabaseService.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Database service unavailable")
    
    try:
        client.table("scan_requests").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", request_id).eq("merchant_id", user['user_id']).execute()
        
        return {
            "status": True,
            "message": "Scan request marked as completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete scan request: {str(e)}")
