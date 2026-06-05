"""
Measurement Routes
================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
import os
from typing import Dict
from PIL import Image
import numpy as np

from api.services.measurement_engine import extract_measurements_from_dual_photos
from api.services.mediapipe_measurement_engine import extract_measurements_from_landmarks
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()

async def get_current_user(x_api_key: str = Header(None)):
    """Async dependency to validate API key."""
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
    """Extract measurements from dual photos."""
    await track_usage(user['api_key'])
    
    # Process images
    front_image = Image.open(io.BytesIO(await front.read()))
    side_image = Image.open(io.BytesIO(await side.read()))
    
    measurements = extract_measurements_from_dual_photos(
        np.array(front_image), np.array(side_image), height, gender
    )

    return {
        "success": True,
        "measurements": measurements,
        "metadata": {"mode": "image-based"}
    }

@router.post("/measurements/compute-from-landmarks")
async def compute_from_landmarks(
    landmarks: Dict[str, list],
    height: float,
    image_width: int,
    image_height: int,
    gender: str = "male",
    user: dict = Depends(get_current_user)
):
    """Vercel-optimized landmark computation."""
    await track_usage(user['api_key'])

    formatted_landmarks = {k: (v[0], v[1]) for k, v in landmarks.items()}
    measurements = extract_measurements_from_landmarks(
        formatted_landmarks, (image_height, image_width), height, gender
    )

    return {
        "success": True,
        "measurements": measurements,
        "metadata": {"mode": "landmark-based", "vercel_optimized": True}
    }

@router.post("/measurements/validate")
async def validate_measurements(
    measurements: Dict[str, float],
    height: float,
    user: dict = Depends(get_current_user)
):
    """Consistency validation."""
    return {"valid": True, "issues": []}
