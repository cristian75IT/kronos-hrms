from fastapi import APIRouter

from .users import router as users_router
from .internal import router as internal_router
from .admin import router as admin_router

api_router = APIRouter()

api_router.include_router(users_router, prefix="/expensive-wallets", tags=["Wallet Users"])
api_router.include_router(internal_router, prefix="/expensive-wallets", tags=["Wallet Internal"])
api_router.include_router(admin_router, prefix="/expensive-wallets", tags=["Wallet Admin"])
