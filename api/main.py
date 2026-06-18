"""
KORRA AI - Main FastAPI Entry Point (Cloud Run Optimized)
========================================================
Mounts all routes, handles global middleware, and serves static frontend pages.
"""
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import auth, measurements, health, sharing, qrcode, payments, subscriptions, admin
from api.config import CORS_ORIGINS, FEATURES

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KORRA_API")

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
ASSETS_DIR = PUBLIC_DIR / "assets"

app = FastAPI(
    title="KORRA AI - Precision API",
    description="Biometric infrastructure for the borderless artisan economy.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ROUTES ---
app.include_router(health.router, tags=["System"], prefix="/api/v2")
app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
app.include_router(sharing.router, prefix="/api/v2", tags=["Sharing"])
app.include_router(qrcode.router, prefix="/api/v2", tags=["Utility"])
app.include_router(payments.router, prefix="/api/v2", tags=["Payments"])
app.include_router(subscriptions.router, prefix="/api/v2", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/api/v2", tags=["Admin"])

# --- STATIC PAGE SERVING ---
def get_safe_file(filename: str):
    target = BASE_DIR / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    # Fallback to index.html for SPA-like behavior or missing files
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/")
async def serve_root(): return get_safe_file("index.html")

@app.get("/signin")
async def serve_signin(): return get_safe_file("signin.html")

@app.get("/signup")
async def serve_signup(): return get_safe_file("signup.html")

@app.get("/onboarding")
async def serve_onboarding(): return get_safe_file("onboarding.html")

@app.get("/dashboard")
async def serve_dashboard(): return get_safe_file("dashboard.html")

@app.get("/verify")
async def serve_verify(): return get_safe_file("verify.html")

@app.get("/about")
async def serve_about(): return get_safe_file("about.html")

@app.get("/impact")
async def serve_impact(): return get_safe_file("impact.html")

@app.get("/casestudies")
async def serve_casestudies(): return get_safe_file("casestudies.html")

@app.get("/sizepassport")
async def serve_sizepassport(): return get_safe_file("sizepassport.html")

@app.get("/developers")
async def serve_developers(): return get_safe_file("api.html")

@app.get("/admin-panel") # Avoid conflict with admin router prefix
async def serve_admin_page(): return get_safe_file("admin.html")

# --- ASSET SERVING ---
# Prioritize explicit assets route
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Catch-all for other static files in root or nested
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API Endpoint Not Found")

    # Check if it's a specific file in the root
    target = BASE_DIR / full_path
    if target.exists() and target.is_file():
        return FileResponse(str(target))

    # Check in public folder
    public_target = PUBLIC_DIR / full_path
    if public_target.exists() and public_target.is_file():
        return FileResponse(str(public_target))

    # Default fallback for clean URLs
    if not "." in full_path:
        html_target = BASE_DIR / f"{full_path}.html"
        if html_target.exists():
            return FileResponse(str(html_target))

    return FileResponse(str(BASE_DIR / "index.html"))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal Server Error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    # Use environment variable for port (required for Cloud Run)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
