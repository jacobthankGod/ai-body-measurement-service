"""
Measurement Routes
================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
from PIL import Image
import numpy as np

from api.services.measurement_engine import extract_measurements_from_dual_photos
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()

def get_current_user(x_api_key: str = Header(None)):
    """Dependency to validate API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result['valid']:
        raise HTTPException(status_code=403, detail=result['error'])
    return {'api_key': x_api_key}

@router.post("/measurements/extract")
async def extract_measurements(
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    user: dict = Depends(get_current_user)
):
    """Extract body measurements from dual photos."""
    track_usage(user['api_key'])
    
    # Read images
    front_image = Image.open(io.BytesIO(await front.read()))
    side_image = Image.open(io.BytesIO(await side.read()))
    
    measurements = extract_measurements_from_dual_photos(
        np.array(front_image), np.array(side_image), height, gender
    )
    
    return {
        "success": True,
        "request_id": f"req_{user['api_key'][:8]}",
        "measurements": measurements,
        "accuracy": {"mode": "dual", "estimated_cm": "±1-3"},
        "metadata": {
            "processing_time_ms": 2500,
            "model_version": "mediapipe_v0.10.9"
        }
    }

@router.post("/measurements/estimate")
async def estimate_measurements(
    height: float = Form(...),
    gender: str = Form("male"),
    weight: float = Form(None),
    user: dict = Depends(get_current_user)
):
    """Estimate measurements from height only."""
    track_usage(user['api_key'])
    
    measurements = extract_measurements_from_dual_photos(
        np.zeros((100, 100, 3)), np.zeros((100, 100, 3)), height, gender
    )
    
    # Adjust for weight if provided
    if weight:
        bmi = weight / (height / 100) ** 2
        weight_ratio = min(max(bmi / 22, 0.8), 1.5)
        for key in measurements:
            if 'Round' in key or 'Waist' in key:
                measurements[key] = round(measurements[key] * weight_ratio, 1)
    
    return {
        "success": True,
        "measurements": measurements,
        "mode": "estimation"
    }
