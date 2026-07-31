"""
Garment Model Serving Route
============================
Serves 3D garment models (GLB) with proper caching headers.
"""
import os
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
logger = logging.getLogger("KORRA_GARMENT_MODELS")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "public" / "assets"

@router.get("/garment-models/agbada")
async def get_agbada_model():
    target = ASSETS_DIR / "agbada_draco.glb"
    if not target.exists():
        target = ASSETS_DIR / "agbada_cloth_model.glb"
    if not target.exists():
        logger.error(f"Agbada model not found at {target}")
        raise HTTPException(status_code=404, detail="Garment model not found")
    return FileResponse(
        str(target),
        media_type="model/gltf-binary",
        headers={
            "Cache-Control": "public, max-age=2592000",  # 30 days
            "Content-Disposition": "inline",
        }
    )

@router.get("/garment-models/huipil")
async def get_huipil_model():
    target = ASSETS_DIR / "huipil1_reduced.glb"
    if not target.exists():
        target = ASSETS_DIR / "huipil1.glb"
    if not target.exists():
        logger.error(f"Huipil model not found at {target}")
        raise HTTPException(status_code=404, detail="Garment model not found")
    return FileResponse(
        str(target),
        media_type="model/gltf-binary",
        headers={
            "Cache-Control": "public, max-age=2592000",  # 30 days
            "Content-Disposition": "inline",
        }
    )
