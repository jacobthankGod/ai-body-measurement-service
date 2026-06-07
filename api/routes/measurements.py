"""
Measurement Routes | Phase 16: Digital Twin Activation
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

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
from api.services.vision_guard import VisionGuard
from api.services.mesh_exporter import MeshExporter
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()

BASE_DIR = Path(os.getcwd()).resolve()
TEMP_MESH_DIR = Path("/tmp/korra_mesh_cache")
TEMP_MESH_DIR.mkdir(parents=True, exist_ok=True)

async def get_current_user(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = await validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail=result.get('error', 'Unauthorized'))
    return {'api_key': x_api_key, 'tier': result.get('tier'), 'is_admin': result.get('is_admin', False)}

@router.post("/measurements/extract")
async def extract_measurements(
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    user: dict = Depends(get_current_user)
):
    """Extract measurements + REAL OBJ GENERATION + Landmarks."""
    
    # Process images
    front_bytes = await front.read()
    side_bytes = await side.read()
    
    front_image_pil = Image.open(io.BytesIO(front_bytes))
    side_image_pil = Image.open(io.BytesIO(side_bytes))

    front_arr = np.array(front_image_pil)
    side_arr = np.array(side_image_pil)

    # --- VISION GUARD (with Admin Bypass) ---
    if not user.get('is_admin'):
        is_front_valid, front_reason = VisionGuard.validate_photo(front_arr, "front")
        if not is_front_valid:
            raise HTTPException(status_code=422, detail={"error": front_reason, "source": "front"})

    await track_usage(user['api_key'])

    scan_id = str(uuid.uuid4())
    mesh_filename = f"korra_twin_{scan_id}.obj"
    mesh_path = TEMP_MESH_DIR / mesh_filename
    mesh_generated = False
    landmarks = {}

    # --- EXTRACTION PIPELINE ---
    try:
        from api.services.extract_measurements import extract_measurements_from_hmr, HMR_ACTIVE
        if HMR_ACTIVE:
            # Full HMR Path (Phase 13 Active)
            measurements, vertices, landmarks = extract_measurements_from_hmr(front_arr, height, gender)
            if vertices is not None:
                MeshExporter.save_to_obj(vertices, str(mesh_path))
                mesh_generated = True
        else:
            measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
    except Exception as e:
        print(f"⚠️ HMR Pipeline Drift: {e}")
        measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)

    return {
        "success": True,
        "measurements": measurements,
        "landmarks": landmarks,
        "scan_id": scan_id,
        "mesh_url": f"/meshes/{mesh_filename}" if mesh_generated else None,
        "metadata": {
            "mode": "digital-twin-activated",
            "vision_guard": "bypassed" if user.get('is_admin') else "verified",
            "mesh_status": "real" if mesh_generated else "proportional"
        }
    }
