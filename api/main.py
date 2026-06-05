"""
AI Body Scan SaaS - FastAPI Entry Point
===================================
Production Hardened "Nuclear" Version:
- Strict path separation (API vs Assets vs Frontend).
- SPA Fallback for /#dashboard and other routes.
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
    title="PrecisionFit 3D Measurement API",
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

@app.get("/api/v2/debug-auth")
async def debug_auth(user: str = Depends(validate_api_key)):
    return {"status": "authenticated", "user_key": f"{user[:4]}...{user[-4:]}"}

# Include dynamic routers
def include_lazy_routers():
    try:
        from api.routes import measurements, auth
        app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"], dependencies=[Depends(validate_api_key)])
        app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
    except Exception as e:
        print(f"Route registration warning: {e}")

include_lazy_routers()

# 2. STATIC ASSET MOUNTING (Isolated folder)
# We mount /assets to the /public directory where images live
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "public")), name="assets")

# 3. SPA / FRONTEND RECOVERY
@app.get("/")
async def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # This prevents the backend from eating images—it only serves index.html for non-asset routes
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
