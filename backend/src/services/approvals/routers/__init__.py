"""
KRONOS Approval Service - Routers Package.
"""
from .config import router as config_router
from .requests import router as requests_router
from .decisions import router as decisions_router
from .internal import router as internal_router

__all__ = [
    "config_router",
    "requests_router",
    "decisions_router",
    "internal_router",
]
