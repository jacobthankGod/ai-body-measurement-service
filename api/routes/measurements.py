"""
Measurement Routes | TASK-QUEUE ARCHITECTURE (Unicorn Scaling)
============================================================
Handles high-precision AI extraction with background processing
to prevent 502 Bad Gateway timeouts across all vectors.
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timedelta
import io
import os
import uuid
import json
import logging
import traceback
from typing import Dict, Optional
from PIL import Image
import numpy as np
from pathlib import Path

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
from api.services.vision_guard import VisionGuard
from api.services.mesh_exporter import MeshExporter
from api.services.database_service import DatabaseService
from middleware.subscription_check import validate_subscription, track_usage

router = APIRouter()
logger = logging.getLogger("KORRA_MEASUREMENTS")

BASE_DIR = Path(os.getcwd()).resolve()
MESH_DIR = BASE_DIR / "public" / "meshes"
MESH_DIR.mkdir(parents=True, exist_ok=True)

# Shared Task Store
EXTRACTION_TASKS = {}

async def get_current_user(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    result = validate_subscription(x_api_key)
    if not result.get('valid'):
        raise HTTPException(status_code=403, detail=result.get('error', 'Unauthorized'))
    return {'api_key': x_api_key, 'user_id': result.get('user_id'), 'is_admin': result.get('is_admin', False)}

def cleanup_task_queue():
    global EXTRACTION_TASKS
    now = datetime.utcnow()
    keys_to_del = [k for k, v in EXTRACTION_TASKS.items() if (now - datetime.fromisoformat(v["created_at"])) > timedelta(hours=24)]
    for k in keys_to_del: del EXTRACTION_TASKS[k]

def run_extraction_task(task_id: str, front_bytes: bytes, side_bytes: bytes, height: float, gender: str, client_name: str, user_id: str):
    """Background worker for 1:1 HMR extraction with descriptive errors (THREADED)."""
    try:
        cleanup_task_queue()
        EXTRACTION_TASKS[task_id]["status"] = "processing"

        front_arr = np.array(Image.open(io.BytesIO(front_bytes)))
        side_arr = np.array(Image.open(io.BytesIO(side_bytes)))

        mesh_filename = f"korra_twin_{task_id}.obj"
        mesh_path = MESH_DIR / mesh_filename
        mesh_url = None
        landmarks = {}
        hmr_error = None

        # AI EXTRACTION
        try:
            from api.services.extract_measurements import extract_measurements_from_hmr, HMR_ACTIVE
            if HMR_ACTIVE:
                logger.info(f"🧬 [TASK {task_id}] EXECUTING HMR HIGH-PRECISION EXTRACTION...")
                measurements, vertices, landmarks, hmr_error = extract_measurements_from_hmr(front_arr, height, gender)

                if vertices is not None:
                    MeshExporter.save_to_obj(vertices, str(mesh_path))
                    # Physical persistence verification
                    if mesh_path.exists() and mesh_path.stat().st_size > 0:
                        mesh_url = f"/meshes/{mesh_filename}"
                        logger.info(f"✅ MESH VERIFIED: {mesh_url} ({mesh_path.stat().st_size} bytes)")
                    else:
                        hmr_error = "MESH_WRITE_FAILURE: File missing or empty on disk."
                        logger.error(f"❌ {hmr_error}")
            else:
                measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
        except Exception as inner_e:
            logger.error(f"⚠️ HMR Pipeline Conflict: {inner_e}")
            hmr_error = str(inner_e)
            measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)

        # ATOMIC PERSISTENCE
        DatabaseService.save_measurement(
            user_id=user_id, client_name=client_name, height=height,
            gender=gender, biometrics=measurements, landmarks=landmarks, mesh_url=mesh_url
        )

        EXTRACTION_TASKS[task_id].update({
            "status": "completed",
            "measurements": measurements,
            "mesh_url": mesh_url,
            "landmarks": landmarks,
            "debug": hmr_error
        })
        logger.info(f"✅ TASK COMPLETED: {task_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ EXTRACTION TASK FAILED: {error_msg}")
        traceback.print_exc()
        EXTRACTION_TASKS[task_id].update({ "status": "failed", "error": error_msg })

@router.post("/measurements/extract")
async def start_extraction(
    background_tasks: BackgroundTasks,
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    client_name: str = Form("Unnamed Client"),
    user: dict = Depends(get_current_user)
):
    task_id = str(uuid.uuid4())
    front_bytes = await front.read()
    side_bytes = await side.read()
    track_usage(user['api_key'])
    EXTRACTION_TASKS[task_id] = {"status": "queued", "created_at": datetime.utcnow().isoformat()}
    background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, user['user_id'])
    return {"status": "accepted", "task_id": task_id}

@router.post("/measurements/extract-widget")
async def extract_widget(
    background_tasks: BackgroundTasks,
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    height: float = Form(...),
    gender: str = Form("male"),
    merchant_id: str = Form(...),
    client_name: str = Form("Widget Customer")
):
    task_id = str(uuid.uuid4())
    front_bytes = await front.read()
    side_bytes = await side.read()
    EXTRACTION_TASKS[task_id] = {"status": "queued", "created_at": datetime.utcnow().isoformat()}
    background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, merchant_id)
    return {"status": "accepted", "task_id": task_id}

@router.get("/measurements/status/{task_id}")
async def get_extraction_status(task_id: str):
    task = EXTRACTION_TASKS.get(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
    return task
