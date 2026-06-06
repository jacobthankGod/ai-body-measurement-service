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
# In Render, BASE_DIR should resolve to the project root
BASE_DIR = Path(__file__).resolve().parent.parent

# --- PRODUCTION LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KORRA_PROD")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"KORRA Infrastructure Initializing at {BASE_DIR}...")
    yield
    logger.info("KORRA Infrastructure Shutting Down.")

app = FastAPI(
    title="KORRA Artisan API",
    description="Production-grade AI body measurement extraction",
    version="2.1.1",
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
    return {"status": "healthy", "version": "2.1.1"}

def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
    except Exception as e:
        logger.error(f"Route registration failed: {e}")

include_lazy_routers()

# --- 2. STATIC ASSET MOUNTING ---
public_dir = BASE_DIR / "public"
if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

# --- 3. HARDENED MPA ROUTING (Explicit Logic) ---

def safe_file_response(filename: str):
    """Safely return a file response if it exists, otherwise 404."""
    file_path = BASE_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    logger.warning(f"File not found: {filename}")
    return JSONResponse(status_code=404, content={"error": f"Page {filename} not found"})

@app.get("/")
async def serve_index():
    return safe_file_response("index.html")

@app.get("/signin")
async def serve_signin():
    return safe_file_response("signin.html")

@app.get("/signup")
async def serve_signup():
    return safe_file_response("signup.html")

@app.get("/dashboard")
async def serve_dashboard():
    return safe_file_response("dashboard.html")

@app.get("/admin")
async def serve_admin():
    return safe_file_response("admin.html")

@app.get("/about")
async def serve_about():
    return safe_file_response("about.html")

@app.get("/casestudies")
async def serve_casestudies():
    return safe_file_response("casestudies.html")

@app.get("/theoryofchange")
async def serve_theory():
    return safe_file_response("theoryofchange.html")

@app.get("/sizepassport")
async def serve_passport():
    return safe_file_response("sizepassport.html")

@app.get("/legal")
async def serve_legal():
    return safe_file_response("legal.html")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. Security check
    if ".." in full_path:
        return JSONResponse(status_code=400, content={"error": "Invalid path"})

    # 2. Check for direct .html requests (e.g. /signin.html)
    if full_path.endswith(".html"):
        return safe_file_response(full_path)

    # 3. Check for specific assets in public dir
    if "." in full_path:
        local_file = public_dir / full_path
        if local_file.exists() and local_file.is_file():
            return FileResponse(str(local_file))
        return JSONResponse(status_code=404, content={"error": "Resource not found"})

    # 4. Final Fallback: Return index.html for unknown clean routes
    return safe_file_response("index.html")

# --- 4. GLOBAL ERROR HANDLER ---
@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    logger.error(f"CRITICAL SYSTEM ERROR: {exc} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "The KORRA Engine encountered an internal conflict. Please refresh."}}
    )

handler = app

if __name__ == "__main__":
    import uvicorn
    # Use exact port and host for Render
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
