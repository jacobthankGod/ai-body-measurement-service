"""
System Health Routes | Phase 18: Autonomous Infrastructure
=========================================================
"""
from fastapi import APIRouter, BackgroundTasks
# from api.services.extract_measurements import get_brain_integrity # MOVED TO LATE IMPORT
import os
import platform
import urllib.request
import tarfile
import logging
from pathlib import Path
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("KORRA_HEALTH")

BASE_DIR = Path(os.getcwd()).resolve()
MODELS_DIR = BASE_DIR / "models"

@router.get("/health")
async def health_check():
    """Returns absolute infrastructure status with GPU and granular integrity checks."""
    try:
        from api.services.extract_measurements import get_brain_integrity
        ai_integrity = get_brain_integrity()

        # Granular check for research weights
        ai_integrity["model_ckpt_index"] = (MODELS_DIR / "model.ckpt-667589.index").exists()
        ai_integrity["model_ckpt_data"] = (MODELS_DIR / "model.ckpt-667589.data-00000-of-00001").exists()

    except Exception as e:
        logger.error(f"Health integrity check failed: {e}")
        ai_integrity = { "error": str(e) }

    # GPU DETECTION
    gpu_active = False
    gpu_details = "None"
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        gpu_active = len(gpus) > 0
        if gpu_active: gpu_details = str(gpus)
    except: pass

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.15",
        "environment": os.environ.get("EXTERNAL_URL", "production"),
        "platform": platform.system(),
        "acceleration": "GPU-Enabled" if gpu_active else "CPU-Stable (Optimized)",
        "gpu_details": gpu_details,
        "ai_integrity": ai_integrity,
        "paths": {
            "root": str(BASE_DIR),
            "models": str(MODELS_DIR)
        }
    }

def restore_brain_sync():
    """High-speed restoration of 385MB research weights from official mirror."""
    logger.info("🚀 UNICORN RESTORATION: Manually Fetching AI Brain Assets...")
    # Verified Berkeley Research Mirror (200 OK)
    url = "https://people.eecs.berkeley.edu/~kanazawa/cachedir/hmr/models.tar.gz"
    dest = BASE_DIR / "hmr_restore.tar.gz"
    try:
        urllib.request.urlretrieve(url, dest)
        logger.info("📦 Extracting AI Brain to Root...")
        with tarfile.open(dest, 'r:gz') as tar:
            tar.extractall(BASE_DIR) # Tar contains 'models/' folder
        os.remove(dest)
        logger.info("✅ RESTORATION COMPLETE: AI Brain Locked and Loaded.")
    except Exception as e:
        logger.error(f"❌ RESTORATION FAILED: {e}")

@router.post("/health/restore")
async def restore_health(background_tasks: BackgroundTasks):
    """Fallback restoration trigger (Admin UI)."""
    background_tasks.add_task(restore_brain_sync)
    return {
        "status": "Restoration Initiated",
        "message": "Fetching 385MB Weights in background. Monitor integrity in 60s."
    }
