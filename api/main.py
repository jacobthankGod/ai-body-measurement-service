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
import mimetypes
from pathlib import Path

# --- CORE PATH RESOLUTION ---
import sys # REDUNDANT IMPORT FOR SCOPE PROTECTION

API_DIR = Path(__file__).resolve().parent
BASE_DIR = API_DIR.parent
MODELS_DIR = BASE_DIR / "models"
PUBLIC_DIR = BASE_DIR / "public"
MESH_DIR = PUBLIC_DIR / "meshes"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure public/meshes exists for technical persistence
MESH_DIR.mkdir(parents=True, exist_ok=True)

# --- PRODUCTION LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KORRA_PROD")

import threading
os.environ["MALLOC_ARENA_MAX"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# --- AUTONOMOUS BRAIN RESTORATION (NON-BLOCKING) ---
def autonomous_restoration():
    """Ensures AI Brain is present without blocking the server start."""
    def run():
        checkpoint_idx = MODELS_DIR / "model.ckpt-667589.index"
        checkpoint_data = MODELS_DIR / "model.ckpt-667589.data-00000-of-00001"

        if not checkpoint_idx.exists() or not checkpoint_data.exists():
            logger.info("🚀 UNICORN RESTORATION: AI Brain Missing. Initiating Autonomous Handshake...")
            url = "https://people.eecs.berkeley.edu/~kanazawa/cachedir/hmr/models.tar.gz"
            dest = BASE_DIR / "hmr_auto_restore.tar.gz"
            try:
                logger.info(f"📥 Pulling 385MB research weights from official mirror...")
                urllib.request.urlretrieve(url, dest)
                logger.info("📦 Extracting AI Brain to Root...")
                with tarfile.open(dest, 'r:gz') as tar:
                    tar.extractall(BASE_DIR)
                os.remove(dest)
                logger.info("✅ RESTORATION COMPLETE: AI Brain Active.")
            except Exception as e:
                logger.error(f"❌ AUTONOMOUS RESTORATION FAILED: {e}")
        else:
            logger.info("💎 KORRA: AI Brain Integrity Verified.")

    # Run in background thread so app can bind to port immediately
    threading.Thread(target=run, daemon=True).start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"KORRA Infrastructure Booting. Root: {BASE_DIR}")
    # NON-BLOCKING BOOT: Bind port first, download later
    autonomous_restoration()
    yield
    logger.info("KORRA Infrastructure Shutting Down.")

app = FastAPI(
    title="KORRA Artisan API",
    description="Production-grade AI body measurement extraction infrastructure.",
    version="2.1.15",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- SECURITY: CORS & HEADERS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *; default-src 'self' * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    response.headers["Permissions-Policy"] = "camera=*, microphone=(), geolocation=()"
    return response

# --- API ROUTE REGISTRATION ---
def register_routers(app: FastAPI):
    try:
        from api.routes import measurements, auth, health, qrcode, sharing, payments
        app.include_router(health.router, prefix="/api/v2", tags=["Health"])
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
        app.include_router(qrcode.router, prefix="/api/v2/qrcode", tags=["QR Systems"])
        app.include_router(sharing.router, prefix="/api/v2/share", tags=["Sharing"])
        app.include_router(payments.router, prefix="/api/v2", tags=["Payments"])
        logger.info("✅ ALL API Routers Handshaked Successfully.")

        # LOG ALL REGISTERED ROUTES FOR DEBUGGING
        for route in app.routes:
            logger.info(f"📍 Route: {route.path} [{route.methods}]")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Router handshake failed: {e}")
        traceback.print_exc()

register_routers(app)

# Note: Static assets are now served via explicit routes above for priority handling

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
@app.get("/developers")
async def serve_developers(): return get_safe_file("api.html")
@app.get("/admin")
async def serve_admin(): return get_safe_file("admin.html")
@app.get("/widget")
async def serve_widget(): return get_safe_file("widget.html")
@app.get("/share")
async def serve_share(): return get_safe_file("share.html")

# --- INDUSTRY PAGES ---
@app.get("/luxury-mtm")
async def serve_luxury(): return get_safe_file("luxury-mtm.html")
@app.get("/manufacturing")
async def serve_manufacturing(): return get_safe_file("manufacturing.html")
@app.get("/rtw")
async def serve_rtw(): return get_safe_file("rtw.html")
@app.get("/bridal")
async def serve_bridal(): return get_safe_file("bridal.html")
@app.get("/custom")
async def serve_custom(): return get_safe_file("custom.html")
@app.get("/uniforms")
async def serve_uniforms(): return get_safe_file("uniforms.html")

# --- EXPLICIT STATIC FILE MOUNT ---
# Mount public/assets as static files for reliable serving
# Ensure correct MIME types for all asset types
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/ttf", ".ttf")

# Mount static files from public/assets
if (PUBLIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(PUBLIC_DIR / "assets"), html=True), name="assets")
    logger.info(f"✅ Static files mounted from {PUBLIC_DIR / 'assets'}")

# Mount static files from public root (fallback)
if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")
    logger.info(f"✅ Static files mounted from {PUBLIC_DIR}")

# --- PRIORITIZED CATCH-ALL ---
@app.get("/api/v2/forensic/assets")
async def forensic_assets():
    """Hidden route to audit the physical file system in production."""
    try:
        manifest = []
        if PUBLIC_DIR.exists():
            for root, dirs, files in os.walk(str(PUBLIC_DIR)):
                for f in files:
                    full_path = Path(root) / f
                    manifest.append({
                        "file": f,
                        "rel_path": str(full_path.relative_to(PUBLIC_DIR)),
                        "size": full_path.stat().st_size
                    })
        return {"public_dir": str(PUBLIC_DIR), "files": manifest}
    except Exception as e:
        return {"error": str(e)}

@app.get("/meshes/{mesh_file:path}")
async def serve_meshes(mesh_file: str):
    mesh_path = MESH_DIR / mesh_file
    if mesh_path.exists(): return FileResponse(str(mesh_path))
    raise HTTPException(status_code=404, detail="Mesh not found")

@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    if full_path.startswith("api/v2") or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": f"API Endpoint /{full_path} not found."})
    if ".." in full_path: return JSONResponse(status_code=400, content={"error": "Illegal access"})
    if full_path.endswith(".html"): return get_safe_file(full_path)
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
