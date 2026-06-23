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
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Optional
# from PIL import Image # MOVED TO LATE IMPORT
# import numpy as np # MOVED TO LATE IMPORT
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, Depends, BackgroundTasks

# Global Concurrency Throttle: Only 1 AI process at a time on 512MB RAM
_AI_SEMAPHORES = {}

def get_ai_semaphore():
    """Returns a loop-bound semaphore to prevent 'different loop' errors."""
    loop = asyncio.get_event_loop()
    if loop not in _AI_SEMAPHORES:
        _AI_SEMAPHORES[loop] = asyncio.Semaphore(1)
    return _AI_SEMAPHORES[loop]

from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
from api.services.vision_guard import VisionGuard
from api.services.mesh_exporter import MeshExporter
from api.services.database_service import DatabaseService
from api.services.imputation_service import imputation_service
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
    expired_keys = []
    for k, v in EXTRACTION_TASKS.items():
        try:
            if (now - datetime.fromisoformat(v["created_at"])) >= timedelta(hours=24):
                expired_keys.append(k)
        except: expired_keys.append(k)

    if expired_keys:
        for k in expired_keys:
            del EXTRACTION_TASKS[k]
        save_tasks(EXTRACTION_TASKS)

def update_task(task_id, data):
    """
    Atomic Task Update: Writes to memory and disk immediately.
    Ensures status survives container restarts after OOM crashes.
    """
    global EXTRACTION_TASKS
    import copy

    # 1. Update In-Memory
    if task_id in EXTRACTION_TASKS:
        EXTRACTION_TASKS[task_id].update(data)
    else:
        EXTRACTION_TASKS[task_id] = data

    # 2. Atomic Disk Flush
    try:
        # Load latest from disk to prevent overwriting other concurrent task updates
        disk_tasks = load_tasks()
        disk_tasks[task_id] = EXTRACTION_TASKS[task_id]
        save_tasks(disk_tasks)
    except Exception as e:
        logger.error(f"Failed to persist task {task_id} to disk: {e}")

# --- SUBPROCESS RELIABILITY ENGINE ---
async def run_extraction_subprocess_cli(task_id: str, front_path: str, side_path: str, height: float, gender: str, client_name: str, user_id: str, client_user_id: str = None):
    """
    Isolated Subprocess Worker: Runs AI in a COMPLETELY separate OS process via CLI.
    This is the ultimate protection against TensorFlow memory leaks in the main process.
    Now supports dual-account persistence via client_user_id.
    """
    import sys # REDUNDANT IMPORT FOR SCOPE PROTECTION
    import numpy as np
    from PIL import Image

    # ENFORCE GLOBAL CONCURRENCY (Wait if another task is running)
    async with get_ai_semaphore():
        try:
            logger.info(f"⏳ [TASK {task_id}] Acquired AI Semaphore. Processing...")
            mesh_filename = f"korra_twin_{task_id}.obj"
            mesh_path = MESH_DIR / mesh_filename

            # 1. EXECUTE EXTERNAL AI PROCESS
            # Path to the standalone script
            script_path = BASE_DIR / "api" / "services" / "hmr_subprocess.py"

            cmd = [
                sys.executable,
                str(script_path),
                front_path,
                side_path,
                str(height),
                gender,
                str(mesh_path)
            ]

            logger.info(f"🚀 [TASK {task_id}] Launching External AI Process: {' '.join(cmd)}")

            # Run with 5 minute timeout
            # Use asyncio to prevent blocking the event loop while waiting for the subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                returncode = proc.returncode
            except asyncio.TimeoutError:
                proc.kill()
                stdout, stderr = await proc.communicate()
                returncode = -1
                logger.error(f"❌ [TASK {task_id}] AI Process timed out.")

            # 2. PARSE RESULTS
            if returncode != 0:
                err_msg = stderr.decode() if stderr else "Unknown exit"
                logger.error(f"❌ AI PROCESS CRASHED: {err_msg}")
                # Fallback to MediaPipe (which doesn't use TF)
                from api.services.mediapipe_measurement_engine import extract_measurements_from_dual_photos as fallback_extract
                with open(front_path, 'rb') as f: front_arr = np.array(Image.open(f))
                with open(side_path, 'rb') as f: side_arr = np.array(Image.open(f))
                measurements, landmarks = fallback_extract(front_arr, side_arr, height, gender)
                body_shape = "Standard"
                size_rec = "M"
                hmr_error = f"AI Subprocess Crashed (RC {returncode}): {err_msg[:200]}"
                mesh_url = None
            else:
                try:
                    # Find JSON in stdout (in case there's other output)
                    stdout_str = stdout.decode().strip()
                    last_line = stdout_str.split('\n')[-1]
                    data = json.loads(last_line)

                    if data.get("status") == "completed":
                        measurements = data["measurements"]
                        landmarks = data["landmarks"]
                        body_shape = data.get("body_shape", "Standard")
                        size_rec = data.get("size_recommendation", "M")
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
                    body_shape = "Standard"
                    size_rec = "M"
                    hmr_error = f"Parse Error: {str(e)}"
                    mesh_url = None

            # 3. CLEANUP TEMP FILES
            if os.path.exists(front_path): os.remove(front_path)
            if os.path.exists(side_path): os.remove(side_path)

