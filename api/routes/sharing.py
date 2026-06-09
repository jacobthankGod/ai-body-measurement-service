"""
Sharing API | KORRA Remote Measurement Links
===========================================
Hardened persistence using PostgreSQL 'invitations' table.
"""
from fastapi import APIRouter, HTTPException, Form
import os
from api.services.database_service import DatabaseService
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

router = APIRouter()

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@korra.work")

@router.post("/send-email")
async def send_scan_link(
    merchant_id: str = Form(...),
    customer_email: str = Form(...),
    client_name: str = Form(None)
):
    """Sends a public scan link using persistent DB tokens."""
    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured.")

    # Atomic Create in Database (Permanent even after server restart)
    token = DatabaseService.create_invitation(merchant_id, client_name)
    if not token:
        raise HTTPException(status_code=500, detail="Internal Persistence Error.")

    host = os.environ.get("RENDER_EXTERNAL_URL", "https://korra-436814609100.us-central1.run.app")
    scan_url = f"{host}/share?token={token}"

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=customer_email,
        subject='Your Digital Body Scan | KORRA',
        html_content=f'''
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; border: 1px solid #eee; border-radius: 12px;">
                <h1 style="color: #000; font-size: 24px;">Digital Body Scan Invitation</h1>
                <p style="color: #666; line-height: 1.6;">Your artisan has invited you to capture your biometric profile.</p>
                <div style="margin: 40px 0; text-align: center;">
                    <a href="{scan_url}" style="background-color: #57D7C0; color: #000; padding: 16px 32px; border-radius: 99px; text-decoration: none; font-weight: 800;">START SCAN</a>
                </div>
                <p style="font-size: 11px; color: #999;">One-time use. Link expires in 24 hours.</p>
            </div>
        '''
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return {"success": True, "message": "Invitation sent."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Email delivery failed.")

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
