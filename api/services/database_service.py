"""
Supabase Database Service | UNICORN-GRADE PERSISTENCE
=====================================================
Handles atomic persistence for API keys, usage, 3D Biometrics, and Invitations.
Now with Supabase Storage integration for mesh files and photos.
"""
import os
import json
import logging
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
# from supabase import create_client, Client # MOVED TO LATE IMPORT

logger = logging.getLogger("KORRA_DB")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

class DatabaseService:
    _instance: Optional[Any] = None

    @classmethod
    def get_client(cls) -> Optional[Any]:
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_KEY: 
                logger.error("❌ DatabaseService: SUPABASE_URL or SUPABASE_KEY is None in ENV!")
                return None
            try:
                from supabase import create_client
                cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e: 
                logger.error(f"❌ DatabaseService: Failed to create client: {e}")
                return None
        return cls._instance

    @classmethod
    def create_invitation(cls, merchant_id: str, client_name: str) -> str:
        """Atomic Invitation Persistence."""
        client = cls.get_client()
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=1)
        try:
            client.table("invitations").insert({
                "token": token,
                "merchant_id": merchant_id,
                "client_name": client_name,
                "expires_at": expires_at.isoformat()
            }).execute()
            return token
        except Exception as e:
            logger.error(f"Invite Persistence Failed: {e}")
            return None

    @classmethod
    def verify_invitation(cls, token: str) -> Optional[dict]:
        """Verify invitation against PostgreSQL vault."""
        client = cls.get_client()
        try:
            res = client.table("invitations").select("*").eq("token", token).execute()
            if not res.data:
                return None
            invite = res.data[0]
            if datetime.fromisoformat(invite["expires_at"]) < datetime.utcnow():
                return None
            return invite
        except Exception as e:
            return None

    @classmethod
    def upload_mesh_to_storage(cls, file_path: Path, task_id: str) -> Optional[str]:
        """Upload .obj mesh file to Supabase Storage 'meshes' bucket.
        Returns public URL on success, None on failure.
        """
        client = cls.get_client()
        if not client:
            logger.error("❌ [STORAGE] No Supabase client — cannot upload mesh")
            return None
        if not file_path or not file_path.exists():
            logger.error(f"❌ [STORAGE] Mesh file not found: {file_path}")
            return None

        try:
            file_name = f"meshes/{file_path.name}"
            file_bytes = file_path.read_bytes()
            file_size = len(file_bytes)

            logger.info(f"📤 [STORAGE] Uploading mesh {file_path.name} ({file_size} bytes) to 'meshes' bucket")

            client.storage.from_('meshes').upload(
                file_name,
                file_bytes,
                {"content-type": "model/obj"}
            )

            public_url = client.storage.from_('meshes').get_public_url(file_name)
            logger.info(f"✅ [STORAGE] Mesh uploaded: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"❌ [STORAGE] Mesh upload failed: {e}")
            return None

    @classmethod
    def upload_photo_to_storage(cls, photo_bytes: bytes, user_id: str, task_id: str, side: str) -> Optional[str]:
        """Upload a photo to Supabase Storage 'scan_photos' bucket.
        side: 'front' or 'side'
        Returns public URL on success, None on failure.
        """
        client = cls.get_client()
        if not client:
            logger.error("❌ [STORAGE] No Supabase client — cannot upload photo")
            return None
        if not photo_bytes:
            logger.error(f"❌ [STORAGE] Empty photo bytes for {side}")
            return None

        try:
            file_name = f"{user_id}/{task_id}/{side}.png"
            file_size = len(photo_bytes)

            logger.info(f"📤 [STORAGE] Uploading {side} photo ({file_size} bytes) to 'scan_photos' bucket")

            client.storage.from_('scan_photos').upload(
                file_name,
                photo_bytes,
                {"content-type": "image/png"}
            )

            public_url = client.storage.from_('scan_photos').get_public_url(file_name)
            logger.info(f"✅ [STORAGE] {side} photo uploaded: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"❌ [STORAGE] {side} photo upload failed: {e}")
            return None

    @classmethod
    def save_measurement(cls, user_id: str, client_name: str, height: float, gender: str, biometrics: dict, landmarks: dict = None, mesh_url: str = None, body_shape: str = None, size_rec: str = None, client_user_id: str = None, clinical_realism_index: float = None, mesh_storage_url: str = None, photo_front_url: str = None, photo_side_url: str = None, smpl_params: dict = None, joints3d: list = None, tpose_mesh_url: str = None):
        """
        Save measurement to database.
        
        CRITICAL: Saves to BOTH merchant AND client accounts for dual-ownership.
        - user_id: The merchant/professional who requested the scan
        - client_user_id: The client's own account (optional but recommended for ownership)
        
        Now persists mesh_storage_url and photo URLs for cloud-resilient storage.
        """
        client = cls.get_client()
        if not client:
            logger.error("❌ DatabaseService: Supabase client is None - ENV variables missing!")
            return None

        if not user_id:
            logger.error("❌ DatabaseService: user_id is None — cannot persist measurement")
            return None

        results = []

        # Phase 0: Map SMPL params and joints to dedicated columns
        # These are used for the self-improving accuracy flywheel (Pillar 1).
        # We also keep them in biometrics for backward compatibility in the UI.
        biometrics_with_smpl = biometrics.copy() if biometrics else {}
        if smpl_params:
            biometrics_with_smpl['__smpl_params'] = smpl_params
        if joints3d:
            biometrics_with_smpl['__joints3d'] = joints3d
            if len(joints3d) > 0:
                logger.info(f"✅ SMPL params prepared: {len(smpl_params.get('shape', []))} shape dims, {len(joints3d)} joints")

        # 1. Save under merchant's account (for professional's dashboard)
        try:
            merchant_payload = {
                "user_id": user_id,
                "client_name": client_name,
                "height": height,
                "gender": gender,
                "biometrics": biometrics_with_smpl,
                "landmarks_3d": landmarks if landmarks else {},
                "mesh_url": mesh_url,
                "mesh_storage_url": mesh_storage_url,
                "photo_front_url": photo_front_url,
                "photo_side_url": photo_side_url,
                "body_shape": body_shape,
                "size_recommendation": size_rec,
                "clinical_realism_index": clinical_realism_index,
                "tpose_mesh_url": tpose_mesh_url,
                "smpl_params": smpl_params,
                "joints_3d": joints3d,
                "source_of_truth": True,
                "created_at": datetime.utcnow().isoformat()
            }
            logger.info(f"💾 DatabaseService: Saving to merchant {user_id} for {client_name}")

            response = client.table("measurements").insert(merchant_payload).execute()
            if response.data:
                logger.info(f"✅ Merchant measurement saved! ID: {response.data[0].get('id')}")
                results.append({"account": "merchant", "id": response.data[0].get('id')})
            else:
                logger.error("❌ Merchant measurement insert failed — no data returned")
        except Exception as e:
            logger.error(f"❌ Merchant measurement save FAILED: {e}")

        # 2. Save under client's own account (client ownership, if different from merchant)
        if client_user_id and client_user_id != user_id:
            try:
                client_payload = {
                    "user_id": client_user_id,
                    "client_name": client_name,
                    "height": height,
                    "gender": gender,
                    "biometrics": biometrics_with_smpl,
                    "landmarks_3d": landmarks if landmarks else {},
                    "mesh_url": mesh_url,
                    "mesh_storage_url": mesh_storage_url,
                    "photo_front_url": photo_front_url,
                    "photo_side_url": photo_side_url,
                    "body_shape": body_shape,
                    "size_recommendation": size_rec,
                    "clinical_realism_index": clinical_realism_index,
                    "tpose_mesh_url": tpose_mesh_url,
                    "smpl_params": smpl_params,
                    "joints_3d": joints3d,
                    "source_of_truth": True,
                    "created_at": datetime.utcnow().isoformat()
                }
                logger.info(f"💾 DatabaseService: Saving to client {client_user_id}")

                response = client.table("measurements").insert(client_payload).execute()
                if response.data:
                    logger.info(f"✅ Client measurement saved! ID: {response.data[0].get('id')}")
                    results.append({"account": "client", "id": response.data[0].get('id')})
                else:
                    logger.error("❌ Client measurement insert failed — no data returned")
            except Exception as e:
                logger.error(f"❌ Client measurement save FAILED: {e}")

        # Phase 31: Structured return dict
        if results:
            return {"status": "saved", "accounts": results}
        return {"status": "failed", "accounts": [], "error": "No measurements saved"}

    @classmethod
    def update_measurement(cls, measurement_id: str, data: dict):
        """Update existing measurement entry."""
        client = cls.get_client()
        if not client: return None
        try:
            return client.table("measurements").update(data).eq("id", measurement_id).execute()
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            return None

    @classmethod
    def get_api_key(cls, api_key: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client: return None
        try:
            response = client.table("api_keys").select("*").eq("key", api_key).eq("is_active", True).execute()
            return response.data[0] if response.data else None
        except: return None

    @classmethod
    def update_usage(cls, api_key: str):
        client = cls.get_client()
        if not client: return
        try:
            res = client.table("usage_logs").select("*").eq("api_key", api_key).execute()
            if res.data:
                client.table("usage_logs").update({"total_count": res.data[0]["total_count"] + 1, "last_used": datetime.now().isoformat()}).eq("api_key", api_key).execute()
            else:
                client.table("usage_logs").insert({"api_key": api_key, "total_count": 1, "last_used": datetime.now().isoformat()}).execute()
        except: pass
