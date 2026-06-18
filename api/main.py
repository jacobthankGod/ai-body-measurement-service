"""
KORRA AI - Main FastAPI Entry Point
=================================
Mounts all routes and handles global middleware.
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import auth, measurements, health, sharing, qrcode, payments, subscriptions, admin
from api.config import CORS_ORIGINS, FEATURES

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KORRA_API")

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

# Mount Routes
app.include_router(health.router, tags=["System"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(measurements.router, prefix="/api", tags=["Measurements"])
app.include_router(sharing.router, prefix="/api", tags=["Sharing"])
app.include_router(qrcode.router, prefix="/api", tags=["Utility"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])
app.include_router(subscriptions.router, prefix="/api", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "KORRA AI Core",
        "version": "1.0.0",
        "features": {k: v for k, v in FEATURES.items()}
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal Server Error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
