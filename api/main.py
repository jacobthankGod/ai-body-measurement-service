"""
KORRA AI - Main FastAPI Entry Point (Cloud Run Optimized)
========================================================
Mounts all routes, handles global middleware, and serves static frontend pages.
"""
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import auth, measurements, health, sharing, qrcode, payments, subscriptions, admin, invoices, webhooks, notifications, scan_requests
from api.config import CORS_ORIGINS, FEATURES

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KORRA_API")

# PHASE 130: SENTRY ERROR REPORTING INTEGRATION
try:
    import sentry_sdk
    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"), traces_sample_rate=1.0)
        logger.info("🛡️ Phase 130: Sentry reporting LIVE.")
except ImportError:
    logger.warning("⚠️ sentry-sdk not found. Error reporting will use local logs.")

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

# --- SECURITY HEADERS & HTTPS MIDDLEWARE ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # FORCE HTTPS: Redirect in production if not using SSL
    # Note: X-Forwarded-Proto is typically set by Nginx reverse proxy
    if request.headers.get("x-forwarded-proto") == "http" and os.environ.get("ENVIRONMENT") == "production":
        url = request.url.replace(scheme="https")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url)

    response = await call_next(request)
    # Relax security policies to allow external integrations (Paystack, Widget iframes)
    # Note: 'unsafe-none' and 'cross-origin' allow external assets to bypass NotSameOrigin blocks
    response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
    response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# --- API ROUTES ---
app.include_router(health.router, tags=["System"], prefix="/api/v2")
app.include_router(auth.router, prefix="/api/v2", tags=["Auth"])
app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
app.include_router(sharing.router, prefix="/api/v2", tags=["Sharing"])
app.include_router(qrcode.router, prefix="/api/v2", tags=["Utility"])
app.include_router(payments.router, prefix="/api/v2", tags=["Payments"])
app.include_router(subscriptions.router, prefix="/api/v2", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/api/v2", tags=["Admin"])
app.include_router(invoices.router, prefix="/api/v2", tags=["Invoices"])
app.include_router(webhooks.router, prefix="/api/v2", tags=["Webhooks"])
app.include_router(notifications.router, prefix="/api/v2", tags=["Notifications"])
app.include_router(scan_requests.router, prefix="/api/v2", tags=["ScanRequests"])

# --- STATIC PAGE SERVING ---
# PHASE 502 FIX: Enhanced static file serving with explicit route logging
def get_safe_file(filename: str):
    """Serve static HTML files with robust error handling for 502 prevention."""
    try:
        target = BASE_DIR / filename
        if target.exists() and target.is_file():
            logger.info(f"📄 Serving static file: {filename}")
            return FileResponse(str(target))
    except Exception as e:
        logger.error(f"Error serving {filename}: {e}")
    
    # Fallback to index.html for SPA-like behavior or missing files
    logger.warning(f"📄 Fallback to index.html for: {filename}")
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/")
async def serve_root(): 
    logger.info("🌐 Root route accessed")
    return get_safe_file("index.html")

# PHASE 502 FIX: Health check endpoint for load balancer verification
@app.get("/health")
async def health_check():
    """Health check endpoint - critical for 502 prevention."""
    return {"status": "ok", "service": "korra-ai", "version": "1.0.0"}

@app.get("/signin")
async def serve_signin(): return get_safe_file("signin.html")

@app.get("/signup")
async def serve_signup(): return get_safe_file("signup.html")

@app.get("/onboarding")
async def serve_onboarding(): return get_safe_file("onboarding.html")

@app.get("/dashboard")
async def serve_dashboard(): 
    logger.info("🏠 Dashboard route accessed")
    return get_safe_file("dashboard.html")

@app.get("/verify")
async def serve_verify(): return get_safe_file("verify.html")

# PHASE 502 FIX: Explicit favicon route to prevent 404 errors
@app.get("/favicon.ico")
async def serve_favicon():
    """Serve favicon to prevent 502 errors."""
    return FileResponse(str(BASE_DIR / "favicon.ico")) if (BASE_DIR / "favicon.ico").exists() else Response(status_code=204)

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

@app.get("/widget")
async def serve_widget(merchant: str = None):
    return get_safe_file("widget.html")

@app.get("/admin-panel") # Avoid conflict with admin router prefix
async def serve_admin_page(): return get_safe_file("admin.html")

# --- ASSET SERVING ---
# Prioritize explicit assets route
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Catch-all for other static files in root or nested
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # PHASE 502 FIX: Graceful error handling for unmatched routes
    logger.info(f"🔄 Catch-all route accessed: {full_path}")
    
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
