"""KRONOS Expense Service - API Router."""
from fastapi import APIRouter

from .routers import trips, reports, items, internal

# Re-export dependency
from .deps import get_expense_service

router = APIRouter()

router.include_router(trips.router, tags=["Business Trips"])
router.include_router(reports.router, tags=["Expense Reports"])
router.include_router(items.router, tags=["Expense Items"])
router.include_router(internal.router, tags=["Internal"])
