"""
Measurement Routes | TASK-QUEUE ARCHITECTURE (Unicorn Scaling)
============================================================
Handles high-precision AI extraction with background processing
to prevent 502 Bad Gateway timeouts across all vectors.
"""
import sys
import threading
import subprocess
import io
import os
import uuid
import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Optional
from PIL import Image
import numpy as np
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends, BackgroundTasks

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

# --- SUBPROCESS RELIABILITY ENGINE ---
def run_extraction_subprocess_cli(task_id: str, front_path: str, side_path: str, height: float, gender: str, client_name: str, user_id: str):
    """
    Isolated Subprocess Worker: Runs AI in a COMPLETELY separate OS process via CLI.
    This is the ultimate protection against TensorFlow memory leaks in the main process.
    """
    try:
        mesh_filename = f"korra_twin_{task_id}.obj"
        mesh_path = MESH_DIR / mesh_filename

        # 1. EXECUTE EXTERNAL AI PROCESS
        # Path to the standalone script
        script_path = BASE_DIR / "api" / "services" / "hmr_subprocess.py"

        cmd = [
            sys.executable,
            str(script_path),
            front_path,
            str(height),
            gender,
            str(mesh_path)
        ]

        logger.info(f"🚀 [TASK {task_id}] Launching External AI Process: {' '.join(cmd)}")

        # Run with 5 minute timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # 2. PARSE RESULTS
        if result.returncode != 0:
            logger.error(f"❌ AI PROCESS CRASHED: {result.stderr}")
            # Fallback to MediaPipe (which doesn't use TF)
            from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
            with open(front_path, 'rb') as f: front_arr = np.array(Image.open(f))
            with open(side_path, 'rb') as f: side_arr = np.array(Image.open(f))
            measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
            hmr_error = f"AI Subprocess Crashed (RC {result.returncode}): {result.stderr[:200]}"
            mesh_url = None
        else:
            try:
                # Find JSON in stdout (in case there's other output)
                stdout = result.stdout.strip()
                last_line = stdout.split('\n')[-1]
                data = json.loads(last_line)

                if data.get("status") == "completed":
                    measurements = data["measurements"]
                    landmarks = data["landmarks"]
                    hmr_error = None
                    mesh_url = f"/meshes/{mesh_filename}" if mesh_path.exists() else None
                else:
                    raise Exception(data.get("error", "Unknown error in subprocess"))
            except Exception as e:
                logger.error(f"❌ FAILED TO PARSE AI OUTPUT: {e}")
                # Fallback
                from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
                with open(front_path, 'rb') as f: front_arr = np.array(Image.open(f))
                with open(side_path, 'rb') as f: side_arr = np.array(Image.open(f))
                measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
                hmr_error = f"Parse Error: {str(e)}"
                mesh_url = None

        # 3. CLEANUP TEMP FILES
        if os.path.exists(front_path): os.remove(front_path)
        if os.path.exists(side_path): os.remove(side_path)

        # 4. ATOMIC PERSISTENCE
        from api.services.database_service import DatabaseService
        DatabaseService.save_measurement(
            user_id=user_id, client_name=client_name, height=height,
            gender=gender, biometrics=measurements, landmarks=landmarks, mesh_url=mesh_url
        )

        return {
            "status": "completed",
            "measurements": measurements,
            "mesh_url": mesh_url,
            "landmarks": landmarks,
            "debug": hmr_error
        }

    except Exception as e:
        logger.error(f"❌ ORCHESTRATOR CRITICAL FAILURE: {e}")
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
        # We use a simple thread here because the isolation happens via subprocess.run
        # This prevents the double-memory hit of ProcessPoolExecutor + subprocess
        result = run_extraction_subprocess_cli(task_id, f_path, s_path, height, gender, client_name, user_id)

        # 3. TASK SYNC
        update_task(task_id, result)
        logger.info(f"✅ [TASK {task_id}] Process returned control to main server.")

    except Exception as e:
        error_msg = f"ORCHESTRATOR_CRASH: {str(e)}"
        logger.error(f"❌ ORCHESTRATOR FAILED: {error_msg}")
        update_task(task_id, { "status": "failed", "error": error_msg })

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
    try:
        task_id = str(uuid.uuid4())
        front_bytes = await front.read()
        side_bytes = await side.read()
        
        # Validate input
        if not front_bytes or not side_bytes:
            raise HTTPException(status_code=400, detail="Empty image files")
        if height < 50 or height > 250:
            raise HTTPException(status_code=400, detail="Invalid height")
            
        track_usage(user['api_key'])
        update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat()})
        background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, user['user_id'])
        return {"status": "accepted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction start failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start extraction")

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
    try:
        task_id = str(uuid.uuid4())
        front_bytes = await front.read()
        side_bytes = await side.read()
        
        # Validate input
        if not front_bytes or not side_bytes:
            raise HTTPException(status_code=400, detail="Empty image files")
        if height < 50 or height > 250:
            raise HTTPException(status_code=400, detail="Invalid height")
        if not merchant_id:
            raise HTTPException(status_code=400, detail="Merchant ID required")
            
        update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat()})
        background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, merchant_id)
        return {"status": "accepted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Widget extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start widget extraction")

@router.get("/measurements/status/{task_id}")
async def get_extraction_status(task_id: str):
    try:
        task = EXTRACTION_TASKS.get(task_id)
        if not task:
            # Try loading from disk as fallback
            tasks = load_tasks()
            task = tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found.")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status temporarily unavailable")
