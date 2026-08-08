"""
Analytics Route | TELEMETRY SINK
==============================
Captures frontend usage patterns and expert-mode signals.
"""
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from api.services.database_service import DatabaseService

router = APIRouter()
logger = logging.getLogger("KORRA_ANALYTICS")

class AnalyticsEvent(BaseModel):
    category: str
    action: str
    label: Optional[str] = ""
    page: Optional[str] = ""
    timestamp: float

class AnalyticsBatch(BaseModel):
    events: List[AnalyticsEvent]

@router.post("/analytics")
async def collect_analytics(batch: AnalyticsBatch, background_tasks: BackgroundTasks):
    """Sinks usage metadata to usage_analytics table."""
    if not batch.events:
        return {"success": True, "count": 0}

    # Process in background to keep frontend flush fast
    background_tasks.add_task(
        DatabaseService.save_analytics_batch,
        [e.dict() for e in batch.events]
    )

    return {"success": True, "count": len(batch.events)}
