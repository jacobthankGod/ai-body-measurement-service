"""
QR Code Engine | KORRA In-Store Integration
==========================================
Generates ephemeral scan tokens and base64 QR imagery.
"""
from fastapi import APIRouter, HTTPException, Form
import qrcode
import io
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import os

router = APIRouter()

# Simple In-Memory Session Store (To be migrated to Redis/Postgres in Phase 22)
ACTIVE_SESSIONS = {}

@router.post("/generate")
async def generate_qr(
    merchant_id: str = Form(...),
    expiry_minutes: int = Form(60),
    client_name: str = Form(None)
):
    """Generates a high-authority in-store scan QR."""

    # Create secure token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    # Register session
    ACTIVE_SESSIONS[token] = {
        "merchant_id": merchant_id,
        "client_name": client_name or "Retail Customer",
        "expires_at": expires_at
    }

    # Generate QR URL
    host = os.environ.get("RENDER_EXTERNAL_URL", "https://korra-436814609100.us-central1.run.app")
    scan_url = f"{host}/widget?merchant={merchant_id}&token={token}"

    # Render QR Image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(scan_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return {
        "success": True,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}",
        "session_token": token,
        "expires_at": expires_at.isoformat(),
        "scan_url": scan_url
    }

@router.get("/verify/{token}")
async def verify_token(token: str):
    """Checks if a QR session is still valid."""
    session = ACTIVE_SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session token.")

    if datetime.utcnow() > session["expires_at"]:
        del ACTIVE_SESSIONS[token]
        raise HTTPException(status_code=410, detail="QR Link Expired.")

    return {"valid": True, "merchant_id": session["merchant_id"]}
