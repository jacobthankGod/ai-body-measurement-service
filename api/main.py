"""
AI Body Scan SaaS - FastAPI Entry Point
===================================
Production Hardened "Nuclear" Version:
- Strict path separation (API vs Assets vs Frontend).
- Multi-Page Architecture (MPA) Routing.
- Supabase Auth Integration.
"""
import os
import sys
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

from middleware.api_key_auth import validate_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI Body Scan SaaS Starting...")
    yield

app = FastAPI(
    title="KORRA Artisan API",
    description="AI-powered body measurement extraction",
    version="2.0.2",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API ROUTES (High Priority)
@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.2"}

# Include dynamic routers
def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"], dependencies=[Depends(validate_api_key)])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
    except Exception as e:
        print(f"Route registration warning: {e}")

include_lazy_routers()

# 2. STATIC ASSET MOUNTING
public_dir = BASE_DIR / "public"
if public_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(public_dir)), name="assets")

# 3. MPA / FRONTEND RECOVERY (Multi-Page Logic)
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

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. Map .html files in root natively (MPA Support)
    if full_path.endswith(".html"):
        local_file = BASE_DIR / full_path
        if local_file.exists():
            return FileResponse(str(local_file))

    # 2. Map Clean URLs to their .html counterparts
    potential_pages = ["signin", "signup", "dashboard"]
    if full_path in potential_pages:
        return FileResponse(str(BASE_DIR / f"{full_path}.html"))

    # 3. Check for specific assets in public dir
    if "." in full_path:
        local_file = public_dir / full_path
        if local_file.exists():
            return FileResponse(str(local_file))
        return JSONResponse(status_code=404, content={"error": "Asset not found"})

    # 4. Fallback to index for marketing routing
    return FileResponse(str(BASE_DIR / "index.html"))

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": str(exc)}}
    )

handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
