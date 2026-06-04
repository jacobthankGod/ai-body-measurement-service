"""
AI Body Scan SaaS - FastAPI Entry Point
===================================
Standalone API deployable to Vercel.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

from api.routes import measurements, health, subscriptions, payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"AI Body Scan SaaS v2.0.0 starting at {datetime.now().isoformat()}")
    yield
    print("Shutting down...")

app = FastAPI(
    title="AI Body Scan API",
    description="AI-powered body measurement extraction from photos",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v2", tags=["Health"])
app.include_router(measurements.router, prefix="/api/v2", tags=["Measurements"])
app.include_router(subscriptions.router, prefix="/api/v2", tags=["Subscriptions"])
app.include_router(payments.router, prefix="/api/v2", tags=["Payments"])

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": {"code": exc.status_code, "message": exc.detail}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
