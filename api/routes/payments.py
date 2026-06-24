"""
Payment Routes - Paystack Integration
====================================
Handles payment initialization, verification, and subscription management.
Including: localized pricing, VAT calculation, invoice generation.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Request, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
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


# Currency setting (NGN = always supported by Paystack; USD requires enabling in dashboard)
PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'NGN')

# Per-scan price in the configured currency's major unit (e.g. USD or NGN)
# For NGN: 300 means ₦300/scan; for USD: 0.50 means $0.50/scan
SCAN_PRICE = float(os.getenv('SCAN_PRICE', '300'))

# Paystack amounts in minor units (cents for USD, kobo for NGN)
TIER_PRICES = {
    'tailor_pro': int(SCAN_PRICE * 100),        # X kobo/cents per scan
    'tailor_elite': int(SCAN_PRICE * 100),
    'enterprise': int(SCAN_PRICE * 100)
}

# Display label for price
SCAN_PRICE_LABEL = f"{SCAN_PRICE:.0f}" if SCAN_PRICE == int(SCAN_PRICE) else f"{SCAN_PRICE:.2f}"


@router.post("/payments/initialize")
async def initialize_payment(
    payload: InitializePaymentRequest,
    user: dict = Depends(get_current_user)
):
    """
    Initialize a Paystack payment session - Global flat $1 per scan.
    Returns authorization URL for customer to complete payment.
    """
    if payload.tier not in TIER_PRICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Use: {', '.join(TIER_PRICES.keys())}"
        )
    
    # Use flat $1 rate - same for all tiers and regions
    amount = TIER_PRICES[payload.tier]
    
    # Initialize payment with Paystack
    callback_url = os.getenv('PAYSTACK_CALLBACK_URL')
    result = paystack_service.initialize_payment(
        email=payload.email,
        amount=amount,
        currency=PAYMENT_CURRENCY,
        reference=None,  # Let Paystack generate one
        callback_url=callback_url,
        metadata={
            'tier': payload.tier,
            'api_key': user['api_key'],
            'price_per_scan': SCAN_PRICE,
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


# ==========================================
# PUBLIC CONFIG ENDPOINT
# ==========================================

@router.get("/config")
async def get_public_config():
    """
    Return public configuration for frontend - includes Paystack public key.
    This endpoint is intentionally public (no auth required) as it only exposes safe config.
    """
    return {
        "status": True,
        "data": {
            "paystack_public_key": os.getenv('PAYSTACK_PUBLIC_KEY', ''),
            "environment": os.getenv('ENVIRONMENT', 'production'),
            "flat_rate_usd": SCAN_PRICE if PAYMENT_CURRENCY == 'USD' else SCAN_PRICE,
            "currency": PAYMENT_CURRENCY,
            "scan_price": SCAN_PRICE,
            "scan_price_label": SCAN_PRICE_LABEL
        }
    }


# ==========================================
# BILLING 100% IMPLEMENTATION ENDPOINTS
# ==========================================

class LocalizedPriceRequest(BaseModel):
    """Request for localized price calculation"""
    credit_amount: int
    country_code: str = "NG"


@router.post("/payments/calculate-final")
async def calculate_final_price(
    payload: LocalizedPriceRequest,
    user: dict = Depends(get_current_user)
):
    """
    Calculate final price with regional VAT/tax for a country.
    Returns itemized receipt for transparency.
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    country_code = payload.country_code.upper()
    
    # Get localized pricing from database
    result = client.table("localized_pricing").select(
        "currency, currency_symbol, credits_per_scan, unit_price_smallest, vat_rate"
    ).eq("country_code", country_code).eq("is_active", True).execute()
    
    if not result.data:
        # Fallback to default pricing
        result = client.table("localized_pricing").select(
            "currency, currency_symbol, credits_per_scan, unit_price_smallest, vat_rate"
        ).eq("country_code", "NG").execute()
        country_code = "NG"
    
    pricing = result.data[0]
    credit_amount = payload.credit_amount
    
    # Calculate amounts
    subtotal = pricing["unit_price_smallest"] * credit_amount
    vat_rate = pricing["vat_rate"]
    tax_amount = int(subtotal * vat_rate)
    total = subtotal + tax_amount
    
    # Build line items
    line_items = [
        {
            "description": f"{credit_amount} Scan Credits",
            "quantity": credit_amount,
            "unit_price": pricing["unit_price_smallest"],
            "credits": credit_amount * pricing["credits_per_scan"],
            "amount": subtotal
        }
    ]
    
    if tax_amount > 0:
        line_items.append({
            "description": f"VAT ({int(vat_rate * 100)}%)",
            "amount": tax_amount,
            "rate": vat_rate
        })
    
    return {
        "status": True,
        "data": {
            "region": country_code,
            "country_code": country_code,
            "currency": pricing["currency"],
            "currency_symbol": pricing["currency_symbol"],
            "credits_per_scan": pricing["credits_per_scan"],
            "bundle_size": credit_amount,
            "total_credits": credit_amount * pricing["credits_per_scan"],
            "line_items": line_items,
            "subtotal": subtotal,
            "vat_rate": f"{vat_rate * 100}%",
            "tax_amount": tax_amount,
            "total": total,
            "vat_included": tax_amount > 0
        }
    }


