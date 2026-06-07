"""
KORRA Global Artisan Infrastructure - Production Entry Point
===========================================================
Hardened Multi-Page Architecture (MPA) with API Security.
"""
import os
import sys
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

# --- CORE PATH RESOLUTION ---
API_DIR = Path(__file__).resolve().parent
BASE_DIR = API_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# --- PRODUCTION LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KORRA_PROD")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"KORRA Infrastructure Booting. Root: {BASE_DIR}")
    yield
    logger.info("KORRA Infrastructure Shutting Down.")

app = FastAPI(
    title="KORRA Artisan API",
    description="Production-grade AI body measurement extraction infrastructure.",
    version="2.1.4",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- SECURITY: CORS (Nuclear Open for Availability) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. API ROUTES ---
@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "version": "2.1.4", "env": "production"}

def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
        logger.info("✅ API Routers Registered Successfully.")
    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        traceback.print_exc()

include_lazy_routers()

# --- 2. STATIC ASSET MOUNTING ---
public_dir = BASE_DIR / "public"
# Use /tmp for mesh cache to avoid permission errors on Render
mesh_dir = Path("/tmp/korra_mesh_cache")
mesh_dir.mkdir(parents=True, exist_ok=True)

if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

# Serve meshes from /tmp
app.mount("/meshes", StaticFiles(directory=str(mesh_dir)), name="meshes")

# --- 3. HARDENED MPA ROUTING ---

def get_safe_file(filename: str):
    """Natively serve a file from root with existence validation."""
    target = BASE_DIR / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))

    # Check public folder
    public_target = public_dir / filename
    if public_target.exists() and public_target.is_file():
        return FileResponse(str(public_target))

    logger.warning(f"File not found: {filename} at {target}")
    # Return index.html as a last resort for clean routing
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    return JSONResponse(status_code=404, content={"error": "Resource not found"})

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

@app.get("/developers")
async def serve_api_portal(): return get_safe_file("api.html")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if ".." in full_path or full_path.startswith("/"):
        return JSONResponse(status_code=400, content={"error": "Illegal access"})

    if full_path.endswith(".html"):
        return get_safe_file(full_path)

    asset_file = public_dir / full_path
    if asset_file.exists() and asset_file.is_file():
        return FileResponse(str(asset_file))

    # Clean URLs fallback to index
    return get_safe_file("index.html")

# --- 4. GLOBAL ERROR HANDLER ---
@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    logger.error(f"CRITICAL SYSTEM ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "System error. Please refresh."}
    )

handler = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
