"""
Virtual Try-On Route | OOTDiffusion via Replicate + Snapchat Camera Kit
========================================================================
POST /api/v2/tryon — Run OOTDiffusion on a person photo + garment image.
POST /api/v2/tryon/capture — Save Camera Kit capture to storage.
GET /api/v2/tryon/captures — Get user's try-on captures.
"""
import os
import uuid
import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from api.services.database_service import DatabaseService
from api.services.tryon_service import TryOnService
from api.routes.measurements import get_current_user

router = APIRouter()
logger = logging.getLogger("KORRA_TRYON")

BASE_DIR = Path(os.getcwd()).resolve()

@router.post("/tryon")
async def virtual_tryon(
    scan_id: Optional[str] = Form(None),
    attire: Optional[str] = Form(None),
    person_image: Optional[UploadFile] = File(None),
    garment_image: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Virtual try-on using OOTDiffusion via Replicate.
    
    Accepts:
    - person_image: optional photo of the person (if not provided, uses scan's front photo)
    - garment_image: photo of the garment to try on
    - scan_id: optional scan ID to associate result with
    - attire: optional attire type for category mapping (t-shirt, dress, etc.)
    """
    user_id = user.get("user_id")

    # 1. Upload garment image to Supabase storage
    garment_bytes = await garment_image.read()
    if not garment_bytes:
        raise HTTPException(status_code=400, detail="Garment image is required")

    garment_storage_url = DatabaseService.upload_photo_to_storage(
        garment_bytes, user_id, str(uuid.uuid4()), "garment"
    )
    if not garment_storage_url:
        raise HTTPException(status_code=500, detail="Failed to upload garment image")

    # 2. Get person image URL
    person_image_url = None

    if person_image:
        person_bytes = await person_image.read()
        if person_bytes:
            person_image_url = DatabaseService.upload_photo_to_storage(
                person_bytes, user_id, str(uuid.uuid4()), "person"
            )

    if not person_image_url and scan_id:
        # Try to get person image from scan front photo
        try:
            db = DatabaseService.get_client()
            res = db.table("measurements").select("photo_front_url, biometrics").eq("id", scan_id).execute()
            if res.data:
                person_image_url = res.data[0].get("photo_front_url")
                if not person_image_url:
                    # Fallback: check biometrics for stored images
                    biometrics = res.data[0].get("biometrics", {})
                    person_image_url = biometrics.get("__scan_photo_front_url")
        except Exception as e:
            logger.warning(f"Could not fetch scan photo: {e}")

    if not person_image_url:
        raise HTTPException(
            status_code=400,
            detail="Person image is required. Upload one or provide a scan_id with a front photo."
        )

    # 3. Determine OOTDiffusion category
    category = TryOnService.get_category(attire or "t-shirt")

    # 4. Run OOTDiffusion
    try:
        result_urls = TryOnService.run_tryon(
            person_image_url=person_image_url,
            garment_image_url=garment_storage_url,
            category=category,
        )
    except Exception as e:
        logger.error(f"Try-on inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Try-on failed: {str(e)}")

    if not result_urls:
        raise HTTPException(status_code=500, detail="Try-on produced no output")

    # 5. Download and persist results to Supabase storage
    import httpx
    persisted_urls = []
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            for i, url in enumerate(result_urls):
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        result_bytes = resp.content
                        result_storage_url = DatabaseService.upload_photo_to_storage(
                            result_bytes, user_id, str(uuid.uuid4()), f"tryon_result_{i}"
                        )
                        if result_storage_url:
                            persisted_urls.append(result_storage_url)
                        else:
                            persisted_urls.append(url)
                    else:
                        persisted_urls.append(url)
                except Exception as e:
                    logger.warning(f"Failed to persist result {i}: {e}")
                    persisted_urls.append(url)
    except Exception as e:
        logger.warning(f"Failed to download/persist results: {e}")
        persisted_urls = result_urls

    # 6. Optionally store result on the scan record
    if scan_id and persisted_urls:
        try:
            db = DatabaseService.get_client()
            scan = db.table("measurements").select("biometrics").eq("id", scan_id).execute()
            if scan.data:
                biometrics = scan.data[0].get("biometrics", {}) or {}
                tryon_history = biometrics.get("__tryon_history", [])
                tryon_history.append({
                    "attire": attire or "custom",
                    "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                    "result_urls": persisted_urls,
                    "garment_url": garment_storage_url,
                })
                biometrics["__tryon_history"] = tryon_history
                db.table("measurements").update({"biometrics": biometrics}).eq("id", scan_id).execute()
        except Exception as e:
            logger.warning(f"Failed to save tryon history to scan: {e}")

    return {
        "success": True,
        "result_urls": persisted_urls,
        "person_image_url": person_image_url,
        "garment_image_url": garment_storage_url,
        "category": category,
    }


# ============================================================
# Snapchat Camera Kit Capture Endpoints
# ============================================================

@router.post("/tryon/capture")
async def save_camerakit_capture(
    photo: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    outfit_id: Optional[str] = Form(None),
    lens_id: Optional[str] = Form(None),
    group_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
):
    """
    Save a Camera Kit capture to Supabase storage.
    
    This endpoint is called from the frontend after a user captures
    a photo using the Snapchat Camera Kit virtual try-on feature.
    """
    try:
        # Read photo bytes
        photo_bytes = await photo.read()
        if not photo_bytes:
            raise HTTPException(status_code=400, detail="Photo is required")
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        capture_id = str(uuid.uuid4())[:8]
        filename = f"tryon_{timestamp}_{capture_id}.png"
        
        # Upload to Supabase storage
        storage_path = f"tryon_captures/{user_id or 'anonymous'}/{filename}"
        photo_url = DatabaseService.upload_photo_to_storage(
            photo_bytes, user_id or 'anonymous', filename, "tryon_capture"
        )
        
        if not photo_url:
            raise HTTPException(status_code=500, detail="Failed to upload capture")
        
        # Save metadata to database
        db = DatabaseService.get_client()
        capture_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id or "anonymous",
            "outfit_id": outfit_id,
            "lens_id": lens_id,
            "group_id": group_id,
            "photo_url": photo_url,
            "filename": filename,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": json.loads(metadata) if metadata else {},
        }
        
        db.table("tryon_captures").insert(capture_record).execute()
        
        logger.info(f"Camera Kit capture saved: {filename} for user {user_id}")
        
        return {
            "success": True,
            "capture_id": capture_record["id"],
            "photo_url": photo_url,
            "filename": filename,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save Camera Kit capture: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save capture: {str(e)}")


@router.get("/tryon/captures")
async def get_captures(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of captures to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get user's try-on captures.
    
    Returns a list of Camera Kit captures for the specified user,
    ordered by creation date (newest first).
    """
    try:
        db = DatabaseService.get_client()
        
        result = (
            db.table("tryon_captures")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        captures = result.data if result.data else []
        
        # Get total count
        count_result = (
            db.table("tryon_captures")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        total = count_result.count if hasattr(count_result, 'count') else len(captures)
        
        return {
            "success": True,
            "captures": captures,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"Failed to get captures: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get captures: {str(e)}")


@router.delete("/tryon/capture/{capture_id}")
async def delete_capture(
    capture_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
):
    """
    Delete a try-on capture.
    
    Only the owner of the capture can delete it.
    """
    try:
        db = DatabaseService.get_client()
        
        # Verify ownership
        result = (
            db.table("tryon_captures")
            .select("user_id, filename")
            .eq("id", capture_id)
            .single()
            .execute()
        )
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Capture not found")
        
        if result.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this capture")
        
        # Delete from storage
        filename = result.data["filename"]
        # DatabaseService.delete_photo_from_storage(filename, "tryon_capture")  # Implement if needed
        
        # Delete from database
        db.table("tryon_captures").delete().eq("id", capture_id).execute()
        
        logger.info(f"Capture deleted: {capture_id} by user {user_id}")
        
        return {"success": True, "message": "Capture deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete capture: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete capture: {str(e)}")
