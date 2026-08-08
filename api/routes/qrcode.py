"""
QR Code Engine | KORRA In-Store Integration
==========================================
Generates persistent scan tokens and base64 QR imagery.
Now backed by PostgreSQL (qr_sessions) for fail-proof scaling.
"""
from fastapi import APIRouter, HTTPException, Form
import qrcode
import io
import base64
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os

from api.services.database_service import DatabaseService

router = APIRouter()
logger = logging.getLogger("KORRA_QR")

@router.post("/generate")
async def generate_qr(
    merchant_id: str = Form(...),
    expiry_minutes: int = Form(60),
    client_name: str = Form(None)
):
    """Generates a persistent in-store scan QR."""

    # Create secure token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    # Register session in DB (Unicorn-Grade Persistence)
    success = DatabaseService.save_qr_session(
        merchant_id=merchant_id,
        token=token,
        client_name=client_name or "Retail Customer",
        expires_at=expires_at
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to register scan session.")

    # Generate QR URL
    host = os.environ.get("EXTERNAL_URL", "https://korra.work")
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
    """Checks if a persistent QR session is still valid."""
    session = DatabaseService.get_qr_session(token)

    if not session:
        raise HTTPException(status_code=404, detail="Invalid session token.")

    # Check expiration (DB column is TIMESTAMPTZ)
    expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
    if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
        raise HTTPException(status_code=410, detail="QR Link Expired.")

    return {
        "valid": True,
        "merchant_id": session["merchant_id"],
        "client_name": session.get("client_name")
    }
