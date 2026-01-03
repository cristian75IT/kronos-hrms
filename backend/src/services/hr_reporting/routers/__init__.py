"""KRONOS HR Reporting Service - Routers Package."""
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .admin import router as admin_router
from .training import router as training_router
from .hr_management import router as hr_management_router

__all__ = [
    "dashboard_router",
    "reports_router",
    "admin_router",
    "training_router",
    "hr_management_router",
]
