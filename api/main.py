"""
KORRA Global Artisan Infrastructure - Production Entry Point
===========================================================
Hardened Multi-Page Architecture (MPA) with API Security.
"""
import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

# Configure paths
BASE_DIR = Path(__file__).parent.parent
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
    logger.info("KORRA Infrastructure Initializing...")
    yield
    logger.info("KORRA Infrastructure Shutting Down.")

app = FastAPI(
    title="KORRA Artisan API",
    description="Production-grade AI body measurement extraction",
    version="2.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# --- SECURITY: CORS LOCKDOWN ---
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- 1. API ROUTES ---
@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "version": "2.1.0"}

def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        # Unified Security Handshake: No redundant global middleware
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
    except Exception as e:
        logger.error(f"Route registration failed: {e}")

include_lazy_routers()

# --- 2. STATIC ASSET MOUNTING ---
public_dir = BASE_DIR / "public"
if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

# --- 3. HARDENED MPA ROUTING ---
@app.get("/")
async def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/signin")
async def serve_signin():
    return FileResponse(str(BASE_DIR / "signin.html"))

@app.get("/signup")
async def serve_signup():
    return FileResponse(str(BASE_DIR / "signup.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(BASE_DIR / "dashboard.html"))

@app.get("/admin")
async def serve_admin():
    return FileResponse(str(BASE_DIR / "admin.html"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if ".." in full_path or full_path.startswith("/"):
        return JSONResponse(status_code=400, content={"error": "Invalid path request"})

    if full_path.endswith(".html"):
        local_file = BASE_DIR / full_path
        if local_file.exists() and local_file.is_file():
            return FileResponse(str(root_file))

    potential_pages = ["signin", "signup", "dashboard", "about", "casestudies", "theoryofchange", "sizepassport", "legal", "admin"]
    if full_path in potential_pages:
        return FileResponse(str(BASE_DIR / f"{full_path}.html"))

    if "." in full_path:
        local_file = public_dir / full_path
        if local_file.exists() and local_file.is_file():
            return FileResponse(str(local_file))
        return JSONResponse(status_code=404, content={"error": "Resource not found"})

    return FileResponse(str(BASE_DIR / "index.html"))

# --- 4. GLOBAL ERROR HANDLER ---
@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    logger.error(f"CRITICAL ERROR: {exc} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "Internal Infrastructure Error"}}
    )

handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
