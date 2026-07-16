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
import uvicorn

# ── Config (all from env, no local files) ──────────────────────
KAGGLE_TUNNEL_URL = os.getenv("KAGGLE_TUNNEL_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://blsettabymllulsxtziw.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsc2V0dGFieW1sbHVsc3h0eml3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAwNTY3NjksImV4cCI6MjA5NTYzMjc2OX0.PuMsTbgyRRcCQ04Y7Y9Y75WjRqmzgMP4S2_B4372V_U")
MAX_RETRIES = 5
TUNNEL_CACHE_FILE = "/tmp/kaggle_tunnel_url.txt"

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
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation" if method in ("POST", "PATCH") else "",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers, params=params or {})
        elif method == "POST":
            resp = await client.post(url, headers=headers, json=json_data)
        elif method == "PATCH":
            resp = await client.patch(url, headers=headers, params=params or {}, json=json_data)
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
    resp = await sb_query("garment_jobs", select="*", params={"id": f"eq.{job_id}", "select": "*"})
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

# ── FastAPI app ────────────────────────────────────────────────
app = FastAPI(title="Garment Reconstruction Proxy")

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

# ── Routes ─────────────────────────────────────────────────────
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

@app.get("/api/v2/garment/reconstruct/progress/{kaggle_job_id}")
async def reconstruct_progress_sse(kaggle_job_id: str):
    """SSE relay — streams progress events from Kaggle to frontend."""
    if not KAGGLE_TUNNEL_URL:
        raise HTTPException(503, "No Kaggle backend connected")

    async def relay_events():
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("GET", f"{KAGGLE_TUNNEL_URL}/api/v1/reconstruct/progress/{kaggle_job_id}") as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'message': 'SSE endpoint unavailable'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
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
                files = {"file": (file.filename, image_bytes, file.content_type)}
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
                    return await poll_and_return_job(req_id, job_id, kaggle_job_id)
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
                    await sb_update_job(job_id, {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
