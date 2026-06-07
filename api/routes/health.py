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
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(os.getcwd()).resolve()
MODELS_DIR = BASE_DIR / "models"

@router.get("/health")
async def health_check():
    """Returns absolute infrastructure status."""
    return {
        "status": "active",
        "version": "2.1.8",
        "environment": os.environ.get("RENDER_EXTERNAL_URL", "development"),
        "platform": platform.system(),
        "acceleration": "CPU-Stable (Optimized)" if "Linux" in platform.system() else "Native",
        "ai_integrity": get_brain_integrity()
    }

def restore_brain_sync():
    """High-speed restoration of 347MB HMR weights."""
    print("🚀 UNICORN RESTORATION: Manually Fetching AI Brain Assets...")
    url = "https://dl.dropboxusercontent.com/s/e8s7q5bq7a5s1bq/hmr_model.tar.gz"
    dest = MODELS_DIR / "hmr_restore.tar.gz"
    try:
        MODELS_DIR.mkdir(exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        with tarfile.open(dest, 'r:gz') as tar:
            tar.extractall(MODELS_DIR)
        os.remove(dest)
        print("✅ RESTORATION COMPLETE: AI Brain Locked.")
    except Exception as e:
        print(f"❌ RESTORATION FAILED: {e}")

@router.post("/health/restore")
async def restore_health(background_tasks: BackgroundTasks):
    """Fallback restoration trigger (Admin UI)."""
    background_tasks.add_task(restore_brain_sync)
    return {"status": "Restoration Initiated", "message": "Fetching 347MB Weights."}
