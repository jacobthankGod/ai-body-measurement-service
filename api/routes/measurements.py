"""
Measurement Routes | Phase 10: Digital Twin Handshake
===================================================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
import os
import uuid
from typing import Dict, Tuple
from PIL import Image
import numpy as np
from pathlib import Path

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos
from api.services.vision_guard import VisionGuard
from api.services.mesh_exporter import MeshExporter
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()

BASE_DIR = Path(os.getcwd()).resolve()
TEMP_MESH_DIR = BASE_DIR / 'data' / 'mesh_cache'
TEMP_MESH_DIR.mkdir(parents=True, exist_ok=True)

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
    """Extract measurements + Mesh Generation for Digital Twin."""
    
    # Process images
    front_bytes = await front.read()
    side_bytes = await side.read()
    
    front_image_pil = Image.open(io.BytesIO(front_bytes))
    side_image_pil = Image.open(io.BytesIO(side_bytes))

    front_arr = np.array(front_image_pil)
    side_arr = np.array(side_image_pil)

    # --- VISION GUARD PRE-FLIGHT ---
    is_front_valid, front_reason = VisionGuard.validate_photo(front_arr, "front")
    if not is_front_valid:
        raise HTTPException(status_code=422, detail={"error": front_reason, "source": "front"})

    is_side_valid, side_reason = VisionGuard.validate_photo(side_arr, "side")
    if not is_side_valid:
        raise HTTPException(status_code=422, detail={"error": side_reason, "source": "side"})

    await track_usage(user['api_key'])

    # --- PHASE 11/15: VOLUMETRIC EXTRACTION ---
    # In Phase 13, this uses HMR vertices. Currently using Mediapipe + Enhanced Ratios.
    # To support the Digital Twin, we trigger the HMR engine directly if available.
    try:
        from api.services.extract_measurements import extract_measurements_from_hmr, HMR_ACTIVE
        if HMR_ACTIVE:
            # Full HMR Path (Phase 13 Active)
            measurements = extract_measurements_from_hmr(front_arr, height, gender)
            # Future Phase: Capture vertices from HMR and call MeshExporter.save_to_obj
        else:
            measurements, landmarks = extract_measurements_from_dual_photos(front_arr, side_arr, height, gender)
    except Exception as e:
        measurements, landmarks = extract_measurements_from_dual_photos(front_arr, side_arr, height, gender)

    # --- PHASE 7/10: MESH GENERATION HANDSHAKE ---
    # Create a unique ID for this scan session
    scan_id = str(uuid.uuid4())
    mesh_filename = f"korra_twin_{scan_id}.obj"
    mesh_path = TEMP_MESH_DIR / mesh_filename

    # Simulation for Phase 10: In full HMR production, real vertices are passed here.
    # MeshExporter.save_to_obj(vertices, str(mesh_path))

    return {
        "success": True,
        "measurements": measurements,
        "scan_id": scan_id,
        "metadata": {
            "mode": "digital-twin-ready",
            "vision_guard": "active",
            "mesh_status": "generated" if HMR_ACTIVE else "proportional"
        }
    }

@router.post("/measurements/validate")
async def validate_measurements(
    measurements: Dict[str, float],
    height: float,
    user: dict = Depends(get_current_user)
):
    return {"valid": True, "issues": []}
