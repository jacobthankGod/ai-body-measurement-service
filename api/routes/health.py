"""
System Health Routes | Phase 17: Infrastructure Diagnostics
========================================================
"""
from fastapi import APIRouter
from api.services.extract_measurements import get_brain_integrity
import os
import platform

router = APIRouter()

@router.get("/health")
async def health_check():
    """Returns absolute infrastructure status."""
    return {
        "status": "active",
        "version": "2.1.6",
        "environment": os.environ.get("RENDER_EXTERNAL_URL", "development"),
        "platform": platform.system(),
        "ai_integrity": get_brain_integrity()
    }
