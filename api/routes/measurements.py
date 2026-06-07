"""
Measurement Routes | Phase 15: Landmark Visualization Handshake
==============================================================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
import os
from typing import Dict, Tuple
from PIL import Image
import numpy as np

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()

async def get_current_user(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = await validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail=result.get('error', 'Unauthorized'))
    return {'api_key': x_api_key, 'tier': result.get('tier')}

@router.post("/measurements/extract")
async def extract_measurements(
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    user: dict = Depends(get_current_user)
):
    """Extract measurements + Landmarks for Phase 15 Viz."""
    await track_usage(user['api_key'])
    
    # Process images
    front_bytes = await front.read()
    side_bytes = await side.read()
    
    front_image = Image.open(io.BytesIO(front_bytes))
    side_image = Image.open(io.BytesIO(side_bytes))

    # Extract
    measurements, landmarks = extract_measurements_from_dual_photos(
        np.array(front_image), np.array(side_image), height, gender
    )

    return {
        "success": True,
        "measurements": measurements,
        "landmarks": landmarks,
        "metadata": {"mode": "volumetric-v2", "viz_enabled": True}
    }

@router.post("/measurements/validate")
async def validate_measurements(
    measurements: Dict[str, float],
    height: float,
    user: dict = Depends(get_current_user)
):
    return {"valid": True, "issues": []}
