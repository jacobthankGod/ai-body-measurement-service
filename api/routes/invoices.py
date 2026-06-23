"""
Invoice Routes | Phase 160: Unicorn Billing Features
==============================================
Handles invoice generation, downloads, and tax receipt generation.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger("KORRA_INVOICES")

router = APIRouter()

# Import services
from api.services.invoice_generator import generate_invoice_pdf, format_invoice_for_display
from api.services.database_service import DatabaseService
from middleware.subscription_check import validate_subscription


# Models
class Invoice(BaseModel):
    """Invoice data model"""
    id: Optional[str] = None
    user_id: str
    amount_paid: float
    currency: str = "NGN"
    credits_purchased: int = 0
    paystack_reference: Optional[str] = None
    status: str = "pending"
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    subtotal: Optional[float] = None
    invoice_pdf_url: Optional[str] = None
    receipt_generated_at: Optional[str] = None
    created_at: Optional[str] = None


def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail=result.get('error', 'Invalid subscription'))
    return {'api_key': x_api_key}


def get_db_client():
    """Get database client"""
    return DatabaseService.get_client()


# Regional Tax Configuration - $1 FLAT RATE (NO TAX)
# UNIFIED TO $1 PER SCAN - No regional variations
REGIONAL_TAX_RATES = {
    "NG": 0.0,   # No VAT - $1 flat rate
    "GH": 0.0,   # No VAT
    "UK": 0.0,   # No VAT
    "FR": 0.0,   # No VAT
    "US": 0.0,   # No VAT
    "DEFAULT": 0.0  # Flat $1 worldwide
}


def get_regional_tax(country_code: str) -> float:
    """Get tax rate for country code"""
    return REGIONAL_TAX_RATES.get(country_code.upper(), REGIONAL_TAX_RATES["DEFAULT"])


def calculate_tax_breakdown(amount: float, country_code: str) -> dict:
    """Calculate tax breakdown for an amount"""
    tax_rate = get_regional_tax(country_code)
    tax_amount = amount * tax_rate
    subtotal = amount
    
    return {
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total": subtotal + tax_amount
    }


@router.get("/invoices")
async def list_invoices(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """
    List all invoices for the authenticated user.
    
    Returns invoices with tax breakdown for each.
    """
    client = get_db_client()
    user_id = user.get('user_id')
    
    # Fetch invoices from the invoices table
    try:
        result = client.table("invoices").select("*").eq("user_id", user_id).order("created_at", {"ascending": False}).limit(limit).execute()
        invoices = result.data or []
    except Exception as e:
        # Fallback to transactions table if invoices table doesn't exist
        logger.warning(f"Invoices table not available, using transactions: {e}")
        result = client.table("transactions").select("*").eq("user_id", user_id).order("created_at", {"ascending": False}).limit(limit).execute()
        invoices = result.data or []
    
    # Format for display
    formatted_invoices = []
    for inv in invoices:
        currency = inv.get('currency', 'NGN')
        amount = (inv.get('amount_paid', inv.get('amount', 0)))
        
        # Get tax info if available
        tax_rate = inv.get('tax_rate') or get_regional_tax('NG')
        tax_amount = inv.get('tax_amount') or (amount * tax_rate)
        
        formatted_invoices.append({
            **inv,
            'amount': amount,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'subtotal': amount - tax_amount,
            'has_pdf': bool(inv.get('invoice_pdf_url'))
        })
    
    return {
        "status": True,
        "count": len(formatted_invoices),
        "data": formatted_invoices
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get a specific invoice with full details.
    """
    client = get_db_client()
    user_id = user.get('user_id')
    
    # Try invoices table first
    try:
        result = client.table("invoices").select("*").eq("id", invoice_id).eq("user_id", user_id).single().execute()
        if result.data:
            invoice = result.data
        else:
            raise HTTPException(status_code=404, detail="Invoice not found")
    except:
        # Fallback to transactions
        result = client.table("transactions").select("*").eq("id", invoice_id).eq("user_id", user_id).single().execute()
        if result.data:
            invoice = result.data
        else:
            raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Add tax breakdown
    currency = invoice.get('currency', 'NGN')
    amount = invoice.get('amount_paid', invoice.get('amount', 0))
    tax_breakdown = calculate_tax_breakdown(amount, 'NG')  # Could get from user profile
    
    return {
        "status": True,
        "data": {
            **invoice,
            **tax_breakdown
        }
    }