@router.get("/payments/localized-price")
async def get_localized_price(
    country_code: str = Query("NG", description="2-letter country code"),
    user: dict = Depends(get_current_user)
):
    """
    Get current pricing for a country (for real-time display updates).
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    cc = country_code.upper()
    
    result = client.table("localized_pricing").select("*").eq("country_code", cc).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Pricing not found for {country_code}")
    
    pricing = result.data[0]
    
    return {
        "status": True,
        "data": {
            "country_code": pricing["country_code"],
            "country_name": pricing["country_name"],
            "currency": pricing["currency"],
            "currency_symbol": pricing["currency_symbol"],
            "credits_per_scan": pricing["credits_per_scan"],
            "price_per_credit": pricing["unit_price_smallest"],
            "vat_rate": f"{pricing['vat_rate'] * 100}%",
            "is_active": pricing["is_active"]
        }
    }


@router.get("/invoices")
async def list_invoices(
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    List all invoices for the authenticated user with full details.
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    result = client.table("invoices").select(
        "id, amount_paid, currency, paystack_reference, plan_id, paid_at, "
        "subtotal, tax_amount, tax_rate, credits_purchased, billing_country"
    ).eq("user_id", user_id).order("paid_at", {"ascending": False}).limit(limit).offset(offset).execute()
    
    return {
        "status": True,
        "data": {
            "invoices": result.data,
            "count": len(result.data),
            "has_more": len(result.data) == limit
        }
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get detailed invoice with full breakdown.
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    result = client.table("invoices").select("*").eq("id", invoice_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = result.data
    
    if invoice["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "status": True,
        "data": invoice
    }


@router.get("/invoices/{invoice_id}/download")
async def download_invoice_pdf(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Generate and return a PDF invoice for the user.
    """
    from api.services.database_service import DatabaseService
    from api.services.invoice_generator import generate_invoice_pdf
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    # Fetch invoice
    result = client.table("invoices").select("*").eq("id", invoice_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = result.data
    
    if invoice["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate PDF
    pdf_url = await generate_invoice_pdf(invoice, client)
    
    return {
        "status": True,
        "data": {
            "invoice_id": invoice_id,
            "pdf_url": pdf_url
        }
    }


@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    new_plan_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Upgrade to a higher subscription plan.
    """
    from api.services.database_service import DatabaseService
    
    valid_plans = ['basic', 'pro', 'elite', 'enterprise']
    if new_plan_id not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Use: {', '.join(valid_plans)}")
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    # Get current subscription
    current = client.table("subscriptions").select("plan_id").eq("user_id", user_id).single().execute()
    
    if not current.data:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    current_plan = current.data["plan_id"]
    
    # Check upgrade is valid (can't downgrade this way)
    plan_order = {'basic': 0, 'pro': 1, 'elite': 2, 'enterprise': 3}
    if plan_order[new_plan_id] <= plan_order.get(current_plan, 0):
        raise HTTPException(status_code=400, detail="Use downgrade endpoint to switch to a lower plan")
    
    # Update subscription
    client.table("subscriptions").update({
        "plan_id": new_plan_id,
        "status": "active"
    }).eq("user_id", user_id).execute()
    
    return {
        "status": True,
        "message": f"Upgraded to {new_plan_id.upper()}",
        "data": {
            "previous_plan": current_plan,
            "new_plan": new_plan_id
        }
    }


@router.post("/subscriptions/downgrade")
async def downgrade_subscription(
    new_plan_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Downgrade to a lower subscription plan.
    """
    from api.services.database_service import DatabaseService
    
    valid_plans = ['basic', 'pro', 'elite', 'enterprise']
    if new_plan_id not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Use: {', '.join(valid_plans)}")
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    # Get current subscription
    current = client.table("subscriptions").select("plan_id").eq("user_id", user_id).single().execute()
    
    if not current.data:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    current_plan = current.data["plan_id"]
    
    # Update subscription (mark for end of period)
    client.table("subscriptions").update({
        "previous_plan_id": current_plan,
        "plan_id": new_plan_id,
        "cancel_at_period_end": True,
        "canceled_at": datetime.now().isoformat()
    }).eq("user_id", user_id).execute()
    
    return {
        "status": True,
        "message": f"Downgrade scheduled to {new_plan_id.upper()}",
        "data": {
            "current_plan": current_plan,
            "new_plan": new_plan_id,
            "effective_from": "end_of_current_period"
        }
    }


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    user: dict = Depends(get_current_user)
):
    """
    Cancel subscription (marks for cancellation at period end).
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    user_id = user.get('user_id') or user.get('id')
    
    client.table("subscriptions").update({
        "cancel_at_period_end": True,
        "canceled_at": datetime.now().isoformat(),
        "status": "canceled"
    }).eq("user_id", user_id).execute()
    
    return {
        "status": True,
        "message": "Subscription will be canceled at end of billing period",
        "data": {
            "cancels_at": "end_of_current_period"
        }
    }


@router.get("/subscription-plans")
async def get_subscription_plans(
    user: dict = Depends(get_current_user)
):
    """
    Get all available subscription plans with details.
    """
    from api.services.database_service import DatabaseService
    
    client = DatabaseService.get_client()
    
    result = client.table("subscription_plans").select("*").execute()
    
    # Get user's current subscription
    user_id = user.get('user_id') or user.get('id')
    current = client.table("subscriptions").select("plan_id, status, current_period_end").eq("user_id", user_id).single().execute()
    
    return {
        "status": True,
        "data": {
            "plans": result.data,
            "current_plan": current.data.get("plan_id") if current.data else "basic",
            "subscription_status": current.data.get("status") if current.data else "active"
        }
    }
