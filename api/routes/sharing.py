"""
Sharing API | KORRA Remote Measurement Links
===========================================
Hardened persistence using PostgreSQL 'invitations' table.
Uses Brevo (formerly Sendinblue) for transactional emails.
"""
from fastapi import APIRouter, HTTPException, Form
import os
import logging
from api.services.database_service import DatabaseService, DatabaseService as DB
from api.config import BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_FROM_NAME

router = APIRouter()
logger = logging.getLogger("KORRA_SHARING")

@router.post("/send-email")
async def send_scan_link(
    merchant_id: str = Form(...),
    customer_email: str = Form(...),
    client_name: str = Form(None)
):
    """Sends a public scan link using persistent DB tokens via Brevo."""
    if not BREVO_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured.")

    # Atomic Create in Database (Permanent even after server restart)
    token = DB.create_invitation(merchant_id, client_name)
    if not token:
        raise HTTPException(status_code=500, detail="Internal Persistence Error.")

    host = os.environ.get("EXTERNAL_URL", "https://korra.work")
    scan_url = f"{host}/share?token={token}"

    # Use Brevo for email delivery
    try:
        from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail, SendSmtpEmailSender, SendSmtpEmailTo
        
        config = Configuration()
        config.api_key['api-key'] = BREVO_API_KEY
        api_client = ApiClient(config)
        email_api = TransactionalEmailsApi(api_client)
        
        sender = SendSmtpEmailSender(name=BREVO_FROM_NAME, email=BREVO_FROM_EMAIL)
        
        html_content = f'''
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; border: 1px solid rgba(255,255,255,0.1); border-radius: 24px; background: #000;">
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="width: 40px; height: 40px; background: #C6FF00; border-radius: 8px; display: inline-block; transform: rotate(-8deg);"></div>
                <h1 style="color: #fff; font-size: 24px; margin-top: 16px;">Digital Body Scan</h1>
            </div>
            <p style="color: #A3A3A3; line-height: 1.6; margin-bottom: 32px;">Your artisan has invited you to capture your biometric profile for perfect-fit clothing.</p>
            <div style="text-align: center; margin: 40px 0;">
                <a href="{scan_url}" style="background-color: #C6FF00; color: #000; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 800; display: inline-block;">START SCAN</a>
            </div>
            <p style="font-size: 11px; color: #737373; text-align: center;">One-time use. Link expires in 24 hours.</p>
        </div>
        '''
        
        email = SendSmtpEmail(
            to=[SendSmtpEmailTo(email=customer_email)],
            sender=sender,
            subject='Your Digital Body Scan | KORRA',
            html_content=html_content
        )
        
        result = email_api.send_transac_email(email)
        logger.info(f"Brevo email sent to {customer_email}")
        return {"success": True, "message": "Invitation sent.", "email_id": result.get("message_id")}
        
    except Exception as e:
        logger.error(f"Brevo email failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email delivery failed: {str(e)}")

@router.get("/verify/{token}")
async def verify_share_token(token: str):
    """Checks if a shared scan token is still valid via DB."""
    invite = DatabaseService.verify_invitation(token)
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired link.")

    return {
        "valid": True,
        "merchant_id": invite["merchant_id"],
        "client_name": invite["client_name"]
    }
