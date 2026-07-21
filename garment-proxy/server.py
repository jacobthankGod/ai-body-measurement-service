"""
Garment Reconstruction Proxy Server
Zero local state — all persistence via Supabase.
Auto-recovers on EC2 rebuild. Tunnel URL auto-registered by Kaggle keep-alive.
"""
import os
import io
import json
import time
import hashlib
import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
try:
    import imagehash
    from PIL import Image as PILImage
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
import uvicorn
import logging

logger = logging.getLogger("garment-proxy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── Config (all from env, no local files) ──────────────────────
KAGGLE_TUNNEL_URL = os.getenv("KAGGLE_TUNNEL_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://blsettabymllulsxtziw.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsc2V0dGFieW1sbHVsc3h0eml3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAwNTY3NjksImV4cCI6MjA5NTYzMjc2OX0.PuMsTbgyRRcCQ04Y7Y9Y75WjRqmzgMP4S2_B4372V_U")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsc2V0dGFieW1sbHVsc3h0eml3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDA1Njc2OSwiZXhwIjoyMDk1NjMyNzY5fQ.oQz1KDOXuPdP2l35pXQVjry5stoe9_Wp4nzEDwPXX2I")
MAX_RETRIES = 5
TUNNEL_CACHE_FILE = "/tmp/kaggle_tunnel_url.txt"
PERCEPTUAL_HASH_CACHE = {}  # {phash: result_zip}
PHASH_CACHE_MAX = 50

# ── Load cached tunnel URL from disk (survives proxy restart) ──
def _load_cached_tunnel() -> str:
    try:
        with open(TUNNEL_CACHE_FILE) as f:
            url = f.read().strip()
            if url.startswith("http"):
                print(f"[Tunnel] Loaded cached URL: {url}")
                return url
    except Exception:
        pass
    return ""

# Override env var with cached file if env is empty
if not KAGGLE_TUNNEL_URL:
    KAGGLE_TUNNEL_URL = _load_cached_tunnel()

# ── Supabase helpers (raw httpx, no SDK) ──────────────────────
async def sb_query(table: str, select: str = "*", params: dict = None, method: str = "GET", json_data: dict = None):
    """Raw Supabase REST query via httpx."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    # Use service_role for writes (POST/PATCH), anon for reads
    auth_key = SUPABASE_SERVICE_KEY if method in ("POST", "PATCH") else SUPABASE_ANON_KEY
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {auth_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation" if method in ("POST", "PATCH") else "",
    }
    query_params = dict(params or {})
    if select and "select" not in query_params:
        query_params["select"] = select
    async with httpx.AsyncClient(timeout=15) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers, params=query_params)
        elif method == "POST":
            resp = await client.post(url, headers=headers, json=json_data)
        elif method == "PATCH":
            resp = await client.patch(url, headers=headers, params=query_params, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        return resp

async def sb_upsert_job(job_id: str, user_id: str, image_hash: str):
    """Insert a new job into Supabase."""
    await sb_query("garment_jobs", method="POST", json_data={
        "id": job_id,
        "user_id": user_id,
        "status": "processing",
        "image_hash": image_hash,
    })

async def sb_update_job(job_id: str, data: dict):
    """Update job status/result in Supabase."""
    await sb_query("garment_jobs", method="PATCH", params={"id": f"eq.{job_id}"}, json_data=data)

async def sb_get_job(job_id: str) -> dict | None:
    """Fetch a job from Supabase."""
    resp = await sb_query("garment_jobs", select="*", params={"id": f"eq.{job_id}"})
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

# ── FastAPI app ────────────────────────────────────────────────
app = FastAPI(title="Garment Reconstruction Proxy")

# Phase 208: Background pre-warm task
@app.on_event("startup")
async def start_prewarm_loop():
    async def _prewarm_loop():
        while True:
            await asyncio.sleep(120)  # Every 2 minutes
            if KAGGLE_TUNNEL_URL:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(f"{KAGGLE_TUNNEL_URL}/api/v1/prewarm")
                        if resp.status_code == 200:
                            data = resp.json()
                            logger.info(f"Prewarm: {data.get('elapsed_sec', '?')}s — {data.get('results', {})}")
                except Exception as e:
                    logger.debug(f"Prewarm failed (non-critical): {e}")
    asyncio.create_task(_prewarm_loop())

# ── Rate limiting (in-memory, resets on restart — fine for proxy) ──
rate_limits: dict[str, tuple[int, float]] = {}
RATE_LIMIT = 10

def check_rate_limit(ip: str) -> bool:
    now = time.time()
    if ip not in rate_limits:
        rate_limits[ip] = (1, now)
        return True
    count, window_start = rate_limits[ip]
    if now - window_start > 60:
        rate_limits[ip] = (1, now)
        return True
    if count >= RATE_LIMIT:
        return False
    rate_limits[ip] = (count + 1, window_start)
    return True

# ── JWT Auth ───────────────────────────────────────────────────
async def verify_jwt(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY},
            )
            if resp.status_code == 200:
                return resp.json()["id"]
            print(f"[AUTH] Supabase rejected token: {resp.status_code} {resp.text[:200]}")
            raise HTTPException(401, "Invalid or expired token")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] JWT verification network error: {e}")
        raise HTTPException(502, "Auth service unavailable")

# ── VTO rate limit (Phase 204): 5 per user per day, tracked in Supabase ──
VTO_DAILY_LIMIT = 5

async def sb_get_vto_count_today(user_id: str) -> int:
    """Count VTO generations for this user today (UTC)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    resp = await sb_query(
        "vto_usage",
        select="id",
        params={
            "user_id": f"eq.{user_id}",
            "created_at": f"gte.{today}T00:00:00Z",
        },
    )
    if resp.status_code == 200:
        return len(resp.json())
    return 0

async def sb_record_vto_usage(user_id: str):
    """Record a VTO generation for rate tracking."""
    await sb_query("vto_usage", method="POST", json_data={
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

async def sb_get_vto_reset_time(user_id: str) -> str:
    """Get when the user's daily VTO limit resets (next UTC midnight)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{today}T23:59:59Z"

async def check_subscription(user_id: str) -> dict:
    """Check if user has an active subscription. Returns {active, plan, expires_at}."""
    resp = await sb_query(
        "subscriptions",
        select="*",
        params={
            "user_id": f"eq.{user_id}",
            "status": f"eq.active",
            "select": "*",
        },
    )
    if resp.status_code == 200:
        subs = resp.json()
        if subs:
            sub = subs[0]
            return {"active": True, "plan": sub.get("plan", "free"), "expires_at": sub.get("expires_at")}
    return {"active": False, "plan": "free", "expires_at": None}

async def sb_check_scan_ownership(user_id: str, scan_id: str) -> bool:
    """Verify user owns this scan."""
    resp = await sb_query(
        "scans",
        select="id",
        params={"id": f"eq.{scan_id}", "user_id": f"eq.{user_id}"},
    )
    return resp.status_code == 200 and len(resp.json()) > 0


# ── Phase 151: Scan photo resolution ──
async def sb_get_scan_photos(scan_id: str) -> dict:
    """Get photo_front_url and photo_side_url from measurements table."""
    resp = await sb_query(
        "measurements",
        select="photo_front_url,photo_side_url",
        params={"id": f"eq.{scan_id}"},
    )
    if resp.status_code == 200:
        rows = resp.json()
        if rows:
            return rows[0]
    return {}


# ── Phase 152: Refined photo persistence ──
async def sb_save_refined_photos(scan_id: str, front_url: str = None, side_url: str = None, back_url: str = None):
    """Save refined neutral photo URLs to measurements table."""
    updates = {}
    if front_url:
        updates["refined_front_url"] = front_url
    if side_url:
        updates["refined_side_url"] = side_url
    if back_url:
        updates["refined_back_url"] = back_url
    if updates:
        await sb_query("measurements", method="PATCH", json_data=updates, params={"id": f"eq.{scan_id}"})


# ── Phase 155: Refined-back cache check ──
async def sb_get_refined_photos(scan_id: str) -> dict:
    """Check if refined photos already exist for this scan. Returns URLs or empty dict."""
    resp = await sb_query(
        "measurements",
        select="refined_front_url,refined_side_url,refined_back_url",
        params={"id": f"eq.{scan_id}"},
    )
    if resp.status_code == 200:
        rows = resp.json()
        if rows:
            row = rows[0]
            # Return only non-null URLs
            return {k: v for k, v in row.items() if v}
    return {}


# ── Phase 175: tryon_history persistence ──
async def sb_save_tryon_history(scan_id: str, result: dict):
    """
    Append a VTO result to the tryon_history JSONB array.
    result should contain: {angle, result_url, garment_type, garment_color, seed, created_at}
    """
    # Read current history
    resp = await sb_query(
        "measurements",
        select="tryon_history",
        params={"id": f"eq.{scan_id}"},
    )
    history = []
    if resp.status_code == 200:
        rows = resp.json()
        if rows and rows[0].get("tryon_history"):
            history = rows[0]["tryon_history"]
            if not isinstance(history, list):
                history = []

    history.append(result)

    # Keep only last 10 results
    history = history[-10:]

    await sb_query(
        "measurements",
        method="PATCH",
        json_data={"tryon_history": history},
        params={"id": f"eq.{scan_id}"},
    )


async def sb_get_tryon_history(scan_id: str) -> list:
    """Get VTO history for a scan."""
    resp = await sb_query(
        "measurements",
        select="tryon_history",
        params={"id": f"eq.{scan_id}"},
    )
    if resp.status_code == 200:
        rows = resp.json()
        if rows and rows[0].get("tryon_history"):
            return rows[0]["tryon_history"]
    return []


# ── Phase 152: Upload refined photo to Supabase storage ──
async def sb_upload_refined_photo(user_id: str, scan_id: str, angle: str, image_bytes: bytes) -> str:
    """Upload refined photo to scan_photos bucket. Returns public URL."""
    import hashlib
    path = f"{user_id}/{scan_id}/refined_{angle}.png"
    try:
        resp = await sb_query(
            "scan_photos",
            method="POST",
            json_data=None,
            params={"upsert": "true"},
        )
        # Use direct upload via httpx to Supabase storage API
        upload_url = f"{SUPABASE_URL}/storage/v1/object/scan_photos/{path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "image/png",
            "x-upsert": "true",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            upload_resp = await client.put(upload_url, content=image_bytes, headers=headers)
            if upload_resp.status_code in (200, 201):
                # Return public URL
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/scan_photos/{path}"
                return public_url
            else:
                logger.warning(f"Photo upload failed: {upload_resp.status_code} {upload_resp.text[:200]}")
                return ""
    except Exception as e:
        logger.warning(f"Photo upload error: {e}")
        return ""


# ── Phase 048: Upload result ZIP to Supabase Storage ──
async def sb_upload_result_zip(job_id: str, user_id: str, result_zip: bytes) -> str:
    """Upload reconstruction ZIP to garment_meshes bucket. Returns storage path."""
    path = f"{user_id}/{job_id}/result.zip"
    try:
        upload_url = f"{SUPABASE_URL}/storage/v1/object/garment_meshes/{path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/zip",
            "x-upsert": "true",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.put(upload_url, content=result_zip, headers=headers)
            if resp.status_code in (200, 201):
                return f"garment_meshes/{path}"
            else:
                logger.warning(f"ZIP upload failed: {resp.status_code} {resp.text[:200]}")
                return ""
    except Exception as e:
        logger.warning(f"ZIP upload error: {e}")
        return ""


# ── Phase 045: Persist SSE progress to Supabase garment_jobs ──
async def sb_update_progress(job_id: str, stage: str, progress: int, message: str):
    """Update progress stage/pct/message on garment_jobs row for SSE polling."""
    try:
        await sb_query(
            "garment_jobs",
            method="PATCH",
            params={"id": f"eq.{job_id}"},
            json_data={
                "progress_stage": stage,
                "progress_pct": progress,
                "progress_message": message,
            },
        )
    except Exception as e:
        logger.debug(f"Progress update failed for {job_id}: {e}")


# ── Phase 190: Face blur for privacy ──
def _blur_face(image_bytes: bytes) -> bytes:
    """Apply Gaussian blur to face region for privacy. Returns processed bytes."""
    try:
        import cv2
        import numpy as np
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
        for (x, y, w, h) in faces:
            roi = img[y:y+h, x:x+w]
            blurred = cv2.GaussianBlur(roi, (51, 51), 30)
            img[y:y+h, x:x+w] = blurred
        _, buf = cv2.imencode(".png", img)
        return buf.tobytes()
    except Exception:
        return image_bytes


@app.get("/api/v2/garment/health")
@app.get("/health")
async def health():
    kaggle_healthy = False
    if KAGGLE_TUNNEL_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{KAGGLE_TUNNEL_URL}/health")
                kaggle_healthy = resp.status_code == 200
        except Exception:
            pass
    return {
        "status": "healthy",
        "kaggle_backend": "connected" if kaggle_healthy else "disconnected",
        "tunnel_url": KAGGLE_TUNNEL_URL or "not registered",
        "sse_supported": True,
    }

@app.post("/api/v1/analytics")
@app.post("/api/v2/analytics")
async def analytics_sink(request: Request):
    """Accept analytics events and discard — no storage needed."""
    try:
        body = await request.json()
        events = body.get("events", [])
        print(f"[Analytics] Received {len(events)} events")
    except Exception:
        pass
    return {"ok": True}

@app.get("/api/v2/garment/reconstruct/progress/{kaggle_job_id}")
async def reconstruct_progress_sse(kaggle_job_id: str):
    """SSE relay — streams progress events from Kaggle to frontend, persists to Supabase."""
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")

    async def relay_events():
        # Resolve job_id from kaggle_job_id for Supabase updates
        job = await sb_query("garment_jobs", select="id", params={"id": f"eq.{kaggle_job_id}"})
        local_job_id = kaggle_job_id
        if job.status_code == 200 and job.json():
            local_job_id = job.json()[0].get("id", kaggle_job_id)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("GET", f"{KAGGLE_TUNNEL_URL}/api/v1/reconstruct/progress/{kaggle_job_id}") as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': 'SSE endpoint unavailable'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
                            # Phase 045: Persist progress to Supabase (fire-and-forget)
                            try:
                                data = json.loads(line[6:])
                                await sb_update_progress(
                                    local_job_id,
                                    data.get("stage", ""),
                                    data.get("progress", 0),
                                    data.get("message", ""),
                                )
                            except Exception:
                                pass
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': 'SSE connection timed out'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': f'SSE relay error: {str(e)[:100]}'})}\n\n"

    return StreamingResponse(
        relay_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v2/garment/tunnel-url")
async def get_tunnel_url():
    """Debug endpoint: return current tunnel URL and source."""
    cached = ""
    try:
        with open(TUNNEL_CACHE_FILE) as f:
            cached = f.read().strip()
    except Exception:
        pass
    return {
        "active_url": KAGGLE_TUNNEL_URL or "not set",
        "cached_on_disk": cached or "not cached",
        "url_match": KAGGLE_TUNNEL_URL == cached if KAGGLE_TUNNEL_URL and cached else "N/A",
        "retries_config": MAX_RETRIES,
    }

@app.post("/api/v2/garment/internal/tunnel")
async def update_tunnel(data: dict):
    global KAGGLE_TUNNEL_URL
    url = (data.get("url") or "").rstrip("/")
    if not url.startswith("https://") and not url.startswith("http://"):
        raise HTTPException(400, "Invalid tunnel URL")
    KAGGLE_TUNNEL_URL = url
    # Persist to disk so proxy restart doesn't lose it
    try:
        with open(TUNNEL_CACHE_FILE, "w") as f:
            f.write(url)
    except Exception as e:
        print(f"[Tunnel] Failed to cache URL to disk: {e}")
    print(f"Tunnel URL updated: {url}")
    return {"status": "ok", "tunnel_url": url}

def _compute_phash(image_bytes: bytes):
    """Compute perceptual hash of image for caching."""
    if not HAS_IMAGEHASH:
        return None
    try:
        img = PILImage.open(io.BytesIO(image_bytes))
        return str(imagehash.phash(img))
    except Exception:
        return None

def _check_phash_cache(phash: str):
    """Check if result exists in phash cache."""
    if phash and phash in PERCEPTUAL_HASH_CACHE:
        return PERCEPTUAL_HASH_CACHE[phash]
    return None

def _store_phash_cache(phash: str, result: dict):
    """Store result in phash cache with LRU eviction."""
    if not phash:
        return
    if len(PERCEPTUAL_HASH_CACHE) >= PHASH_CACHE_MAX:
        oldest = next(iter(PERCEPTUAL_HASH_CACHE))
        del PERCEPTUAL_HASH_CACHE[oldest]
    PERCEPTUAL_HASH_CACHE[phash] = result


@app.post("/api/v2/garment/reconstruct")
async def reconstruct_garment(
    request: Request,
    file: UploadFile = File(...),
    include_mesh: bool = True,
    include_pattern: bool = True,
):
    user_id = await verify_jwt(request.headers.get("authorization"))

    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(429, "Rate limit exceeded. Try again in 1 minute.")

    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected. Try again in a moment.")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 20MB)")
    image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]

    # Create job in Supabase
    job_id = hashlib.md5(f"{user_id}{image_hash}{time.time()}".encode()).hexdigest()[:12]
    req_id = job_id  # use job_id as request_id for correlation
    await sb_upsert_job(job_id, user_id, image_hash)

    # Quick tunnel liveliness pre-check (Phase 4)
    tunnel_alive = False
    if KAGGLE_TUNNEL_URL:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                hr = await c.get(f"{KAGGLE_TUNNEL_URL}/health")
                tunnel_alive = hr.status_code == 200
        except Exception:
            pass
    print(f"[{req_id}] Tunnel pre-check: {'ALIVE' if tunnel_alive else 'DEAD'} | URL: {KAGGLE_TUNNEL_URL[:60] if KAGGLE_TUNNEL_URL else 'NONE'}")

    # Forward to Kaggle async endpoint
    for attempt in range(MAX_RETRIES):
        attempt_start = time.time()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15.0, read=60.0, write=30.0, pool=10.0)) as client:
                fname = file.filename or "image.png"
                files = {"file": (fname, image_bytes, file.content_type or "image/png")}
                params = {"include_mesh": include_mesh, "include_pattern": include_pattern, "user_id": user_id}
                resp = await client.post(f"{KAGGLE_TUNNEL_URL}/api/v1/reconstruct", files=files, params=params)
                elapsed = time.time() - attempt_start

                if resp.status_code == 200:
                    data = resp.json()
                    kaggle_job_id = data.get("job_id")
                    if not kaggle_job_id:
                        print(f"[{req_id}] Attempt {attempt+1}/{MAX_RETRIES}: 200 but no job_id in {elapsed:.1f}s")
                        raise HTTPException(502, "No job_id returned from backend")
                    print(f"[{req_id}] Attempt {attempt+1}/{MAX_RETRIES}: OK (job={kaggle_job_id}) in {elapsed:.1f}s")
                    # Return job_id immediately — frontend polls/SSEs for progress
                    return JSONResponse({
                        "job_id": kaggle_job_id,
                        "status": "processing",
                    })
                else:
                    backend_detail = ""
                    try:
                        backend_detail = resp.json().get("detail", resp.text[:300])
                    except Exception:
                        backend_detail = resp.text[:300]
                    print(f"[{req_id}] Attempt {attempt+1}/{MAX_RETRIES}: HTTP {resp.status_code} in {elapsed:.1f}s: {backend_detail[:200]}")
                    await sb_update_job(job_id, {"status": "failed", "error_message": f"Backend {resp.status_code}: {backend_detail}"})
                    raise HTTPException(502, f"Backend error {resp.status_code}: {backend_detail}")

        except HTTPException:
            raise
        except httpx.TimeoutException:
            elapsed = time.time() - attempt_start
            print(f"[{req_id}] Attempt {attempt+1}/{MAX_RETRIES}: Timeout after {elapsed:.1f}s")
            await sb_update_job(job_id, {"status": "retrying", "error_message": f"Timeout attempt {attempt+1}"})
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            elapsed = time.time() - attempt_start
            print(f"[{req_id}] Attempt {attempt+1}/{MAX_RETRIES}: {type(e).__name__}: {e} after {elapsed:.1f}s")
            await sb_update_job(job_id, {"status": "retrying", "error_message": f"{type(e).__name__}: {str(e)[:100]}"})
            await asyncio.sleep(2 ** attempt)

    await sb_update_job(job_id, {"status": "failed", "error_message": "Service unavailable after retries"})
    print(f"[{req_id}] ALL {MAX_RETRIES} attempts failed — returning 503")
    raise HTTPException(503, "Garment reconstruction service temporarily unavailable")

async def poll_and_return_job(req_id: str, job_id: str, kaggle_job_id: str, max_wait: int = 300) -> StreamingResponse:
    start = time.time()
    while time.time() - start < max_wait:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{KAGGLE_TUNNEL_URL}/api/v1/job/{kaggle_job_id}")
                elapsed = time.time() - start
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/zip"):
                    result_zip = resp.content

                    # Phase 048: Upload ZIP to Supabase storage
                    result_url = ""
                    job = await sb_get_job(job_id)
                    user_id = job.get("user_id", "") if job else ""
                    if user_id:
                        result_url = await sb_upload_result_zip(job_id, user_id, result_zip)

                    await sb_update_job(job_id, {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result_url": result_url if result_url else None,
                    })
                    print(f"[{req_id}] Job {kaggle_job_id} completed in {elapsed:.0f}s ({len(result_zip)} bytes)")
                    return StreamingResponse(
                        io.BytesIO(result_zip),
                        media_type="application/zip",
                        headers={"X-Cache": "MISS", "X-Job-Id": job_id}
                    )
                elif resp.status_code == 500:
                    error_data = resp.json()
                    err_msg = error_data.get("error", "unknown")
                    print(f"[{req_id}] Kaggle job {kaggle_job_id} failed at {elapsed:.0f}s: {err_msg[:200]}")
                    await sb_update_job(job_id, {"status": "failed", "error_message": err_msg})
                    raise HTTPException(502, f"Backend processing failed: {err_msg}")
        except httpx.TimeoutException:
            pass
        except HTTPException:
            raise
        except Exception as e:
            print(f"[{req_id}] Poll error for {kaggle_job_id}: {type(e).__name__}: {e}")
            pass
        await asyncio.sleep(3)

    print(f"[{req_id}] Job {kaggle_job_id} timed out after {max_wait}s")
    await sb_update_job(job_id, {"status": "failed", "error_message": "Processing timed out"})
    raise HTTPException(504, "Processing timed out after 5 minutes")


@app.get("/api/v2/garment/job/{kaggle_job_id}")
async def get_job_result(kaggle_job_id: str, request: Request):
    """Fetch reconstruction result ZIP from Kaggle backend."""
    user_id = await verify_jwt(request.headers.get("authorization"))
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                f"{KAGGLE_TUNNEL_URL}/api/v1/job/{kaggle_job_id}",
            )
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/zip"):
                # Upload ZIP to Supabase for persistence
                result_zip = resp.content
                result_url = ""
                if user_id:
                    result_url = await sb_upload_result_zip(kaggle_job_id, user_id, result_zip)
                if result_url:
                    await sb_update_job(kaggle_job_id, {"result_url": result_url})
                return StreamingResponse(
                    io.BytesIO(result_zip),
                    media_type="application/zip",
                    headers={"Content-Disposition": f"attachment; filename=garment_{kaggle_job_id}.zip"},
                )
            elif resp.status_code == 500:
                err = resp.json().get("error", "unknown")
                raise HTTPException(502, f"Backend failed: {err}")
            else:
                raise HTTPException(resp.status_code, f"Backend returned {resp.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch result: {str(e)[:200]}")


@app.get("/api/v2/garment/status/{kaggle_job_id}")
async def get_job_status(kaggle_job_id: str, request: Request):
    """Poll reconstruction status from Kaggle backend."""
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{KAGGLE_TUNNEL_URL}/api/v1/reconstruct/status",
                params={"job_id": kaggle_job_id},
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                raise HTTPException(404, "Job not found")
            else:
                raise HTTPException(resp.status_code, "Backend error")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Status check failed: {str(e)[:200]}")


@app.get("/api/v2/garment/result/{job_id}")
async def get_result(job_id: str, request: Request):
    user_id = await verify_jwt(request.headers.get("authorization"))
    job = await sb_get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["user_id"] != user_id:
        raise HTTPException(403, "Not authorized to view this job")
    if job["status"] == "completed":
        return {"status": "completed", "job_id": job_id}
    elif job["status"] == "failed":
        return JSONResponse(status_code=500, content={"status": "failed", "error": job.get("error_message")})
    return {"status": job["status"]}

@app.post("/api/v2/garment/mesh-only")
async def mesh_only(request: Request, file: UploadFile = File(...)):
    return await reconstruct_garment(request, file, include_mesh=True, include_pattern=False)

@app.post("/api/v2/garment/pattern-only")
async def pattern_only(request: Request, file: UploadFile = File(...)):
    return await reconstruct_garment(request, file, include_mesh=False, include_pattern=True)

# ═══════════════════════════════════════════════════════════════
#  VTO — Virtual Try-On (subscription-gated, rate-limited)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v2/garment/vto/synthesize")
async def vto_synthesize(
    request: Request,
    file: UploadFile = File(...),
    scan_id: str = "",
):
    """
    Phase 151: Multi-angle VTO with scan_id passthrough.
    Phase 155: Checks for cached refined photos before re-synthesis.
    Phase 152: Persists refined photos after synthesis.
    Phase 189: 180s per-angle timeout.
    """
    user_id = await verify_jwt(request.headers.get("authorization"))

    # ── Subscription gate ──
    sub = await check_subscription(user_id)
    if not sub["active"]:
        raise HTTPException(403, detail={
            "error": "subscription_required",
            "message": "Virtual Try-On requires an active subscription.",
            "plan": sub["plan"],
        })

    # ── Rate limit ──
    vto_count = await sb_get_vto_count_today(user_id)
    if vto_count >= VTO_DAILY_LIMIT:
        reset_time = await sb_get_vto_reset_time(user_id)
        raise HTTPException(429, detail={
            "error": "vto_rate_limit",
            "message": f"Daily VTO limit reached ({VTO_DAILY_LIMIT}/day).",
            "used": vto_count,
            "limit": VTO_DAILY_LIMIT,
            "resets_at": reset_time,
        })

    # ── Phase 155: Cache check — if scan_id provided, check for existing refined photos ──
    if scan_id:
        cached = await sb_get_refined_photos(scan_id)
        if cached.get("refined_front_url") and cached.get("refined_side_url"):
            logger.info(f"[VTO] Cache hit for scan {scan_id}: using existing refined photos")
            return {
                "cached": True,
                "front_url": cached.get("refined_front_url"),
                "side_url": cached.get("refined_side_url"),
                "back_url": cached.get("refined_back_url"),
                "scan_id": scan_id,
            }

    # ── Validate image ──
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 20MB)")

    # ── Forward to Kaggle synthesize-views endpoint ──
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")

    await sb_record_vto_usage(user_id)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15.0, read=180.0, write=30.0, pool=10.0)) as client:
            files = {"file": (file.filename, image_bytes, file.content_type)}
            params = {"user_id": user_id, "scan_id": scan_id}
            resp = await client.post(f"{KAGGLE_TUNNEL_URL}/api/v1/synthesize-views", files=files, params=params)

            if resp.status_code == 200:
                result = resp.json()

                # ── Phase 152: Persist refined photos if scan_id provided ──
                if scan_id and result.get("angles"):
                    angles = result["angles"]
                    await sb_save_refined_photos(
                        scan_id,
                        front_url=angles.get("front"),
                        side_url=angles.get("side"),
                        back_url=angles.get("back"),
                    )
                    result["scan_id"] = scan_id

                return result
            elif resp.status_code == 429:
                raise HTTPException(429, detail=resp.json())
            else:
                detail = ""
                try:
                    detail = resp.json().get("detail", resp.text[:300])
                except Exception:
                    detail = resp.text[:300]
                raise HTTPException(502, f"Backend error {resp.status_code}: {detail}")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "VTO synthesis timed out")
    except Exception as e:
        raise HTTPException(502, f"VTO synthesis failed: {str(e)[:200]}")


@app.post("/api/v2/garment/vto/tryon")
async def vto_tryon(
    request: Request,
    file: UploadFile = File(...),
    angle: str = "front",
    garment_type: str = "casual",
    garment_color: str = "#000000",
    scan_id: str = "",
):
    """
    Phase 151: Single-angle VTO with scan_id passthrough.
    Phase 175: Persists result to tryon_history.
    Phase 189: 180s timeout per angle.
    """
    user_id = await verify_jwt(request.headers.get("authorization"))

    # ── Subscription gate ──
    sub = await check_subscription(user_id)
    if not sub["active"]:
        raise HTTPException(403, detail={
            "error": "subscription_required",
            "message": "Virtual Try-On requires an active subscription.",
            "plan": sub["plan"],
        })

    # ── Rate limit ──
    vto_count = await sb_get_vto_count_today(user_id)
    if vto_count >= VTO_DAILY_LIMIT:
        reset_time = await sb_get_vto_reset_time(user_id)
        raise HTTPException(429, detail={
            "error": "vto_rate_limit",
            "message": f"Daily VTO limit reached ({VTO_DAILY_LIMIT}/day).",
            "used": vto_count,
            "limit": VTO_DAILY_LIMIT,
            "resets_at": reset_time,
        })

    # ── Phase 151: If scan_id provided, resolve photo from scan ──
    if scan_id and not file.filename:
        # No file uploaded — try to get photo from scan
        photos = await sb_get_scan_photos(scan_id)
        if photos.get("photo_front_url"):
            # Download front photo from Supabase storage
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    img_resp = await client.get(photos["photo_front_url"])
                    if img_resp.status_code == 200:
                        image_bytes = img_resp.content
                        file = UploadFile(filename="scan_photo.png", file=io.BytesIO(image_bytes))
                    else:
                        raise HTTPException(404, "Could not load scan photo")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Failed to load scan photo: {e}")
        else:
            raise HTTPException(404, "No photo found for this scan")
    else:
        image_bytes = await file.read()
        if len(image_bytes) > 20 * 1024 * 1024:
            raise HTTPException(413, "Image too large (max 20MB)")

    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")

    await sb_record_vto_usage(user_id)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15.0, read=180.0, write=30.0, pool=10.0)) as client:
            files = {"file": (file.filename, image_bytes, file.content_type)}
            params = {"user_id": user_id, "angle": angle, "garment_type": garment_type, "garment_color": garment_color}
            resp = await client.post(f"{KAGGLE_TUNNEL_URL}/api/v1/vto/tryon", files=files, params=params)

            if resp.status_code == 200:
                result = resp.json()

                # ── Phase 175: Persist to tryon_history if scan_id ──
                if scan_id:
                    from datetime import datetime, timezone
                    await sb_save_tryon_history(scan_id, {
                        "angle": angle,
                        "result_url": result.get("result_url"),
                        "garment_type": garment_type,
                        "garment_color": garment_color,
                        "seed": result.get("seed", 42),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })

                return result
            else:
                detail = ""
                try:
                    detail = resp.json().get("detail", resp.text[:300])
                except Exception:
                    detail = resp.text[:300]
                raise HTTPException(502, f"Backend error {resp.status_code}: {detail}")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "VTO try-on timed out")
    except Exception as e:
        raise HTTPException(502, f"VTO try-on failed: {str(e)[:200]}")


@app.get("/api/v2/garment/vto/progress/{kaggle_job_id}")
async def vto_progress_sse(kaggle_job_id: str):
    """SSE relay for VTO progress (multi-angle)."""
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")

    async def relay_events():
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("GET", f"{KAGGLE_TUNNEL_URL}/api/v1/vto/progress/{kaggle_job_id}") as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': 'SSE unavailable'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': 'SSE timed out'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': f'SSE relay error: {str(e)[:100]}'})}\n\n"

    return StreamingResponse(
        relay_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v2/garment/vto/status")
async def vto_status(user_id: str = None, request: Request = None):
    """Return VTO usage status for the current user."""
    if request:
        uid = await verify_jwt(request.headers.get("authorization"))
    elif user_id:
        uid = user_id
    else:
        raise HTTPException(401, "Missing user")

    count = await sb_get_vto_count_today(uid)
    reset = await sb_get_vto_reset_time(uid)
    sub = await check_subscription(uid)
    return {
        "used_today": count,
        "limit": VTO_DAILY_LIMIT,
        "remaining": max(0, VTO_DAILY_LIMIT - count),
        "resets_at": reset,
        "subscription": sub,
    }


@app.get("/api/v2/garment/vto/history/{scan_id}")
async def vto_history(scan_id: str, request: Request):
    """Phase 182: Get VTO history for a scan."""
    user_id = await verify_jwt(request.headers.get("authorization"))
    if not await sb_check_scan_ownership(user_id, scan_id):
        raise HTTPException(403, "Not authorized to view this scan's history")
    history = await sb_get_tryon_history(scan_id)
    return {"history": history, "scan_id": scan_id}


@app.post("/api/v2/garment/vto/feedback")
async def vto_feedback(request: Request):
    """Phase 211: Collect user feedback on VTO accuracy."""
    user_id = await verify_jwt(request.headers.get("authorization"))
    body = await request.json()
    scan_id = body.get("scan_id", "")
    angle = body.get("angle", "")
    rating = body.get("rating", "")
    garment_type = body.get("garment_type", "")

    if not scan_id or not rating:
        raise HTTPException(400, "scan_id and rating required")

    # Store in vto_usage table as a feedback row (repurpose for simplicity)
    # In production, create a separate vto_feedback table
    try:
        await sb_query(
            "vto_usage",
            method="POST",
            json_data={
                "user_id": user_id,
                "created_at": "now()",
                "scan_id": scan_id,
                "angle": angle,
                "rating": rating,
                "garment_type": garment_type,
            },
        )
    except Exception as e:
        logger.warning(f"Feedback storage failed: {e}")

    return {"status": "ok"}


# Phase 210: A/B test traffic routing
AB_CONFIG_PATH = "/home/ubuntu/garment-proxy/ab_config.json"

def _load_ab_config():
    """Load A/B test config for VTO traffic splitting."""
    try:
        with open(AB_CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"active_version": "baseline", "traffic_split": {"baseline": 100}}

def _assign_ab_version(user_id: str) -> str:
    """Deterministically assign A/B version based on user_id hash."""
    config = _load_ab_config()
    split = config.get("traffic_split", {})
    if not split or len(split) <= 1:
        return config.get("active_version", "baseline")
    # Deterministic hash-based assignment
    h = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
    bucket = h % 100
    cumulative = 0
    for version, pct in sorted(split.items()):
        cumulative += pct
        if bucket < cumulative:
            return version
    return config.get("active_version", "baseline")


@app.get("/api/v2/garment/ab/status")
async def ab_test_status():
    """Phase 210: Get current A/B test configuration."""
    return _load_ab_config()


@app.post("/api/v2/garment/ab/assign")
async def ab_test_assign(request: Request):
    """Phase 210: Get A/B version assignment for a user."""
    body = await request.json()
    user_id = body.get("user_id", "")
    version = _assign_ab_version(user_id)
    return {"version": version, "user_id": user_id}


# Phase 209: GPU cost tracking
@app.get("/api/v2/garment/cost/usage")
async def gpu_cost_usage(request: Request):
    """Proxy for GPU cost usage from Kaggle backend."""
    user_id = await verify_jwt(request.headers.get("authorization"))
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{KAGGLE_TUNNEL_URL}/api/v1/cost/usage",
                params={"user_id": user_id},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Cost usage fetch failed: {e}")
    return {"error": "unavailable"}



# Phase 192: AI Master Tailor — forward to Kaggle VLM
@app.post("/api/v2/garment/tailor/chat")
async def tailor_chat_proxy(
    file: UploadFile = File(None),
    message: str = "",
    history: str = "[]",
    measurements: str = "{}",
):
    """Forward tailor chat to Kaggle VLM endpoint."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            form_data = {"message": message, "history": history, "measurements": measurements}
            if file and file.filename:
                image_bytes = await file.read()
                form_data["file"] = (file.filename, image_bytes, file.content_type or "image/png")
            resp = await client.post(f"{KAGGLE_TUNNEL_URL}/api/v1/tailor/chat", data=form_data)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Kaggle returned {resp.status_code}"}
    except Exception as e:
        logger.warning(f"Tailor chat failed: {e}")
        return {"error": str(e), "source": "proxy_error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
