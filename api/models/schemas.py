"""
Pydantic Schemas
================
Request/Response models for API.
"""
from pydantic import BaseModel, Field
from typing import Optional

class MeasurementExtractRequest(BaseModel):
    height: float = Field(..., ge=100, le=230, description="User height in cm")
    gender: str = Field(default="male", pattern="^(male|female)$")

class MeasurementResponse(BaseModel):
    success: bool
    request_id: Optional[str] = None
    measurements: dict
    accuracy: dict
    metadata: Optional[dict] = None

class SubscriptionStatus(BaseModel):
    tier: str
    scans_used: int
    scans_remaining: int
    reset_date: str
    features: list
    usage: dict

class ErrorResponse(BaseModel):
    error: dict
