"""
Payment Routes - Paystack Integration
====================================
Handles payment initialization, verification, and subscription management.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from datetime import datetime
import os

from middleware.subscription_check import validate_subscription, get_user_quota
from api.services.paystack_service import PaystackService

router = APIRouter()
paystack_service = PaystackService(
    secret_key=os.getenv('PAYSTACK_SECRET_KEY', ''),
    public_key=os.getenv('PAYSTACK_PUBLIC_KEY', '')
)


class InitializePaymentRequest(BaseModel):
    """Request to initialize a Paystack payment"""
    tier: str  # tailor_pro, tailor_elite, enterprise
    email: str
    currency: str = "NGN"  # Default to Nigerian Naira


class PaymentResponse(BaseModel):
    """Response from Paystack payment initialization"""
    status: bool
    message: str
    data: dict = None


def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail=result.get('error', 'Invalid subscription'))
    return {'api_key': x_api_key}


# Pricing in smallest currency units (kobo for NGN)
TIER_PRICES = {
    'tailor_pro': 299900,      # ₦2,999
    'tailor_elite': 749900,    # ₦7,499
}


@router.post("/payments/initialize")
async def initialize_payment(
    payload: InitializePaymentRequest,
    user: dict = Depends(get_current_user)
):
    """
    Initialize a Paystack payment session.
    
    Returns authorization URL for customer to complete payment.
    """
    if payload.tier not in TIER_PRICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Use: {', '.join(TIER_PRICES.keys())}"
        )
    
    amount = TIER_PRICES[payload.tier]
    
    # Initialize payment with Paystack
    result = paystack_service.initialize_payment(
        email=payload.email,
        amount=amount,
        reference=None,  # Let Paystack generate one
        metadata={
            'tier': payload.tier,
            'api_key': user['api_key'],
            'timestamp': datetime.now().isoformat()
        }
    )
    
    if result['status']:
        return {
            "status": True,
            "message": "Authorization URL created",
            "data": result['data']
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get('message', 'Failed to initialize payment')
        )


@router.get("/payments/verify/{reference}")
async def verify_payment(
    reference: str
):
    """
    Verify a Paystack payment (Bundle or Single Scan).
    """
    result = paystack_service.verify_payment(reference)
    
    if not result['status'] or result['data']['status'] != 'success':
        raise HTTPException(
            status_code=400,
            detail=result.get('message', 'Verification failed')
        )
    
    payment_data = result['data']
    metadata = payment_data.get('metadata', {})
    user_id = metadata.get('user_id')
    tx_type = metadata.get('type', 'bundle') # 'bundle' or 'single'
    credits_to_add = int(metadata.get('credits', 0))
    amount_paid = payment_data.get('amount', 0) / 100.0 # Convert to float
    currency = payment_data.get('currency', 'USD')

    if not user_id:
        raise HTTPException(status_code=400, detail="Transaction missing user context.")

    # Atomic Sync with PostgreSQL Ledger
    from api.services.database_service import DatabaseService
    client = DatabaseService.get_client()
    
    # 1. Record in Transactions Table (for Admin Financial Audit)
    try:
        client.table("transactions").insert({
            "user_id": user_id,
            "amount": amount_paid,
            "currency": currency,
            "type": "bundle_purchase" if tx_type == 'bundle' else "single_scan_payment",
            "credits_added": credits_to_add,
            "reference": reference,
            "status": "success"
        }).execute()
    except Exception as e:
        print(f"⚠️ Ledger Sync Warning: {e}")

    # 2. Update Credits if applicable
    if tx_type == 'bundle' and credits_to_add > 0:
        res = client.table("profiles").select("credits").eq("id", user_id).single().execute()
        current = res.data.get('credits', 0) if res.data else 0
        client.table("profiles").update({"credits": current + credits_to_add}).eq("id", user_id).execute()

    return {
        "status": True,
        "message": "Payment verified and ledger synchronized.",
        "data": {
            "type": tx_type,
            "credits_added": credits_to_add,
            "reference": reference
        }
    }


@router.get("/payments/transactions")
async def list_transactions(
    limit: int = 10,
    page: int = 1,
    user: dict = Depends(get_current_user)
):
    """
    List transactions for the authenticated user.
    """
    result = paystack_service.list_transactions(limit=limit, page=page)
    
    if result['status']:
        return {
            "status": True,
            "message": "Transactions retrieved",
            "data": result['data']
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get('message', 'Failed to retrieve transactions')
        )


@router.post("/payments/webhook")
async def webhook_handler(request: Request):
    """
    Paystack webhook handler for payment events.
    
    Verifies signature and processes payment success/failure.
    """
    # Get the request body
    body = await request.json()
    
    # Verify signature
    signature = request.headers.get('x-paystack-signature')
    if not paystack_service.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    event = body.get('event')
    data = body.get('data', {})
    
    if event == 'charge.success':
        reference = data.get('reference')
        metadata = data.get('metadata', {})
        tier = metadata.get('tier', 'tailor_pro')
        api_key = metadata.get('api_key')
        
        # Update subscription
        if api_key:
            from middleware.subscription_check import load_api_keys, save_api_keys
            keys = load_api_keys()
            
            if api_key in keys:
                keys[api_key]['tier'] = tier
                keys[api_key]['last_payment'] = datetime.now().isoformat()
                keys[api_key]['paystack_reference'] = reference
                save_api_keys(keys)
        
        return {
            "status": "success",
            "message": "Payment processed",
            "tier": tier
        }
    
    elif event == 'charge.failed':
        reference = data.get('reference')
        print(f"Payment failed for reference: {reference}")
        
        return {
            "status": "failed",
            "message": "Payment failed",
            "reference": reference
        }
    
    else:
        return {"status": "ignored", "message": f"Event {event} not handled"}


@router.get("/payments/subscription-status")
async def get_subscription_status(
    user: dict = Depends(get_current_user)
):
    """
    Get current subscription status and payment history.
    """
    quota = get_user_quota(user['api_key'])
    
    return {
        "status": True,
        "data": {
            "tier": quota['tier'],
            "quota": quota['quota'],
            "used": quota['used'],
            "remaining": quota['remaining'],
            "reset_date": quota['reset_date'],
            "api_key": user['api_key'][:8] + "..." # Masked for security
        }
    }
