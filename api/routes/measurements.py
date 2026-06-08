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

# Shared Task Store (Persistent via JSON to survive minor restarts)
TASK_STORE_FILE = BASE_DIR / "data" / "tasks.json"

def load_tasks():
    try:
        if TASK_STORE_FILE.exists():
            return json.loads(TASK_STORE_FILE.read_text())
    except: pass
    return {}

def save_tasks(tasks):
    try:
        TASK_STORE_FILE.parent.mkdir(exist_ok=True)
        # Only keep last 100 tasks to prevent file bloat
        pruned = dict(list(tasks.items())[-100:])
        TASK_STORE_FILE.write_text(json.dumps(pruned))
    except: pass

EXTRACTION_TASKS = load_tasks()

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
    # Filter out tasks older than 24 hours
    changed = False
    new_tasks = {}
    for k, v in EXTRACTION_TASKS.items():
        try:
            if (now - datetime.fromisoformat(v["created_at"])) < timedelta(hours=24):
                new_tasks[k] = v
            else:
                changed = True
        except: changed = True

    if changed:
        EXTRACTION_TASKS = new_tasks
        save_tasks(EXTRACTION_TASKS)

def update_task(task_id, data):
    global EXTRACTION_TASKS
    if task_id in EXTRACTION_TASKS:
        EXTRACTION_TASKS[task_id].update(data)
    else:
        EXTRACTION_TASKS[task_id] = data
    save_tasks(EXTRACTION_TASKS)

import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

# ... (rest of imports)

# --- SUBPROCESS RELIABILITY ENGINE ---
def run_extraction_subprocess(task_id: str, front_path: str, side_path: str, height: float, gender: str, client_name: str, user_id: str):
    """
    Isolated Subprocess Worker: Runs AI in a completely separate memory space.
    If this process crashes (OOM), the main web server survives.
    """
    try:
        # 1. READ DISK HANDSHAKE (Minimize RAM during IPC)
        with open(front_path, 'rb') as f: front_arr = np.array(Image.open(f))
        os.remove(front_path)

        with open(side_path, 'rb') as f: side_arr = np.array(Image.open(f))
        os.remove(side_path)

        mesh_filename = f"korra_twin_{task_id}.obj"
        mesh_path = MESH_DIR / mesh_filename
        mesh_url = None
        landmarks = {}
        hmr_error = None

        # 2. AI EXTRACTION
        try:
            from api.services.extract_measurements import extract_measurements_from_hmr, HMR_ACTIVE
            if HMR_ACTIVE:
                logger.info(f"🧬 [SUBPROCESS {task_id}] EXECUTING HMR...")
                measurements, vertices, landmarks, hmr_error = extract_measurements_from_hmr(front_arr, height, gender)

                if vertices is not None:
                    from api.services.mesh_exporter import MeshExporter
                    MeshExporter.save_to_obj(vertices, str(mesh_path))
                    if mesh_path.exists() and mesh_path.stat().st_size > 0:
                        mesh_url = f"/meshes/{mesh_filename}"
            else:
                from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
                measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
        except Exception as inner_e:
            from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
            hmr_error = str(inner_e)
            measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)

        # 3. ATOMIC PERSISTENCE
        from api.services.database_service import DatabaseService
        DatabaseService.save_measurement(
            user_id=user_id, client_name=client_name, height=height,
            gender=gender, biometrics=measurements, landmarks=landmarks, mesh_url=mesh_url
        )

        # 4. FINAL HANDSHAKE
        return {
            "status": "completed",
            "measurements": measurements,
            "mesh_url": mesh_url,
            "landmarks": landmarks,
            "debug": hmr_error
        }

    except Exception as e:
        logger.error(f"❌ SUBPROCESS CRITICAL FAILURE: {e}")
        return {"status": "failed", "error": str(e)}

def run_extraction_task(task_id: str, front_bytes: bytes, side_bytes: bytes, height: float, gender: str, client_name: str, user_id: str):
    """
    Reliability Wrapper: Manages the lifecycle of the AI Subprocess.
    """
    try:
        cleanup_task_queue()
        update_task(task_id, {"status": "processing"})

        # 1. DISK-BASED IPC (Render 512MB RAM protection)
        tmp_dir = BASE_DIR / "data" / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        f_path = str(tmp_dir / f"f_{task_id}.png")
        s_path = str(tmp_dir / f"s_{task_id}.png")

        with open(f_path, 'wb') as f: f.write(front_bytes)
        del front_bytes
        with open(s_path, 'wb') as f: f.write(side_bytes)
        del side_bytes

        # 2. ISOLATED EXECUTION
        # Using ProcessPoolExecutor with max_workers=1 to force serial execution on low-RAM
        with ProcessPoolExecutor(max_workers=1) as executor:
            logger.info(f"🚀 [TASK {task_id}] Launching Isolated AI Process...")
            future = executor.submit(run_extraction_subprocess, task_id, f_path, s_path, height, gender, client_name, user_id)
            result = future.result(timeout=300) # 5 minute timeout

        # 3. TASK SYNC
        update_task(task_id, result)
        logger.info(f"✅ [TASK {task_id}] Process returned control to main server.")

    except Exception as e:
        error_msg = f"ORCHESTRATOR_CRASH: {str(e)}"
        logger.error(f"❌ ORCHESTRATOR FAILED: {error_msg}")
        update_task(task_id, { "status": "failed", "error": error_msg })
        # Cleanup orphan files
        for p in [f_path, s_path]:
            if os.path.exists(p): os.remove(p)

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
    update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat()})
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
    update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat()})
    background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, merchant_id)
    return {"status": "accepted", "task_id": task_id}

@router.get("/measurements/status/{task_id}")
async def get_extraction_status(task_id: str):
    task = EXTRACTION_TASKS.get(task_id)
    if not task: raise HTTPException(status_code=404, detail="Task not found.")
    return task
