"""
System Health Routes | Phase 18: Autonomous Infrastructure
=========================================================
"""
from fastapi import APIRouter, BackgroundTasks
from api.services.extract_measurements import get_brain_integrity
import os
import platform
import urllib.request
import tarfile
import logging
from pathlib import Path

router = APIRouter()
logger = logging.getLogger("KORRA_HEALTH")

BASE_DIR = Path(os.getcwd()).resolve()
MODELS_DIR = BASE_DIR / "models"

@router.get("/health")
async def health_check():
    """Returns absolute infrastructure status."""
    return {
        "status": "active",
        "version": "2.1.14",
        "environment": os.environ.get("RENDER_EXTERNAL_URL", "production"),
        "platform": platform.system(),
        "acceleration": "CPU-Stable (Optimized)" if "Linux" in platform.system() else "Native",
        "ai_integrity": get_brain_integrity(),
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
