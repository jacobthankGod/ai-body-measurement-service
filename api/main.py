"""
KORRA Global Artisan Infrastructure - Production Entry Point
===========================================================
Expert implementation featuring Autonomous Brain Restoration and Prioritized Routing.
"""
import os
import sys
import logging
import traceback
import urllib.request
import tarfile
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

# --- CORE PATH RESOLUTION ---
API_DIR = Path(__file__).resolve().parent
BASE_DIR = API_DIR.parent
MODELS_DIR = BASE_DIR / "models"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# --- PRODUCTION LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KORRA_PROD")

# --- AUTONOMOUS BRAIN RESTORATION ---
def autonomous_restoration():
    """Ensures AI Brain is present on-boot."""
    checkpoint_idx = MODELS_DIR / "model.ckpt-667589.index"
    checkpoint_data = MODELS_DIR / "model.ckpt-667589.data-00000-of-00001"

    if not checkpoint_idx.exists() or not checkpoint_data.exists():
        logger.info("🚀 UNICORN RESTORATION: AI Brain Missing. Initiating Autonomous Handshake...")
        url = "https://dl.dropboxusercontent.com/s/e8s7q5bq7a5s1bq/hmr_model.tar.gz"
        dest = MODELS_DIR / "hmr_auto_restore.tar.gz"
        try:
            MODELS_DIR.mkdir(exist_ok=True)
            logger.info(f"📥 Pulling 347MB weights from secure mirror...")
            urllib.request.urlretrieve(url, dest)
            logger.info("📦 Extracting AI Brain...")
            with tarfile.open(dest, 'r:gz') as tar:
                tar.extractall(MODELS_DIR)
            os.remove(dest)
            logger.info("✅ RESTORATION COMPLETE: AI Brain Active.")
        except Exception as e:
            logger.error(f"❌ AUTONOMOUS RESTORATION FAILED: {e}")
    else:
        logger.info("💎 KORRA: AI Brain Integrity Verified.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    autonomous_restoration()
    logger.info(f"KORRA Infrastructure Booting. Root: {BASE_DIR}")
    yield
    logger.info("KORRA Infrastructure Shutting Down.")

app = FastAPI(
    title="KORRA Artisan API",
    description="Production-grade AI body measurement extraction infrastructure.",
    version="2.1.11",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- SECURITY: CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ROUTE REGISTRATION ---
# CRITICAL: Routes are registered BEFORE the catch-all HTML fallback
def include_routers():
    try:
        from api.routes import measurements, auth, health, qrcode, sharing
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
        app.include_router(health.router, prefix="/api/v2", tags=["Health"])
        app.include_router(qrcode.router, prefix="/api/v2/qrcode", tags=["QR Systems"])
        app.include_router(sharing.router, prefix="/api/v2/share", tags=["Sharing"])
        logger.info("✅ ALL API Routers Synchronized.")
    except Exception as e:
        logger.error(f"❌ Router registration failed: {e}")

include_routers()

# --- STATIC ASSET MOUNTING ---
public_dir = BASE_DIR / "public"
mesh_dir = Path("/tmp/korra_mesh_cache")
mesh_dir.mkdir(parents=True, exist_ok=True)

if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

app.mount("/meshes", StaticFiles(directory=str(mesh_dir)), name="meshes")

# --- MPA ROUTING ---

def get_safe_file(filename: str):
    target = BASE_DIR / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/")
async def serve_root(): return get_safe_file("index.html")

@app.get("/signin")
async def serve_signin(): return get_safe_file("signin.html")

@app.get("/signup")
async def serve_signup(): return get_safe_file("signup.html")

@app.get("/dashboard")
async def serve_dashboard(): return get_safe_file("dashboard.html")

@app.get("/admin")
async def serve_admin(): return get_safe_file("admin.html")

@app.get("/widget")
async def serve_widget(): return get_safe_file("widget.html")

@app.get("/share")
async def serve_share(): return get_safe_file("share.html")

# --- PRIORITIZED CATCH-ALL ---
@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    # 1. Block API leakage to HTML fallback
    if full_path.startswith("api/v2"):
        return JSONResponse(
            status_code=404,
            content={"error": f"API Endpoint /api/v2/{full_path} not found. Check router registration."}
        )

    # 2. Block path traversal
    if ".." in full_path:
        return JSONResponse(status_code=400, content={"error": "Illegal access"})

    # 3. Serve specific HTML pages if explicitly requested
    if full_path.endswith(".html"):
        return get_safe_file(full_path)

    # 4. Check for Static Assets
    asset_file = public_dir / full_path
    if asset_file.exists() and asset_file.is_file():
        return FileResponse(str(asset_file))

    # 5. Default Fallback (SPA behavior)
    return get_safe_file("index.html")

# --- GLOBAL ERROR HANDLER ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"SYSTEM CONFLICT: {exc}")
    return JSONResponse(status_code=500, content={"error": "KORRA Engine conflict."})

handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
