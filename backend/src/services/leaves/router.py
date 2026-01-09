"""KRONOS Leave Service - API Router (Aggregated)."""
from fastapi import APIRouter
from src.services.leaves.routers import requests, balances, calendar, reports, internal


router = APIRouter()

router.include_router(calendar.router, tags=["Leave Calendar"])
router.include_router(requests.router, tags=["Leave Requests"])
router.include_router(balances.router, tags=["Leave Balances"])
router.include_router(reports.router, tags=["Leave Reports"])
router.include_router(internal.router, tags=["Leave Internal"])




