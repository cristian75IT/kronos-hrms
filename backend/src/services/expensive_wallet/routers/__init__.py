from fastapi import APIRouter
from .wallet import router as wallet_router

api_router = APIRouter()
api_router.include_router(wallet_router, prefix="/expensive-wallets", tags=["wallet"])
