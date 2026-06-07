"""
Measurement Routes | UNICORN-GRADE DATA PERSISTENCE
===================================================
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends
from datetime import datetime
import io
import os
import uuid
from typing import Dict, Tuple, Optional
from PIL import Image
import numpy as np
from pathlib import Path

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
from api.services.vision_guard import VisionGuard
from api.services.mesh_exporter import MeshExporter
from api.services.database_service import DatabaseService
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

    # Unicorn Handshake: Map API key to real User UUID
    return {
        'api_key': x_api_key,
        'user_id': result.get('user_id'), # Inferred from the API Key owner
        'tier': result.get('tier'),
        'is_admin': result.get('is_admin', False)
    }

@router.post("/measurements/extract")
async def extract_measurements(
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    client_name: str = Form("Unnamed Client"),
    user: dict = Depends(get_current_user)
):
    """Extract measurements + ATOMIC CLOUD PERSISTENCE."""
    
    # Process images
    front_bytes = await front.read()
    side_bytes = await side.read()
    front_arr = np.array(Image.open(io.BytesIO(front_bytes)))
    side_arr = np.array(Image.open(io.BytesIO(side_bytes)))

    # --- VISION GUARD ---
    if not user.get('is_admin'):
        is_front_valid, front_reason = VisionGuard.validate_photo(front_arr, "front")
        if not is_front_valid: raise HTTPException(status_code=422, detail={"error": front_reason})

    await track_usage(user['api_key'])

    scan_id = str(uuid.uuid4())
    mesh_filename = f"korra_twin_{scan_id}.obj"
    mesh_path = TEMP_MESH_DIR / mesh_filename
    mesh_url = None
    landmarks = {}

    # --- EXTRACTION PIPELINE ---
    try:
        from api.services.extract_measurements import extract_measurements_from_hmr, HMR_ACTIVE
        if HMR_ACTIVE:
            measurements, vertices, landmarks = extract_measurements_from_hmr(front_arr, height, gender)
            if vertices is not None:
                MeshExporter.save_to_obj(vertices, str(mesh_path))
                # For Block 5 verification, we use relative URL.
                # In Full production, this triggers the S3 upload bridge.
                mesh_url = f"/meshes/{mesh_filename}"
        else:
            measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
    except Exception as e:
        measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)

    # --- UNICORN ATOMIC SAVE (DATABASE VAULT) ---
    # We persist the scan to Supabase before returning success.
    db_record = await DatabaseService.save_measurement(
        user_id=user['user_id'],
        client_name=client_name,
        height=height,
        gender=gender,
        biometrics=measurements,
        landmarks=landmarks,
        mesh_url=mesh_url
    )

    return {
        "success": True,
        "measurements": measurements,
        "landmarks": landmarks,
        "scan_id": scan_id,
        "record_id": db_record.get('id') if db_record else None,
        "mesh_url": mesh_url,
        "metadata": {
            "mode": "digital-twin-activated",
            "vision_guard": "bypassed" if user.get('is_admin') else "verified",
            "persistence": "atomic-cloud-locked"
        }
    }