@router.get("/invoices/{invoice_id}/receipt")
async def download_invoice_receipt(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Generate and download a PDF receipt for an invoice.
    """
    client = get_db_client()
    user_id = user.get('user_id')
    
    # Fetch invoice
    try:
        result = client.table("invoices").select("*").eq("id", invoice_id).eq("user_id", user_id).single().execute()
        invoice = result.data
    except:
        # Fallback to transactions
        result = client.table("transactions").select("*").eq("id", invoice_id).eq("user_id", user_id).single().execute()
        invoice = result.data
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if PDF already exists
    if invoice.get('invoice_pdf_url'):
        # Return existing PDF URL
        return {"status": True, "url": invoice['invoice_pdf_url']}
    
    # Generate new PDF
    try:
        pdf_url = await generate_invoice_pdf(invoice, client)
        return {
            "status": True,
            "url": pdf_url,
            "message": "Receipt generated"
        }
    except Exception as e:
        logger.error(f"Receipt generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate receipt")


@router.get("/invoices/tax-summary")
async def get_tax_summary(
    year: int = None,
    user: dict = Depends(get_current_user)
):
    """
    Get tax summary for a given year (for tax filing purposes).
    """
    import calendar
    
    client = get_db_client()
    user_id = user.get('user_id')
    current_year = year or datetime.now().year
    
    # Get country code from user profile
    try:
        profile = client.table("profiles").select("country_code").eq("id", user_id).single().execute()
        country_code = profile.data.get('country_code', 'NG') if profile.data else 'NG'
    except:
        country_code = 'NG'
    
    tax_rate = get_regional_tax(country_code)
    
    # Get all invoices for the year
    start_date = f"{current_year}-01-01"
    end_date = f"{current_year}-12-31"
    
    try:
        result = client.table("invoices").select("*").eq("user_id", user_id).gte("created_at", start_date).lte("created_at", end_date).execute()
        invoices = result.data or []
    except:
        result = client.table("transactions").select("*").eq("user_id", user_id).gte("created_at", start_date).lte("created_at", end_date).execute()
        invoices = result.data or []
    
    # Calculate totals
    total_amount = sum(inv.get('amount_paid', inv.get('amount', 0)) for inv in invoices)
    total_tax = sum(inv.get('tax_amount', total_amount * tax_rate) for inv in invoices)
    total_credits = sum(inv.get('credits_added', inv.get('credits_purchased', 0)) for inv in invoices)
    
    return {
        "status": True,
        "data": {
            "year": current_year,
            "country_code": country_code,
            "tax_rate": tax_rate,
            "total_transactions": len(invoices),
            "total_amount": total_amount,
            "total_tax_paid": total_tax,
            "total_credits": total_credits,
            "currency": "NGN"
        }
    }


@router.post("/invoices/webhook")
async def create_invoice_webhook(
    reference: str,
    amount: float,
    user_id: str,
    credits: int = 0,
    currency: str = "NGN",
    tax_amount: float = 0,
    tax_rate: float = 0
):
    """
    Create invoice from payment webhook (internal endpoint).
    """
    client = get_db_client()
    
    # Calculate tax breakdown
    subtotal = amount - tax_amount
    
    invoice_data = {
        "id": reference,
        "user_id": user_id,
        "amount_paid": amount,
        "currency": currency,
        "credits_purchased": credits,
        "paystack_reference": reference,
        "status": "success",
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "subtotal": subtotal,
        "created_at": datetime.now().isoformat()
    }
    
    try:
        client.table("invoices").insert(invoice_data).execute()
        logger.info(f"Invoice created: {reference}")
        return {"status": True, "invoice_id": reference}
    except Exception as e:
        logger.error(f"Invoice creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create invoice")