# 4. ATOMIC PERSISTENCE (Dual Account - Unicorn Level)
            from api.services.database_service import DatabaseService
            DatabaseService.save_measurement(
                user_id=user_id, client_name=client_name, height=height,
                gender=gender, biometrics=measurements, landmarks=landmarks,
                mesh_url=mesh_url, body_shape=body_shape, size_rec=size_rec,
                client_user_id=client_user_id  # UNICORN: Save to both merchant AND client
            )

            return {
                "status": "completed",
                "measurements": measurements,
                "mesh_url": mesh_url,
                "landmarks": landmarks,
                "body_shape": body_shape,
                "size_recommendation": size_rec,
                "debug": hmr_error
            }

        except Exception as e:
            logger.error(f"❌ ORCHESTRATOR CRITICAL FAILURE: {e}")
            return {"status": "failed", "error": str(e)}

async def run_extraction_task(task_id: str, front_bytes: bytes, side_bytes: bytes, height: float, gender: str, client_name: str, user_id: str, client_user_id: str = None):
    """
    Reliability Wrapper: Manages the lifecycle of the AI Subprocess.
    Now with dual-account support for unicorn-level measurement ownership.
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
        # We now await the async subprocess function (with client_user_id for dual ownership)
        result = await run_extraction_subprocess_cli(task_id, f_path, s_path, height, gender, client_name, user_id, client_user_id)

# 3. TASK SYNC
        update_task(task_id, result)
        logger.info(f"✅ [TASK {task_id}] Process returned control to main server.")

        # 4. UNICORN SYNC NOTIFICATIONS (Phase 4)
        if result.get("status") == "completed":
            # Get measurement data for notifications
            measurement_data = result.get("measurements", {})
            body_shape = result.get("body_shape", "Standard")
            size_rec = result.get("size_recommendation", "M")
            
            # a) In-app notification to merchant
            try:
                from api.services.notification_service import notification_service
                await notification_service.notify_scan_completed(
                    merchant_id=user_id,
                    client_name=client_name,
                    measurement_id=task_id
                )
                logger.info(f"🔔 [TASK {task_id}] Notification sent to merchant")
            except Exception as e:
                logger.warning(f"Notification failed: {e}")
            
            # b) Email notification to merchant (via Brevo)
            try:
                from api.services.email_service import email_service
                # Get merchant email
                client = DatabaseService.get_client()
                if client:
                    merchant_profile = client.table("profiles").select("email, company_name").eq("id", user_id).single().execute()
                    if merchant_profile.data:
                        merchant_email = merchant_profile.data.get("email")
                        merchant_name = merchant_profile.data.get("company_name") or "Your tailor"
                        host = os.environ.get("RENDER_EXTERNAL_URL", "https://korra.work")
                        await email_service.send_scan_completed_email(
                            to_email=merchant_email,
                            merchant_name=merchant_name,
                            client_name=client_name,
                            measurement_summary=measurement_data,
                            dashboard_url=f"{host}/dashboard#measurements"
                        )
                        logger.info(f"📧 [TASK {task_id}] Email sent to merchant")
            except Exception as e:
                logger.warning(f"Email notification failed: {e}")
            
            # c) Webhook trigger to merchant
            try:
                from api.services.webhook_service import webhook_service
                await webhook_service.notify_scan_completed(
                    merchant_id=user_id,
                    measurement_data={
                        "id": task_id,
                        "client_name": client_name,
                        "biometrics": measurement_data,
                        "body_shape": body_shape,
                        "size_recommendation": size_rec,
                        "mesh_url": result.get("mesh_url")
                    }
                )
                logger.info(f"🪝 [TASK {task_id}] Webhook triggered")
            except Exception as e:
                logger.warning(f"Webhook trigger failed: {e}")

        if result.get("status") == "failed":
            from middleware.subscription_check import refund_credit
            await refund_credit(user_id)
            logger.info(f"♻️ [TASK {task_id}] Credit refunded due to AI core rejection.")

    except Exception as e:
        error_msg = f"ORCHESTRATOR_CRASH: {str(e)}"
        logger.error(f"❌ ORCHESTRATOR FAILED: {error_msg}")
        update_task(task_id, { "status": "failed", "error": error_msg })

        # PHASE 20: REFUND PROTOCOL
        from middleware.subscription_check import refund_credit
        await refund_credit(user_id)

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
        # Enforce merchant credits for dashboard scans
        if not user.get('is_admin'):
            from middleware.subscription_check import check_and_decrement_credits
            if not await check_and_decrement_credits(user['user_id']):
                raise HTTPException(status_code=402, detail="Insufficient credits for extraction.")

        task_id = str(uuid.uuid4())
        front_bytes = await front.read()
        side_bytes = await side.read()
        
        # Validate input
        if not front_bytes or not side_bytes:
            raise HTTPException(status_code=400, detail="Empty image files")
        if height < 50 or height > 250:
            raise HTTPException(status_code=400, detail="Invalid height")
            
        track_usage(user['api_key'])
        update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat(), "height": height, "gender": gender})
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
    client_name: str = Form("Widget Customer"),
    payment_reference: Optional[str] = Form(None),
    client_user_id: Optional[str] = Form(None)
):
    try:
        # 1. Payment Verification Gate
        paid = False
        if payment_reference:
            # Verify single-scan payment ($0.50)
            from api.routes.payments import paystack_service
            verify = paystack_service.verify_payment(payment_reference)
            if verify['status'] and verify['data']['status'] == 'success':
                paid = True

        if not paid:
            # Try merchant credits
            from middleware.subscription_check import check_and_decrement_credits
            if not await check_and_decrement_credits(merchant_id):
                raise HTTPException(status_code=402, detail="Payment Required: Merchant has 0 credits and no single-scan reference provided.")

        # 2. Process Task
        task_id = str(uuid.uuid4())
        front_bytes = await front.read()
        side_bytes = await side.read()
        
        if not front_bytes or not side_bytes: raise HTTPException(status_code=400, detail="Empty image files")
            
update_task(task_id, {"status": "queued", "created_at": datetime.utcnow().isoformat(), "height": height, "gender": gender})
        # Pass client_user_id for dual-account persistence
        background_tasks.add_task(run_extraction_task, task_id, front_bytes, side_bytes, height, gender, client_name, merchant_id, client_user_id)
        return {"status": "accepted", "task_id": task_id}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Widget extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start widget extraction")

@router.get("/measurements/status/{task_id}")
async def get_extraction_status(task_id: str):
    # ULTRA-RESILIENT STATUS CHECK
    try:
        # Fast path: in-memory lookup
        task = EXTRACTION_TASKS.get(task_id)
        if task:
            return task
        
        # Fallback: disk lookup
        try:
            tasks = load_tasks()
            task = tasks.get(task_id)
            if task:
                # Sync memory if found on disk
                EXTRACTION_TASKS[task_id] = task
                return task
        except: pass
        
        # FINAL PROTECTION: If task was accepted but not yet updated in store
        # we return a synthetic "queued" state instead of a scary 404.
        # This prevents "Task Not Found" during the split-second registration window.
        return {"status": "queued", "created_at": datetime.utcnow().isoformat(), "synthetic": True}
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {"status": "processing", "error": "Handshake jitter"}

@router.post("/refinement/impute")
async def impute_biometrics(gender: str, data: dict):
    """
    Phase 26: API Hook for Biometric Imputation
    """
    try:
        refined = imputation_service.impute(gender, data)
        return {"status": "success", "refined_biometrics": refined}
    except Exception as e:
        logger.error(f"Imputation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
