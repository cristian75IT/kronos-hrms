"""KRONOS Calendar Service - API Routers."""
from .holidays import router as holidays_router
from .closures import router as closures_router
from .events import router as events_router
from .calendar import router as calendar_router
from .export import router as export_router

from fastapi import APIRouter

api_router = APIRouter()

# Mount sub-routers
api_router.include_router(holidays_router, prefix="/holidays", tags=["Holidays"])
api_router.include_router(closures_router, prefix="/closures", tags=["Closures"])
api_router.include_router(events_router, prefix="/events", tags=["Events"])
api_router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
