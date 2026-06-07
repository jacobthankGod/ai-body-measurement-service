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
# Use getcwd() for absolute reliability in container environments like Render
BASE_DIR = Path(os.getcwd()).resolve()
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
    description="Production-grade AI body measurement extraction",
    version="2.1.2",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# --- SECURITY: CORS ---
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. API ROUTES ---
@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "version": "2.1.2", "env": "production"}

def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
    except Exception as e:
        logger.error(f"FATAL: Route registration failed: {e}")
        traceback.print_exc()

include_lazy_routers()

# --- 2. STATIC ASSET MOUNTING ---
public_dir = BASE_DIR / "public"
mesh_dir = BASE_DIR / "data" / "mesh_cache"
mesh_dir.mkdir(parents=True, exist_ok=True)

if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

# Mount mesh cache for technical diagnostics
app.mount("/meshes", StaticFiles(directory=str(mesh_dir)), name="meshes")
else:
    logger.warning("WARN: /public directory missing. Asset serving may fail.")

# --- 3. HARDENED MPA ROUTING (Zero-Recursion) ---

def get_safe_file(filename: str):
    """Natively serve a file from root with existence validation."""
    target = BASE_DIR / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    logger.error(f"404: Missing Core Page -> {filename}")
    return JSONResponse(status_code=404, content={"error": f"KORRA Resource '{filename}' not found."})

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

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. Security Check
    if ".." in full_path or full_path.startswith("/"):
        return JSONResponse(status_code=400, content={"error": "Illegal path access"})

    # 2. Support direct .html hits
    if full_path.endswith(".html"):
        return get_safe_file(full_path)

    # 3. Check for public assets
    asset_file = public_dir / full_path
    if asset_file.exists() and asset_file.is_file():
        return FileResponse(str(asset_file))

    # 4. Final Fallback (SPA Style for dashboard hashes etc)
    return get_safe_file("index.html")

# --- 4. GLOBAL ERROR HANDLER ---
@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    logger.error(f"CRITICAL SYSTEM ERROR: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Infrastructure Error. Please contact KORRA technical support."}
    )

handler = app

if __name__ == "__main__":
    import uvicorn
    # Render standard: listen on 0.0.0.0 and use PORT env
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
