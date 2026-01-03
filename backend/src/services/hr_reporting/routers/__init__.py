"""KRONOS HR Reporting Service - Routers Package."""
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .admin import router as admin_router

__all__ = ["dashboard_router", "reports_router", "admin_router"]
