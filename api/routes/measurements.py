"""
Measurement Routes | Phase 14: Vision Guard Integration
======================================================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
import os
from typing import Dict, Tuple
from PIL import Image
import numpy as np

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos
from api.services.vision_guard import VisionGuard
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
    """Extract measurements with Vision Guard Pre-Flight checks."""
    
    # Process images
    front_bytes = await front.read()
    side_bytes = await side.read()
    
    front_image_pil = Image.open(io.BytesIO(front_bytes))
    side_image_pil = Image.open(io.BytesIO(side_bytes))

    front_arr = np.array(front_image_pil)
    side_arr = np.array(side_image_pil)

    # --- PHASE 14: VISION GUARD PRE-FLIGHT ---
    is_front_valid, front_reason = VisionGuard.validate_photo(front_arr, "front")
    if not is_front_valid:
        raise HTTPException(status_code=422, detail={"error": front_reason, "source": "front"})

    is_side_valid, side_reason = VisionGuard.validate_photo(side_arr, "side")
    if not is_side_valid:
        raise HTTPException(status_code=422, detail={"error": side_reason, "source": "side"})

    # Proceed to extraction if vision is clear
    await track_usage(user['api_key'])

    measurements, landmarks = extract_measurements_from_dual_photos(
        front_arr, side_arr, height, gender
    )

    # Pose Stability check (Post-landmark detection)
    is_stable, pose_reason = VisionGuard.analyze_pose_stability(landmarks, "front")
    if not is_stable:
        return {
            "success": False,
            "error": pose_reason,
            "code": "POSE_UNSTABLE",
            "landmarks": landmarks
        }

    return {
        "success": True,
        "measurements": measurements,
        "landmarks": landmarks,
        "metadata": {"mode": "volumetric-v2", "vision_guard": "active"}
    }

@router.post("/measurements/validate")
async def validate_measurements(
    measurements: Dict[str, float],
    height: float,
    user: dict = Depends(get_current_user)
):
    return {"valid": True, "issues": []}
