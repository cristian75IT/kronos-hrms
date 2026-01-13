"""KRONOS Auth Service - Main API Router (Aggregator)."""
from fastapi import APIRouter

from src.services.auth.routers.security import router as security_router
from src.services.auth.routers.users import router as users_router
from src.services.auth.routers.rbac import router as rbac_router
from src.services.auth.routers.org import router as org_router
from src.services.auth.routers.contracts import router as contracts_router
from src.services.auth.routers.trainings import router as trainings_router

router = APIRouter()

# Include sub-routers
router.include_router(security_router, tags=["Security"])
router.include_router(users_router, tags=["Users"])
router.include_router(rbac_router, tags=["RBAC"])
router.include_router(org_router, tags=["Organization (Legacy)"])
router.include_router(contracts_router, tags=["Contracts"])
router.include_router(trainings_router, tags=["Trainings"])
