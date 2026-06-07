"""
Sharing API | KORRA Remote Measurement Links
===========================================
Handles Email invitations via SendGrid and token-based public access.
"""
from fastapi import APIRouter, HTTPException, Form
import os
import uuid
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

router = APIRouter()

# Share Session Store (In-memory for prototype, sync with qrcode.py logic)
SHARE_SESSIONS = {}

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@korra.work")

@router.post("/send-email")
async def send_scan_link(
    merchant_id: str = Form(...),
    customer_email: str = Form(...),
    client_name: str = Form(None)
):
    """Sends a public scan link to a customer via email."""
    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured.")

    # Create secure token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=1) # 24h validity

    SHARE_SESSIONS[token] = {
        "merchant_id": merchant_id,
        "client_name": client_name or "Remote Client",
        "expires_at": expires_at
    }

    host = os.environ.get("RENDER_EXTERNAL_URL", "https://ai-body-measurement-service-1.onrender.com")
    scan_url = f"{host}/share?token={token}"

    # Prepare Email
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=customer_email,
        subject='Your Body Scan Invitation | KORRA',
        html_content=f'''
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; border: 1px solid #eee; border-radius: 12px;">
                <h1 style="color: #000; font-size: 24px;">Digital Body Scan Invitation</h1>
                <p style="color: #666; line-height: 1.6;">You have been invited to perform a digital body scan. This will provide your tailor/merchant with clinical-grade biometrics for a perfect fit.</p>
                <div style="margin: 40px 0; text-align: center;">
                    <a href="{scan_url}" style="background-color: #57D7C0; color: #000; padding: 16px 32px; border-radius: 99px; text-decoration: none; font-weight: 800;">START SCAN NOW</a>
                </div>
                <p style="font-size: 12px; color: #999;">This link will expire in 24 hours. No login required.</p>
            </div>
        '''
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return {"success": True, "message": f"Invitation sent to {customer_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify/{token}")
async def verify_share_token(token: str):
    """Checks if a shared scan token is still valid."""
    session = SHARE_SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired link.")

    if datetime.utcnow() > session["expires_at"]:
        del SHARE_SESSIONS[token]
        raise HTTPException(status_code=410, detail="Invitation link has expired.")

    return {"valid": True, "merchant_id": session["merchant_id"], "client_name": session["client_name"]}
